"""Coordinator regression tests exercise failure chains and delivery recovery."""
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from protocol import invocation, plan_repair, valid_review
from runner import Runner, atomic
from continuity import publish, deliver, records


class Protocol(unittest.TestCase):
    def task(self):
        return dict(id='runtime', objective='Build actual runtime', scope=['android'], dependencies=[],
                    acceptance_checks=[['true']], artifacts=[], head_commit='abc', status='rework',
                    critic_result={'decision':'rework', 'visible_result':'The runtime failed and requires repair.'})

    def setup_control(self, path):
        atomic(path/'roles/sessions.json', {'builder':'builder-id','critic':'critic-id','continuity':'continuity-id'})
        policy={'approval_policy':'never','sandbox_mode':'read-only','add_dirs':[]}
        atomic(path/'runner/config.json', {'codex':'codex','role_policies':{'builder':policy,'critic':policy,'continuity':policy}})
        (path/'continuity').mkdir(exist_ok=True)

    def test_repair_chain_survives_restart_and_terminates(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory); r=Runner(p,p); t=self.task()
            ids=[]
            for number in range(4):
                r.state['tasks'][t['id']]=t; r.save(); r=Runner(p,p)
                next_task=plan_repair(r.state['tasks'][t['id']])
                if number==3:
                    self.assertIsNone(next_task)
                    break
                ids.append(next_task['id'])
                if number==2:
                    self.assertTrue(next_task['strategy_change_required'])
                    self.assertEqual(next_task['approach_id'],'runtime:alternative')
                    self.assertTrue(any('strategy-change.md' in a for a in next_task['artifacts']))
                t={**next_task, 'head_commit':'failed', 'status':'rework', 'critic_result':self.task()['critic_result']}
            self.assertEqual(ids,['runtime-repair-1','runtime-repair-2','runtime-strategy-change'])
            t['status']='blocked'; r.state['tasks'][t['id']]=t
            r.state['tasks']['independent']={**self.task(),'id':'independent','status':'pending'}
            r.state['tasks']['dependent']={**self.task(),'id':'dependent','status':'pending','dependencies':['runtime']}
            self.assertEqual([x['id'] for x in r.ready_tasks()],['independent'])

    def test_review_word_sentence_and_language_guards(self):
        good={'decision':'continue','visible_result':'The emulator checks pass, but physical device acceptance remains open.'}
        self.assertTrue(valid_review(good))
        for sentence in ['', 'The checks pass. Another sentence fails.', 'The checks pass!Another fails.',
                         'The checks pass\nbut need review.', 'The checks pass', 'The ' + 'word '*35 + 'passes.',
                         '\u00d6nceki engel giderilmi\u015ftir.']:
            self.assertFalse(valid_review({**good,'visible_result':sentence}),sentence)
        self.assertTrue(valid_review({**good,'visible_result':'The ' + 'word '*33 + 'passes.'}))

    def test_invocation_preserves_policy_without_bypass(self):
        policy={'approval_policy':'never','sandbox_mode':'workspace-write','add_dirs':['/specific/cache'],'network_access':True}
        args=invocation('codex','exact-id',policy,'out.json')
        self.assertEqual(args[:5],['codex','-a','never','-s','workspace-write'])
        self.assertIn('/specific/cache',args); self.assertIn('exact-id',args)
        self.assertNotIn('--last',args); self.assertFalse(any('bypass' in x for x in args))
        with self.assertRaises(ValueError):invocation('codex','exact-id',{**policy,'sandbox_mode':'danger-full-access'},'out')

    def test_completion_replay_repairs_outbox_without_duplicate_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory);self.setup_control(p);t=self.task();event={'id':'runtime:completion','time':1}
            state={'last_known_good_commit':'abc'}
            # Crash after durable ledger append, before outbox/state publication.
            import runner
            original=runner.atomic
            def fault(path,value):
                if '/notifications/' in str(path):raise OSError('injected outbox failure')
                return original(path,value)
            with patch('runner.atomic',side_effect=fault):
                with self.assertRaises(OSError):publish(p,event,t,state,'independent')
            publish(p,event,t,state,'independent');publish(p,event,t,state,'independent')
            self.assertEqual(len(records(p/'state/continuity-ledger.jsonl')),1)
            self.assertEqual(len(list((p/'notifications/pending').glob('*.json'))),1)
            text=(p/'context/CURRENT_STATE.md').read_text()
            for word in ['runtime','abc','rework','independent']:self.assertIn(word,text)

    def test_notification_failure_retries_and_recovery_avoids_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory);self.setup_control(p)
            publish(p,{'id':'runtime:completion','time':1},self.task(),{'last_known_good_commit':'abc'},'independent')
            path=p/'notifications/pending/runtime-completion.json'
            def failed(*args,**kwargs):return subprocess.CompletedProcess(args[0],1)
            first=deliver(p,path,run=failed);self.assertEqual(first['status'],'pending')
            first['retry_after']=0;atomic(path,first)
            def success(*args,**kwargs):
                self.assertIn('continuity-id',args[0]);kwargs['stdout'].write('{"type":"turn.completed"}\n')
                return subprocess.CompletedProcess(args[0],0)
            second=deliver(p,path,run=success);self.assertEqual(second['status'],'delivered')
            second['status']='delivering';atomic(path,second)
            with patch('subprocess.run',side_effect=AssertionError('must not relaunch')):
                recovered=deliver(p,path,run=lambda *a,**kw: self.fail('duplicate delivery'))
            self.assertEqual(recovered['status'],'delivered');self.assertIn('recovered_log',recovered)

    def test_canonical_critic_session_receives_only_evidence_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory);self.setup_control(p);r=Runner(p,p)
            t={'id':'runtime','attempt':0}
            class Fake:
                pid=123
                def __init__(self,*args,**kwargs):
                    self.argv=args[0];self.stdin=__import__('io').StringIO()
                    self.assertions=kwargs
                def wait(self):return 0
            with patch('runner.subprocess.Popen',Fake):
                r.run_process(t,'critic',['codex'],p,'Inspect only immutable evidence.json; no private chat or builder logs.')
            self.assertEqual(t['critic_session_id'],'critic-id')
            self.assertIn('critic-id',t['invocations']['critic'])
            self.assertEqual(t['invocation_policies']['critic']['sandbox_mode'],'read-only')

if __name__=='__main__':unittest.main()
