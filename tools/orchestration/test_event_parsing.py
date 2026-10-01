"""Mixed validation stdout must never crash or masquerade as role events."""
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from runner import Runner, codex_events


MIXED = b'''0.375
42
true
"text"
null
[]
[{"type":"turn.completed"}]
plain output
{malformed
{}
{"type":null}
{"type":["thread.started"]}
{"type":"unrecognized","thread_id":"wrong"}
{"type":"thread.started"}
{"type":"thread.started","thread_id":12}
{"type":"thread.started","thread_id":""}
{"type":"thread.started","thread_id":"expected-id"}
{"type":"turn.completed","usage":{"output_tokens":3}}
'''


class EventParsing(unittest.TestCase):
    def test_accept_only_recognized_well_shaped_objects_preserving_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'mixed.log'; path.write_bytes(MIXED)
            self.assertEqual(list(codex_events(path)), [
                {'type':'thread.started','thread_id':'expected-id'},
                {'type':'turn.completed','usage':{'output_tokens':3}}])
            self.assertEqual(path.read_bytes(), MIXED)

    def test_validation_stdout_and_recovered_receipt_do_not_repeat_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); runner = Runner(root, root)
            task = {'id':'mixed-validation','attempt':0}; counter = root/'executions'
            program = ('from pathlib import Path; import sys; '
                       f'p=Path({str(counter)!r}); p.write_bytes(p.read_bytes()+b"x" if p.exists() else b"x"); '
                       f'sys.stdout.buffer.write({MIXED!r})')
            result = runner.run_process(task, 'check-1', ['python3','-c',program], root)
            self.assertEqual(result['returncode'], 0)
            self.assertEqual(pathlib.Path(result['log']).read_bytes(), MIXED)
            self.assertNotIn('check-1_session_id',task)
            recovered = Runner(root,root).run_process(task,'check-1',['/must/not/relaunch'],root)
            self.assertEqual(recovered,result);self.assertEqual(counter.read_bytes(),b'x')

    def test_receiptless_validation_recovery_keeps_old_and_new_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory); folder=root/'evidence/check';folder.mkdir(parents=True)
            log=folder/'check-0-0.jsonl';log.write_bytes(MIXED)
            task={'id':'check','attempt':0}
            result=Runner(root,root).run_process(task,'check-0',['python3','-c','print("fresh validation")'],root)
            self.assertEqual(result['returncode'],0)
            self.assertEqual(log.read_bytes(),MIXED+b'fresh validation\n')
            self.assertNotIn('check-0_session_id',task)
            self.assertNotIn('recovered_completed_turn',result)

    def test_successful_codex_turn_recovery_ignores_mixed_output(self):
        for phase in ('builder','critic'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root=pathlib.Path(directory);folder=root/'evidence/role';folder.mkdir(parents=True)
                log=folder/f'{phase}-0.jsonl';log.write_bytes(MIXED)
                task={'id':'role','attempt':0}
                result=Runner(root,root).run_process(task,phase,['/must/not/relaunch'],root)
                self.assertTrue(result['recovered_completed_turn'])
                self.assertEqual(task[f'{phase}_session_id'],'expected-id')
                self.assertEqual(json.loads((folder/f'{phase}-0.receipt.json').read_text())['returncode'],0)
                self.assertEqual(log.read_bytes(),MIXED)
                self.assertEqual(Runner(root,root).run_process(task,phase,['/must/not/relaunch'],root),result)

    def test_fresh_codex_completion_scan_handles_mixed_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);runner=Runner(root,root)
            (root/'runner').mkdir();(root/'roles').mkdir()
            policy={'approval_policy':'never','sandbox_mode':'read-only','add_dirs':[]}
            (root/'runner/config.json').write_text(json.dumps({'codex':'unused','role_policies':{'critic':policy}}))
            (root/'roles/sessions.json').write_text(json.dumps({'critic':'expected-id'}))
            original_popen=subprocess.Popen
            def launch(argv,**kwargs):
                return original_popen(['python3','-c',f'import sys; sys.stdout.buffer.write({MIXED!r})'],**kwargs)
            task={'id':'role','attempt':0}
            with patch('runner.subprocess.Popen',side_effect=launch):
                result=runner.run_process(task,'critic',['unused'],root)
            self.assertEqual(result['returncode'],0)
            self.assertEqual(task['critic_session_id'],'expected-id')
            self.assertNotIn('process',task)
            self.assertEqual(pathlib.Path(result['log']).read_bytes(),MIXED)

if __name__=='__main__':unittest.main()
