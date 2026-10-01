import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[1]/'full_scale_capacity.py'
s=importlib.util.spec_from_file_location('capacity',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CapacityChecks(unittest.TestCase):
 def test_actual_small_volume(self):
  import json
  root=pathlib.Path(__file__).resolve().parents[3]
  observed=json.loads((root/'docs/evidence/full-scale/repair-1/environment.json').read_text())['filesystems']
  result=m.capacity(observed,41628740516)
  self.assertFalse(result['prerequisite_met']);self.assertEqual(result['total_bytes'],6082144*1024)
 def test_larger_capacity_is_only_prerequisite(self):
  r=m.capacity('/dev/block/dm-43 80000000 1000000 79000000 2% /data',41628740516)
  self.assertTrue(r['prerequisite_met']);self.assertIn('remain required',r['meaning'])
 def test_exact_boundary(self):
  self.assertTrue(m.capacity('/dev/a 10 5 5 50% /data',10240)['prerequisite_met'])
  self.assertFalse(m.capacity('/dev/a 10 5 5 50% /data',10241)['prerequisite_met'])
 def test_no_tmpfs_or_external_substitution(self):
  for text in ['tmpfs 80000000 0 80000000 0% /data','/dev/fuse 80000000 0 80000000 0% /storage/emulated','', '/dev/a 10 20 0 100% /data']:
   with self.assertRaises(ValueError):m.capacity(text,1024)
 def test_ambiguous_mount_rejected(self):
  with self.assertRaises(ValueError):m.capacity('/dev/a 10 5 5 50% /data\n/dev/b 10 5 5 50% /data',1)
if __name__=='__main__':unittest.main()
