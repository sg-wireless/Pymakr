import unittest
import sys

sys.path.append("../")

from monitor_pc import Sync

class TestMonitor(unittest.TestCase):
    def setUp(self):
        self.local  = [('file1', 'f'), ('file2', 'f')                ]
        self.remote = [('file1', 'f'),                 ('file3', 'f')]

        self.sync = Sync(self.local, self.remote)
        
    def test_init(self):
        self.assertEqual(self.sync.local, frozenset(self.local))
        self.assertEqual(self.sync.remote, frozenset(self.remote))
   
    def test_update(self):
        self.assertEqual(self.sync.to_update(), [('file1', 'f')])

    def test_create(self):
        self.assertEqual(self.sync.to_create(), [('file2', 'f')])
 
    def test_delete(self):
        self.assertEqual(self.sync.to_delete(), [('file3', 'f')])

    def test_filter_by_type(self):
        self.assertEqual(self.sync.filter_by_type([('file1', 'f'), ('dir1', 'd')], 'f'), ['file1'])
   
    def tearDown(self):
        pass