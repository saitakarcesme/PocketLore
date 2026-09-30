"""Recovery contracts without launching inference or modifying a real repository."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import importlib.util, json, pathlib, subprocess, tempfile, unittest
spec = importlib.util.spec_from_file_location('runner', pathlib.Path(__file__).with_name('runner.py'))
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class Recovery(unittest.TestCase):
    def test_events_are_idempotent_and_state_is_reloadable(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = module.Runner(directory, directory)
            self.assertTrue(runner.event('task:completion', status='accepted'))
            other = module.Runner(directory, directory)
            self.assertFalse(other.event('task:completion', status='accepted'))
            self.assertEqual(len(other.state['events']), 1)

    def test_completed_process_receipt_prevents_duplicate_work(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = module.Runner(directory, directory)
            task = {'id': 'smoke', 'attempt': 0}
            output = pathlib.Path(directory)/'counter'
            command = ['python3', '-c', f'from pathlib import Path; p=Path({str(output)!r}); p.write_text(p.read_text()+"x" if p.exists() else "x")']
            first = runner.run_process(task, 'check', command, directory)
            recovered = module.Runner(directory, directory)
            second = recovered.run_process(task, 'check', command, directory)
            self.assertEqual(first, second)
            self.assertEqual(output.read_text(), 'x')

    def test_completed_turn_recovers_without_launching_another_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = module.Runner(directory, directory)
            task = {'id': 'crash-window', 'attempt': 0}
            folder = pathlib.Path(directory)/'evidence/crash-window'; folder.mkdir(parents=True)
            (folder/'builder-0.jsonl').write_text('{"type":"thread.started","thread_id":"explicit-test-id"}\n{"type":"turn.completed"}\n')
            result = runner.run_process(task, 'builder', ['/does/not/exist'], directory)
            self.assertTrue(result['recovered_completed_turn'])
            self.assertEqual(task['builder_session_id'], 'explicit-test-id')

    def test_freeze_recovers_after_crash_between_chmod_and_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'evidence.log'
            source = pathlib.Path(module.__file__).resolve()
            program = (
                'import importlib.util, os, sys; '
                f'sys.path.insert(0, {str(source.parent)!r}); '
                f's=importlib.util.spec_from_file_location("runner", {str(source)!r}); '
                'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
                'm.os.replace=lambda *args: os._exit(42); '
                f'm.freeze({str(target)!r}, b"durable evidence")'
            )
            crashed = subprocess.run(['python3', '-c', program])
            self.assertEqual(crashed.returncode, 42)
            self.assertFalse(target.exists())
            abandoned = list(pathlib.Path(directory).glob('*.tmp'))
            self.assertEqual(len(abandoned), 1)
            self.assertEqual(abandoned[0].stat().st_mode & 0o777, 0o444)
            module.freeze(target, b'durable evidence')
            module.freeze(target, b'durable evidence')
            self.assertEqual(target.read_bytes(), b'durable evidence')
            with self.assertRaises(RuntimeError):
                module.freeze(target, b'changed evidence')

    def test_ingest_does_not_duplicate_or_reset_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); (root/'tasks').mkdir()
            module.atomic(root/'tasks/test.json', {'id':'test','dependencies':[],'objective':'Test','scope':['test'],'acceptance_checks':[],'artifacts':[]})
            runner = module.Runner(directory, directory); runner.ingest()
            runner.state['tasks']['test']['status']='running'; runner.state['tasks']['test']['phase']='critic'; runner.save()
            recovered = module.Runner(directory,directory); recovered.ingest()
            self.assertEqual(len(recovered.state['tasks']), 1)
            self.assertEqual(recovered.state['tasks']['test']['phase'], 'critic')

if __name__ == '__main__': unittest.main()
