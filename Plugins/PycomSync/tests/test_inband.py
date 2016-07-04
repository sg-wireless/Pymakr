import unittest
import sys

from mock import Mock

from mock import patch

sys.path.append("../")

from monitor import InbandCommunication


class TestInbandCommunication(unittest.TestCase):
    def setUp(self):
        self.mock_sys = Mock()
        self.inband = InbandCommunication(self.mock_sys.stdin)

    def test_command_detection(self):
        self.mock_sys.stdin.read.side_effect = ['\x1b', 'a', '\x1F']
        self.assertEqual(("a", True), self.inband.read_field(), "test command detection")

    def test_in_middle_command_detection(self):
        self.mock_sys.stdin.read.side_effect = ['b', '\x1b', 'a', '\x1F']
        self.assertEqual(("a", True), self.inband.read_field(), "test in the middle command detection")

    def test_regular_field_detection(self):
        self.mock_sys.stdin.read.side_effect = ['a', 'm', 'b', '\x1F']
        self.assertEqual(("amb", False), self.inband.read_field(), "test regular field detection")

if __name__ == '__main__':
    unittest.main()