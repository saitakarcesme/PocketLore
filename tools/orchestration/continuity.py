"""Durable completion ledger and asynchronous canonical continuity delivery."""
import argparse
import fcntl
import json
import os
import pathlib
import subprocess
import time


def records(path):
    if not path.exists():
        return []
    result = []
    for line in path.read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                result.append(value)
        except ValueError:
            # Preserve a crash-truncated tail; the next append begins a new line.
            pass
    return result


def publish(control, event, task, state, next_task):
    from runner import atomic
    control = pathlib.Path(control)
    marker = control / 'state/continuity-published' / (event['id'].replace(':', '-') + '.json')
    if marker.exists():
        return
    registry = json.loads((control / 'roles/sessions.json').read_text())
    payload = {'event_id': event['id'], 'task_id': task['id'], 'commit': task.get('head_commit'),
               'result': task['status'], 'review': task.get('critic_result', {}).get('visible_result',
                            task.get('critic_result', {}).get('sentence', 'No review text recorded.')),
               'next_step': next_task, 'time': event['time'], 'continuity_session_id': registry['continuity']}
    ledger = control / 'state/continuity-ledger.jsonl'
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if not any(item.get('event_id') == event['id'] for item in records(ledger)):
        with ledger.open('a') as out:
            out.write('\n' + json.dumps(payload, ensure_ascii=True) + '\n'); out.flush(); os.fsync(out.fileno())
    outbox = control / 'notifications/pending' / (event['id'].replace(':', '-') + '.json')
    if not outbox.exists():
        atomic(outbox, {'payload': payload, 'status': 'pending', 'attempts': 0, 'retry_after': 0})
    # Keep the human handoff derived from exact durable state, not worker prose.
    current = control / 'context/CURRENT_STATE.md'
    current.parent.mkdir(parents=True, exist_ok=True)
    text = ('# PocketLore current state\n\nAll persisted project content and critic output must be English; original private user conversation transcripts remain verbatim. '
            'All implementation, builds, data and inference run on LLMRig; the Mac source chat coordinates. '
            'Normal project development and pushes are authorized. The runner owns implementation.\n\n'
            f"Last completed task: {task['id']}\n\nCommit: {task.get('head_commit')}\n\nResult: {task['status']}\n\n"
            f"Critic: {payload['review']}\n\nNext step: {next_task}\n\n"
            f"Last known good commit: {state.get('last_known_good_commit')}\n\n"
            'Canonical role registry: /home/isa/PocketLore-control/roles/sessions.json\n\n' +
            '\n'.join(f'- {role}: {value}' for role, value in registry.items() if isinstance(value, str)) +
            '\n\nFull English working inputs: context/RESEARCH.md, context/PLAN.md and translations/CONTINUITY_CRITIC_CONTRACT.md. '
            'The original visible-history.jsonl is private conversation history, not product data.\n\n'
            'No physical Android device is attached. Physical Android/GrapheneOS acceptance, phone resource/latency proof, supported synthesis, '
            'broad knowledge/travel coverage and comparable evaluation remain subject to their release gates. No superiority is established.\n\n'
            'Live task state: state/runner.json; append-only events: state/continuity-ledger.jsonl. Notification failures are retained in notifications/pending and retried independently.\n')
    temp = current.with_suffix('.tmp'); temp.write_text(text)
    with temp.open('r') as handle:
        os.fsync(handle.fileno())
    os.replace(temp, current)
    atomic(marker, {'event_id': event['id'], 'published_at': time.time(), 'outbox': str(outbox)})


def deliver(control, path, run=subprocess.run):
    from runner import atomic, read
    from protocol import invocation
    control, path = pathlib.Path(control), pathlib.Path(path)
    job = read(path, {})
    if job.get('status') == 'delivered' or job.get('retry_after', 0) > time.time():
        return job
    config = read(control / 'runner/config.json', {})
    registry = read(control / 'roles/sessions.json', {})
    session = registry['continuity']
    folder = control / 'notifications/evidence' / path.stem; folder.mkdir(parents=True, exist_ok=True)
    # Recover a completed role turn before launching another notification.
    for log in folder.glob('attempt-*.jsonl'):
        if any(item.get('type') == 'turn.completed' for item in records(log)):
            job.update(status='delivered', delivered_at=time.time(), session_id=session, recovered_log=str(log))
            atomic(path, job); return job
    attempt = job.get('attempts', 0) + 1
    output = folder / f'attempt-{attempt}.txt'
    log = folder / f'attempt-{attempt}.jsonl'
    policy = job.setdefault('invocation_policy', config['role_policies']['continuity'])
    argv = invocation(config['codex'], session, policy, output, cwd=control / 'continuity')
    prompt = ('You are the canonical PocketLore continuity chat, not an implementation worker. '
              'Record this exact completion event in your conversation context; if its event ID is already recorded, acknowledge without duplicating work. '
              'All persisted responses must be English. The runner owns implementation; do not edit, dispatch, or read private holdout. '
              'Read CURRENT_STATE and the full English RESEARCH.md and PLAN.md under the private context directory when needed for handoff. '
              'Acknowledge the exact task, commit, result, next step and event ID in a short English response.\n' + json.dumps(job['payload']))
    job.update(attempts=attempt, status='delivering', session_id=session, argv=argv, last_started=time.time())
    atomic(path, job)
    try:
        with log.open('w') as out:
            result = run(argv, input=prompt, text=True, stdout=out, stderr=subprocess.STDOUT,
                         cwd=control / 'continuity', timeout=180)
        succeeded = result.returncode == 0 and any(item.get('type') == 'turn.completed' for item in records(log))
        error = None if succeeded else f'Continuity process exit {result.returncode}; completion event required'
    except (OSError, subprocess.TimeoutExpired) as exc:
        succeeded, error = False, str(exc)
    job.update(status='delivered' if succeeded else 'pending', last_error=error,
               retry_after=0 if succeeded else time.time() + min(300, 5 * 2 ** min(attempt, 6)), log=str(log))
    if succeeded:
        job['delivered_at'] = time.time()
    atomic(path, job)
    return job


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--control', required=True); parser.add_argument('--once', action='store_true')
    args = parser.parse_args(); control = pathlib.Path(args.control)
    (control / 'notifications/pending').mkdir(parents=True, exist_ok=True)
    (control / 'continuity').mkdir(exist_ok=True)
    with (control / 'state/continuity-notifier.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while True:
            for path in sorted((control / 'notifications/pending').glob('*.json')):
                deliver(control, path)
            if args.once:
                return
            # Delivery is independent of product dispatch; this wait only schedules retry.
            time.sleep(5)

if __name__ == '__main__':
    main()
