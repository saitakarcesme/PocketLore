#!/usr/bin/env python3
"""Single-writer, durable PocketLore task supervisor. No external Python dependencies."""
from protocol import invocation, valid_review, plan_repair
import argparse, fcntl, hashlib, json, os, pathlib, re, select, subprocess, tempfile, time


def atomic(path, value):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as out:
        json.dump(value, out, indent=2); out.write('\n'); out.flush(); os.fsync(out.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def freeze(path, data):
    """Create immutable evidence once; retries may only reuse identical bytes."""
    path = pathlib.Path(path)
    if path.exists():
        if path.read_bytes() != data: raise RuntimeError(f'Immutable evidence mismatch: {path}')
        return
    # A crash after chmod must not poison the next attempt's temporary path.
    # Keep abandoned files as evidence; each retry gets a fresh inode.
    descriptor, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    temp = pathlib.Path(name)
    with os.fdopen(descriptor, 'wb') as out:
        out.write(data); out.flush(); os.fsync(out.fileno())
    temp.chmod(0o444); os.replace(temp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def read(path, default):
    try: return json.loads(pathlib.Path(path).read_text())
    except FileNotFoundError: return default


def codex_events(path):
    """Read recognized object events without altering the retained output stream."""
    for line in pathlib.Path(path).read_text(errors='replace').splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if not isinstance(item, dict):
            continue
        event_type = item.get('type')
        if event_type == 'thread.started':
            if isinstance(item.get('thread_id'), str) and item['thread_id']:
                yield item
        elif event_type == 'turn.completed':
            yield item


class Runner:
    def __init__(self, control, repo):
        self.control, self.repo = pathlib.Path(control), pathlib.Path(repo)
        self.state_path = self.control / 'state/runner.json'
        self.state = read(self.state_path, {'version': 1, 'tasks': {}, 'events': [], 'last_known_good_commit': None})
        self.stop = False

    def save(self): atomic(self.state_path, self.state)
    def git(self, *args): return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()
    def event(self, key, **data):
        if any(e['id'] == key for e in self.state['events']): return False
        self.state['events'].append({'id': key, 'time': time.time(), **data}); self.save(); return True

    def ingest(self):
        for path in sorted((self.control / 'tasks').glob('*.json')):
            spec = read(path, {})
            if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', spec.get('id', '')): raise ValueError(f'{path}: unsafe task ID')
            if not isinstance(spec.get('acceptance_checks'), list) or any(not isinstance(c, list) or not c or not all(isinstance(a, str) for a in c) for c in spec['acceptance_checks']): raise ValueError(f'{path}: checks must be argument arrays')
            if spec['id'] in self.state['tasks'] and self.state['tasks'][spec['id']]['status'] == 'pending':
                self.state['tasks'][spec['id']].update(spec)
            if spec['id'] not in self.state['tasks']:
                for field in ('objective', 'scope', 'acceptance_checks', 'artifacts', 'dependencies'):
                    if field not in spec: raise ValueError(f'{path}: missing {field}')
                self.state['tasks'][spec['id']] = {**spec, 'status': 'pending', 'phase': 'builder', 'checks': [], 'critic_result': None, 'base_commit': None, 'head_commit': None, 'attempt': 0}
        self.save()

    def run_process(self, task, phase, argv, cwd, prompt=None):
        """A launch receipt lets a restart reuse finished output or resume interrupted sessions."""
        folder = self.control / 'evidence' / task['id']; folder.mkdir(parents=True, exist_ok=True)
        receipt = folder / f'{phase}-{task["attempt"]}.receipt.json'
        previous = read(receipt, {})
        if 'returncode' in previous: return previous
        log = folder / f'{phase}-{task["attempt"]}.jsonl'
        # If a previous process died, retain its real session ID before resuming it.
        if phase in ('builder', 'critic') and log.exists():
            completed = False
            for item in codex_events(log):
                if item['type'] == 'thread.started': task[f'{phase}_session_id'] = item['thread_id']
                if item['type'] == 'turn.completed': completed = True
            if completed and phase in ('builder', 'critic'):
                result = {'returncode': 0, 'log': str(log), 'recovered_completed_turn': True}
                atomic(receipt, result); self.save(); return result
        if phase in ('builder', 'critic'):
            config = read(self.control / 'runner/config.json', {})
            sessions = read(self.control / 'roles/sessions.json', {})
            session = sessions.get(phase)
            if task.get(f'{phase}_session_id') not in (None, session):
                raise RuntimeError('Task session differs from canonical registry; explicit migration required')
            task[f'{phase}_session_id'] = session
            policy = task.setdefault('invocation_policies', {}).setdefault(phase, config['role_policies'][phase])
            schema = pathlib.Path(__file__).with_name('critic.schema.json') if phase == 'critic' else None
            output_path = folder / ('critic-result.json' if phase == 'critic' else 'builder-result.txt')
            argv = invocation(config['codex'], session, policy, output_path, schema, cwd=cwd)
            task.setdefault('invocations', {})[phase] = argv
            self.save()
        with log.open('a') as output:
            child = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if prompt else subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, text=True)
            task['process'] = {'pid': child.pid, 'phase': phase, 'log': str(log), 'started': time.time()}; self.save()
            atomic(receipt, {'pid': child.pid, 'started': time.time()})
            if prompt:
                child.stdin.write(prompt); child.stdin.close()
            code = child.wait()
        result = {'returncode': code, 'log': str(log), 'finished': time.time()}
        atomic(receipt, result)
        if phase in ('builder', 'critic'):
            for item in codex_events(log):
                if item['type'] == 'thread.started': task[f'{phase}_session_id'] = item['thread_id']
        task.pop('process', None); self.save(); return result

    def execute(self, task):
        folder = self.control / 'evidence' / task['id']; folder.mkdir(parents=True, exist_ok=True)
        config = read(self.control / 'runner/config.json', {})
        codex = config.get('codex', 'codex')
        if task['status'] == 'pending':
            if self.git('status', '--porcelain'): raise RuntimeError('Working tree must be clean before task dispatch')
            task['base_commit'] = self.git('rev-parse', 'HEAD')
            task['branch'] = 'checkpoint/' + task['id']
            self.git('checkout', '-B', task['branch'])
            task['status'] = 'running'; self.save()
        if task['phase'] == 'builder':
            sessions = read(self.control / 'roles/sessions.json', {})
            session = task.get('builder_session_id') or task.get('session_id') or sessions.get('builder')
            if isinstance(session, dict): session = session.get('session_id')
            if not session: raise RuntimeError('Explicit builder session ID is required')
            task['builder_session_id'] = session; self.save()
            prompt = ('Continue PocketLore work on LLMRig. Inspect existing work first; this task may be recovering. '
                      'Do not push, change branches, touch private context, or change orchestration. Make meaningful technical checkpoint commits on the current checkpoint branch roughly every 5-15 minutes when changes warrant; label unvalidated or failing checkpoints honestly. Never advance main yourself. '
                      'All product content must be English. Complete only the concrete task below; report evidence and limitations.\n' + json.dumps({k: task[k] for k in ('id','objective','scope','acceptance_checks','artifacts')}) + '\n' + task.get('prompt', ''))
            result = self.run_process(task, 'builder', [codex], self.repo, prompt)
            task['builder_exit'] = result['returncode']; task['phase'] = 'validation'; self.save()
        if task['phase'] == 'validation':
            review = folder / 'review'; review.mkdir(exist_ok=True)
            checks = []
            for i, command in enumerate(task['acceptance_checks']):
                result = self.run_process(task, f'check-{i}', command, self.repo)
                frozen_log = review / f'check-{i}.log'
                data = pathlib.Path(result['log']).read_bytes()
                freeze(frozen_log, data)
                checks.append({'command': command, **result, 'log': str(frozen_log), 'sha256': hashlib.sha256(data).hexdigest()})
            task['checks'] = checks
            for path in task['artifacts']:
                artifact = pathlib.Path(path)
                if not artifact.is_absolute(): artifact = self.repo / artifact
                if not artifact.exists(): checks.append({'artifact': path, 'returncode': 1, 'error': 'Missing required artifact'})
            # Preserve useful failed experiments on their checkpoint branch as well.
            self.git('add', '-A')
            if self.git('diff', '--cached', '--stat'):
                self.git('commit', '-m', f'Checkpoint {task["id"]}: implementation and evidence')
            task['head_commit'] = self.git('rev-parse', 'HEAD')
            evidence = {'task_id': task['id'], 'objective': task['objective'], 'base_commit': task['base_commit'], 'head_commit': task['head_commit'], 'checks': checks, 'builder_exit': task.get('builder_exit'), 'artifacts': []}
            for i, source in enumerate(task['artifacts']):
                path = pathlib.Path(source); path = path if path.is_absolute() else self.repo / path
                if path.is_file():
                    data = path.read_bytes(); frozen = review / f'artifact-{i}-{path.name}'; freeze(frozen, data)
                    evidence['artifacts'].append({'path': str(frozen), 'sha256': hashlib.sha256(data).hexdigest()})
            diff = review / 'change.patch'; freeze(diff, self.git('diff', task['base_commit'], task['head_commit']).encode())
            evidence['diff'] = str(diff)
            evidence['diff_sha256'] = hashlib.sha256(diff.read_bytes()).hexdigest()
            freeze(review / 'evidence.json', (json.dumps(evidence, indent=2) + '\n').encode())
            task['phase'] = 'critic'; self.save()
        if task['phase'] == 'critic':
            review = folder / 'review'
            schema = pathlib.Path(__file__).with_name('critic.schema.json')
            goals = (self.repo / 'docs/GOALS.md').read_text()
            prompt = ('You are an independent acceptance critic. You have no builder planning conversation. Inspect only the immutable evidence in this directory and the bounty goals below. '
                      'Never read builder logs, private conversations, planning context or sibling directories. Read evidence.json, change.patch, and relevant artifact files. Builder completion is not acceptance. Desktop tests do not prove physical Android acceptance. '
                      'Return only JSON decision continue/rework/unsupported and visible_result exactly one English sentence of at most 35 words. '
                      'Review directory: ' + str(review) + '. '
                      'continue means this bounded task passed; it does not mean product acceptance or superiority.\nBounty goals:\n' + goals)
            result = self.run_process(task, 'critic', [codex], review, prompt)
            try: verdict = read(folder/'critic-result.json', {})
            except ValueError: verdict = {}
            if result['returncode'] or not valid_review(verdict):
                verdict = {'decision': 'unsupported', 'reason': 'Critic failed or returned invalid English single-sentence result',
                           'visible_result': 'The critic output failed validation and requires a bounded repair before acceptance.'}
            if any(c['returncode'] for c in task['checks']) or task.get('builder_exit'):
                verdict['decision'] = 'rework'; verdict['reason'] = 'Required automated checks or builder process failed. ' + verdict.get('reason','')
            task['critic_result'] = verdict; task['phase'] = 'checkpoint'; self.save()
        if task['phase'] == 'checkpoint':
            accepted = task['critic_result']['decision'] == 'continue'
            if accepted:
                self.git('checkout', 'main'); self.git('merge', '--ff-only', task['head_commit'])
                tag = 'accepted/' + task['id']
                if not self.git('tag', '--list', tag): self.git('tag', tag, task['head_commit'])
                self.git('push', 'origin', 'main', 'refs/tags/' + tag)
                self.state['last_known_good_commit'] = task['head_commit']; task['status'] = 'accepted'
            else:
                self.git('push', 'origin', task['branch'])
                self.git('checkout', 'main'); task['status'] = 'rework'
                repair = plan_repair(task)
                if repair is None:
                    task['status'] = 'blocked'
                    task['blocked_reason'] = 'Three initial failures and one alternative strategy failed; a revised task is required.'
                    task['block_kind'] = 'strategy_exhausted'
                else:
                    atomic(self.control/'tasks'/f'{repair["id"]}.json', repair)
            self.event(task['id'] + ':completion', status=task['status'], head=task['head_commit'])
            task['phase'] = 'done'; self.save()
            self.sync_completions()

    def ready_tasks(self):
        def satisfied(dependency):
            return self.state['tasks'].get(dependency, {}).get('status') == 'accepted' or any(
                t.get('repair_of') == dependency and t['status'] == 'accepted' for t in self.state['tasks'].values())
        return sorted((t for t in self.state['tasks'].values() if t['status'] == 'running' or
                       (t['status'] == 'pending' and all(satisfied(d) for d in t['dependencies']))),
                      key=lambda t: (t['status'] != 'running', t['id']))

    def sync_completions(self):
        from continuity import publish
        # Replay from durable completion events if a crash interrupted publication.
        next_task = next((t['id'] for t in self.ready_tasks()), 'Review release gaps and external dependencies')
        for event in self.state['events']:
            if event['id'].endswith(':completion'):
                task = self.state['tasks'].get(event['id'].rsplit(':', 1)[0])
                if task:
                    try:
                        publish(self.control, event, task, self.state, next_task)
                    except OSError as error:
                        self.state['continuity_sync_error'] = str(error)
                        self.save()

    def run(self, once=False):
        self.control.joinpath('state').mkdir(parents=True, exist_ok=True)
        with (self.control/'state/runner.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.state = read(self.state_path, self.state)
            self.state['supervisor_pid'] = os.getpid(); self.state['started_at'] = time.time(); self.save()
            self.event('startup:' + str(time.time_ns()), kind='startup')
            while not self.stop:
                self.ingest()
                self.sync_completions()
                ready = self.ready_tasks()
                dispatch_enabled = read(self.control/'runner/config.json', {}).get('dispatch_enabled', False)
                if ready and dispatch_enabled:
                    self.execute(ready[0])
                if once: break
                if not ready or not dispatch_enabled:
                    self.state['queue_summary'] = {'ready': [t['id'] for t in ready], 'blocked': [t['id'] for t in self.state['tasks'].values() if t['status']=='blocked'], 'dispatch_enabled': dispatch_enabled, 'updated_at': time.time()}
                    self.save()
                    # Filesystem events wake the daemon immediately; timeout only checks service health.
                    select.select([self.notify_fd], [], [], 30)
                    try: os.read(self.notify_fd, 65536)
                    except BlockingIOError: pass

    def watch(self):
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        self.notify_fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.notify_fd < 0: raise OSError(ctypes.get_errno(), 'inotify_init1')
        self.control.joinpath('tasks').mkdir(exist_ok=True)
        libc.inotify_add_watch(self.notify_fd, os.fsencode(self.control/'tasks'), 0x00000008 | 0x00000080 | 0x00000100)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--control', required=True); parser.add_argument('--repo', required=True); parser.add_argument('--once', action='store_true')
    args = parser.parse_args(); runner = Runner(args.control,args.repo); runner.watch(); runner.run(args.once)

if __name__ == '__main__': main()
