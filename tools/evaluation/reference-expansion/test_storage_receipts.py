"""Synthetic validator controls only; never substitutes for Android observations."""
import copy
import unittest
from verify import verify_storage

class StorageReceiptTest(unittest.TestCase):
    def fixture(self):
        def sample(staged=False):
            rows=['1 1 4096 8','1 2 10000 24','1 2 10000 24']
            if staged: rows.append('1 3 65536 128')
            return dict(stat_rows=rows,unique_inodes=3 if staged else 2,
                        logical=14096+(65536 if staged else 0),
                        allocated=16384+(65536 if staged else 0),
                        covered=16384+(65536 if staged else 0),
                        meter=16384+(65536 if staged else 0),reserved=0)
        result={p:sample(p=='during') for p in ['before','during','after']}
        result['during'].update(reserved=501453+2*256*1024*1024+17*1024*1024,
                                copied_bytes_before_next_read=65536)
        return result

    def test_deduplicated_valid_sample(self):
        verify_storage(self.fixture(),501453)

    def test_negative_controls(self):
        mutations=[('missing-stage',lambda x:x.pop('during')),
                   ('meter-mismatch',lambda x:x['during'].update(meter=1)),
                   ('released-too-soon',lambda x:x['during'].update(reserved=0)),
                   ('reservation-leak',lambda x:x['after'].update(reserved=1)),
                   ('wrong-inode-count',lambda x:x['before'].update(unique_inodes=3)),
                   ('changed-stat',lambda x:x['during']['stat_rows'].append('1 3 10 1'))]
        for name,mutate in mutations:
            with self.subTest(name=name):
                sample=copy.deepcopy(self.fixture());mutate(sample)
                with self.assertRaises((AssertionError,KeyError)):
                    verify_storage(sample,501453)

if __name__=='__main__':unittest.main()
