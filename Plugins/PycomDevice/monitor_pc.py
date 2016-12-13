import time
import struct
import os
import json

class TransferError(Exception):
    pass

class MonitorPC(object):
    def __init__(self, pyb):
        """
        Load the code that is going to be control the Pycom Board, execute it, and
        setup the communication channel with it.
        """

        monitor_file = open(os.path.dirname(os.path.realpath(__file__)) + '/monitor.py', 'rb')
        monitor_code = monitor_file.read()
        monitor_file.close()

        self.pyb = pyb
        monitor_code = self.__get_script_parameters(pyb.get_connection_type()) + monitor_code
        self.pyb.enter_raw_repl_no_reset()
        self.pyb.exec_raw_no_follow(monitor_code)
        time.sleep(0.5) # give the Pycom board a little setup time
        self.__setup_channel()

    def __get_script_parameters(self, connection_type):
        # variables that are going to be appended to the monitor code
        if connection_type == 'serial':
            return "connection_type = 'u'\nTIMEOUT = 5000\n"
        else:
            info = self.pyb.get_username_password()
            return "connection_type = 's'\ntelnet_login = ('{}', '{}')\nTIMEOUT = 5000\n".format(info[0], info[1])

    def __setup_channel(self):
        """
        Prepare to work with the monitor mode. In case of WiFi, switch to RAW sockets
        """
        connection_type = self.pyb.get_connection_type()

        if connection_type == 'serial':
            self.connection = self.pyb.connection
            self.connection.reset_input_buffer()
        else:
            # device was stored in the previous call to _connect
            self.pyb.close_dont_notify()
            self.pyb._connect(device="", raw=True)
            self.connection = self.pyb.connection

    def __restore_channel(self):
        """
        Switch back to or previous connection style
        """
        try:
            time.sleep(0.25)
            if self.pyb.get_connection_type() != 'serial':
                self.pyb.close_dont_notify()
                time.sleep(0.25)
                # device was stored in the previous call to _connect
                self.pyb._connect(device="", raw=False)
            self.pyb.exit_raw_repl()
            self.pyb.flush()
        except:
            pass

    @staticmethod
    def get_string_block(string, block, block_size):
        return string[block * block_size: (block + 1) * block_size]

    def __read_exactly(self, length):
        return self.connection.read(length)

    def __read_with_timeout(self, length, timeout):
        return self.connection.read_with_timeout(length, timeout)

    def __send(self, data):
        # escape ESC characters
        self.connection.write(data.replace(b'\x1b', b'\x1b\x1b'))

    def __send_command(self, cmd):
        self.connection.write(b'\x1b' + cmd)

    def read_int16(self):
        return struct.unpack('>H', self.__read_exactly(2))[0]

    def __send_int_16(self, i):
        self.__send(struct.pack('>H', i))

    def __send_int_32(self, i):
        self.__send(struct.pack('>L', i))

    def exit_monitor(self):
        """
        Tell the Monitor code that is running at the Pycom Board to exit
        """
        self.__send_command(b'\x00\xff')
        self.__restore_channel()

    def request_ack(self):
        self.__send_command(b'\x00\x00')
        if self.__read_with_timeout(3, 5.0) != b'\x1b\x00\x00':
            raise TransferError()

    def reset_board(self):
        self.__send_command(b'\x00\xfe')
        time.sleep(1)
        self.__restore_channel()

    def write_file(self, name, content):
        """
        Write a file in the Pycom Board

        Send the write command, the len of the filename, the filename
        len of the contents and finally the contents.

        Contents are sent in 256 bytes long chunks. A request for acknowledge
        is sent between those chunks
        """
        data_len = len(content)
        self.__send_command(b'\x01\x00')
        self.__send_int_16(len(name))
        self.__send(name)
        self.__send_int_32(len(content))
        time.sleep(0.3)
        for i in range(1 + data_len // 256):
            self.__send(MonitorPC.get_string_block(content, i, 256))
            self.request_ack()

    def read_file(self, name):
        self.__send_command(b'\x01\x01')
        self.__send_int_16(len(name))
        self.__send(name)
        file_len = struct.unpack('>L', self.pyb.connection.read(4))[0]
        if file_len == 0xFFFFFFFF:
            return None
        return self.__read_exactly(file_len)

    def remove_file(self, name):
        self.__send_command(b'\x01\x02')
        self.__send_int_16(len(name))
        self.__send(name)

    def req_last_file_hash(self):
        self.__send_command(b'\x01\x03')
        return self.__read_exactly(self.read_int16())

    def create_dir(self, name):
        self.__send_command(b'\x01\x04')
        self.__send_int_16(len(name))
        self.__send(name)

    def remove_dir(self, name):
        self.__send_command(b'\x01\x05')
        self.__send_int_16(len(name))
        self.__send(name)
