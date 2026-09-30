"""Role invocation, review validation and bounded repair protocol."""
import json
import re


def invocation(codex, session_id, policy, output, schema=None, cwd=None):
    if not session_id:
        raise ValueError('An explicit canonical session ID is required')
    if policy.get('approval_policy') not in ('never', 'on-request'):
        raise ValueError('An explicit approval policy is required')
    if policy.get('sandbox_mode') not in ('read-only', 'workspace-write'):
        raise ValueError('Persist a scoped sandbox policy; blanket bypass is forbidden')
    args = [codex, '-a', policy['approval_policy'], '-s', policy['sandbox_mode']]
    if cwd:
        args += ['-C', str(cwd)]
    for directory in policy.get('add_dirs', []):
        args += ['--add-dir', directory]
    if policy.get('network_access', False):
        args += ['-c', 'sandbox_workspace_write.network_access=true']
    args += ['exec', 'resume', '--skip-git-repo-check', '--json', '-o', str(output)]
    if schema:
        args += ['--output-schema', str(schema)]
    return args + [session_id, '-']


def valid_review(verdict):
    """Conservative format/language guard, not a proof of semantic English fluency."""
    if verdict.get('decision') not in ('continue', 'rework', 'unsupported'):
        return False
    text = verdict.get('visible_result', '')
    if not isinstance(text, str) or not text.strip() or text != text.strip():
        return False
    if '\n' in text or '\r' in text or len(text.split()) > 35:
        return False
    if not re.fullmatch(r'[^.!?]+[.!?]', text):
        return False
    # English text can use typographic punctuation, but these are Turkish letters.
    if re.search('[\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc]', text):
        return False
    words = set(re.findall(r'[a-z]+', text.lower()))
    return bool(words & {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'and', 'but', 'with', 'without', 'requires', 'remains', 'passes', 'passed', 'failed', 'cannot', 'supports'})


def plan_repair(task):
    """Persisted ordinal, never a count that can shrink when statuses change."""
    root = task.get('repair_of', task['id'])
    ordinal = task.get('repair_ordinal', 0) + 1
    if ordinal > 3:
        return None
    repair = {k: task[k] for k in ('objective', 'scope', 'acceptance_checks', 'artifacts', 'dependencies')}
    changed = ordinal == 3
    repair.update(id=root + ('-strategy-change' if changed else f'-repair-{ordinal}'),
                  repair_of=root, repair_ordinal=ordinal,
                  approach_id=(root + ':alternative' if changed else task.get('approach_id', root + ':initial')),
                  strategy_change_required=changed)
    repair['prompt'] = ('Inspect preserved failed checkpoint ' + task['head_commit'] + '. Critic: ' +
                        json.dumps(task['critic_result']) + '. Recover useful prior changes on the current checkpoint branch. ')
    if changed:
        repair['objective'] = 'Use a materially different approach to complete: ' + task['objective']
        repair['prompt'] += ('The initial approach has failed three times; do not repeat it. First write docs/evidence/' +
                             root + '-strategy-change.md describing the failures, materially different design and discriminating checks. ')
        repair['artifacts'] = list(repair['artifacts']) + ['docs/evidence/' + root + '-strategy-change.md']
    else:
        repair['prompt'] += 'Repair this bounded task and preserve actual evidence.'
    return repair
