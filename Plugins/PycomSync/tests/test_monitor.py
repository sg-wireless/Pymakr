import unittest
import sys
import random
import string
import binascii

from mock import Mock

from mock import patch
from mock import call

sys.path.append("../")

from monitor import Monitor

class TestHelper():
    @staticmethod
    def get_string_block(string, block, block_size):
        return string[block * block_size: (block + 1) * block_size]

class TestMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_comm_patch = patch("monitor.InbandCommunication")
        self.mock_comm = self.mock_comm_patch.start()
        self.monitor = Monitor()

    def test_init(self):
        self.mock_comm.assert_called_once_with(sys.stdin)

    def test_block_split_helper(self):
        self.assertEqual(Monitor.block_split_helper(2047), (2047, 0), "test with a byte less than a block")
        self.assertEqual(Monitor.block_split_helper(2048), (2048, 0), "test with a round block")
        self.assertEqual(Monitor.block_split_helper(2049), (2048, 1), "test with a byte more than a block")

    def test_exit(self):
        self.monitor.stream.read_field.return_value = ("monitor.exit", True)
        mock_sys_patch = patch("monitor.sys")
        mock_sys = mock_sys_patch.start()
        self.monitor._Monitor__listening = True
        self.monitor.read_data_or_commands()
        self.assertEqual(self.monitor._Monitor__listening, False)
        mock_sys_patch.stop()
        self.assertEqual(self.monitor.commands["monitor.exit"], self.monitor.exit_monitor, "test the exit monitor command is in the library")

    @patch("monitor.open", create=True)
    def test_write_to_file(self, mock_open):
        file_mock = Mock()
        mock_open.return_value = file_mock
        self.monitor.read_data_or_commands = Mock()
        test_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(4097))
        self.monitor.read_data_or_commands.side_effect = ["test.txt", "4097", 
            binascii.b2a_base64(TestHelper.get_string_block(test_string, 0, 2048)),
            binascii.b2a_base64(TestHelper.get_string_block(test_string, 1, 2048)),
            binascii.b2a_base64(TestHelper.get_string_block(test_string, 2, 2048))]
        self.monitor.write_to_file()
        mock_open.assert_called_once_with("test.txt", "w")
        self.assertEqual(file_mock.write.call_count, 3, "test if it read from stdin 3 times")
        file_mock.write.assert_has_calls([
            call(TestHelper.get_string_block(test_string, 0, 2048)),
            call(TestHelper.get_string_block(test_string, 1, 2048)),
            call(TestHelper.get_string_block(test_string, 2, 2048))])
        self.assertEqual(self.monitor.commands["file.write"], self.monitor.write_to_file, "test the write command is in the library")

    @patch("monitor.open", create=True)
    def test_read_file(self, mock_open):
        mock_sys_patch = patch("monitor.sys")
        mock_sys = mock_sys_patch.start()
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()

        file_mock = Mock()
        mock_open.return_value = file_mock
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "test.txt"
        simulated_content = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(4097))
        file_mock.read.side_effect = [
            TestHelper.get_string_block(simulated_content, 0, 2048),
            TestHelper.get_string_block(simulated_content, 1, 2048),
            TestHelper.get_string_block(simulated_content, 2, 2048)]


        mock_os.stat.return_value = Mock()
        sim_len = [0] * 7
        sim_len[6] = len(simulated_content)
        mock_os.stat.return_value = sim_len

        self.monitor.read_from_file()
        mock_os.stat.assert_called_once_with("test.txt")
        mock_open.assert_called_once_with("test.txt", "r")
        self.assertEqual(file_mock.read.call_count, 3, "test if it read from file 3 times")
        file_mock.close.assert_called_once_with()
        mock_sys.stdout.write.assert_has_calls([call(str(len(simulated_content))), call('\x1F'),
            call(binascii.b2a_base64(TestHelper.get_string_block(simulated_content, 0, 2048))), call('\x1F'),
            call(binascii.b2a_base64(TestHelper.get_string_block(simulated_content, 1, 2048))), call('\x1F'),
            call(binascii.b2a_base64(TestHelper.get_string_block(simulated_content, 2, 2048))), call('\x1F')])
        mock_os_patch.stop()
        mock_sys_patch.stop()

    def test_read_nonexistent_file(self):
        mock_sys_patch = patch("monitor.sys")
        mock_sys = mock_sys_patch.start()        
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "nonexistent.txt"
        mock_os.stat.side_effect = OSError(2)
        self.monitor.read_from_file()
        mock_os.stat.assert_called_once_with("nonexistent.txt")
        mock_sys.stdout.write.assert_has_calls([call(str(-1)), call('\x1F')])
        mock_os_patch.stop()
        mock_sys_patch.stop()

    def test_file_rm(self):
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "test.txt"
        self.monitor.remove_file()
        mock_os.remove.assert_called_once_with("test.txt")

        self.monitor.read_data_or_commands.return_value = "test.txt"
        mock_os.remove.side_effect = OSError(1)
        self.monitor.remove_file()
        mock_os_patch.stop()
        self.assertEqual(self.monitor.commands["file.remove"], self.monitor.remove_file, "test the remove command is in the library")
 
    def test_create_dir(self):
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "test.txt"
        self.monitor.create_dir()
        mock_os.makedirs.assert_called_once_with("test.txt")
        mock_os_patch.stop()
        self.assertEqual(self.monitor.commands["dir.create"], self.monitor.create_dir, "test the create dir command is in the library")

    def test_remove_dir(self):
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "test"
        self.monitor.remove_dir()
        mock_os.rmdir.assert_called_once_with("test")
        mock_os_patch.stop()
        self.assertEqual(self.monitor.commands["dir.remove"], self.monitor.remove_dir, "test the remove dir command is in the library")

    def test_list_dir(self):
        mock_os_patch = patch("monitor.os")
        mock_os = mock_os_patch.start()
        mock_sys_patch = patch("monitor.sys")
        mock_sys = mock_sys_patch.start()  
        self.monitor.read_data_or_commands = Mock()
        self.monitor.read_data_or_commands.return_value = "test"
        mock_os.listdir.return_value = ["file1", "file2"]
        self.monitor.list_dir()
        mock_os.listdir.assert_called_once_with("test")
        mock_sys.stdout.write.assert_has_calls([call(str(len(mock_os.listdir.return_value))), call('\x1F'),
            call(mock_os.listdir.return_value[0]), call('\x1F'),
            call(mock_os.listdir.return_value[1]), call('\x1F')])
        mock_os_patch.stop()
        mock_sys_patch.stop()
        self.assertEqual(self.monitor.commands["dir.list"], self.monitor.list_dir, "test the list dir command is in the library")
      
    def tearDown(self):
        self.mock_comm_patch.stop()

if __name__ == '__main__':
    unittest.main()