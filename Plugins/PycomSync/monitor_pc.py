import time
import struct
import os
import struct
import binascii
import json
import serial

class Sync():
    def __init__(self, local, remote):
        self.local = frozenset(local)
        self.remote = frozenset(remote)

    def to_update(self):
        return list(self.local & self.remote)

    def to_create(self):
        return list(self.local - self.remote)

    def to_delete(self):
        return list(self.remote - self.local)

    def filter_by_type(self, l, by):
        return [i[0].encode('utf-8') for i in l if i[1] == by] # encode is done here because somehow the & operator over two frozensets convert bytes to unicode without being asked

    def filter_by_type_order_by_depth(self, l, by, orderby, reverse=False):
        # yeah... I know...
        # encode is done here because somehow the & operator over two frozensets convert bytes to unicode without being asked
        return [j[0] for j in sorted([(i[0].encode('utf-8'), i[2]) for i in l if i[1] == by], key=lambda tup: tup[1], reverse=reverse)]


class Monitor_PC():
    def __init__(self, pyb):
        f = open(os.path.dirname(os.path.realpath(__file__)) + '/monitor.py', 'rb')
        monitor_code = f.read()
        f.close()

        self.pyb = pyb
        monitor_code = self.__get_script_parameters(pyb.get_connection_type()) + monitor_code
        self.pyb.enter_raw_repl_no_reset()
        self.pyb.exec_raw_no_follow(monitor_code)
        time.sleep(0.5)
        self.__setup_channel()

    def destroy(self):
        self.exit_monitor()

    def __get_script_parameters(self, connection_type):
        if connection_type == 'serial':
            return "connection_type = 'u'\n"
        else:
            info = self.pyb.get_username_password()
            return "connection_type = 's'\ntelnet_login = ('{}', '{}')\n".format(info[0], info[1])

    def __setup_channel(self):
        connection_type = self.pyb.get_connection_type()

        if connection_type == 'serial':
            self.connection = self.pyb.connection
            self.connection.stream.reset_input_buffer()
        else:
            self.pyb._connect(device="", raw=True) # device was stored in the previous call to _connect
            self.connection = self.pyb.connection

    def __restore_channel(self):
        try:
            time.sleep(0.25)
            if self.pyb.get_connection_type() != 'serial':
                time.sleep(0.1)
                self.pyb._connect(device="", raw=False) # device was stored in the previous call to _connect
            self.pyb.exit_raw_repl()
            self.pyb.flush()
        except:
            pass

    @staticmethod
    def get_string_block(string, block, block_size):
        return string[block * block_size: (block + 1) * block_size]

    def __read_exactly(self, n):
        return self.connection.read(n)

    def __send(self, data):
        self.connection.write(data.replace(b'\x1b', b'\x1b\x1b'))

    def __send_command(self, cmd):
        self.connection.write(b'\x1b' + cmd)

    def read_int16(self):
        return struct.unpack('>H', self.__read_exactly(2))[0]

    def __send_int_16(self, i):
        self.connection.write(struct.pack('>H', i))

    def __send_int_32(self, i):
        self.connection.write(struct.pack('>L', i))

    def exit_monitor(self):
        self.__send_command(b'\x00\xff')
        self.__restore_channel()

    def request_ack(self):
        self.__send_command(b'\x00\x00')
        if self.__read_exactly(3) != b'\x1b\x00\x00':
            raise Exception() #todo: add a real exception

    def reset_board(self):
        self.__send_command(b'\x00\xfe')
        time.sleep(1)
        self.__restore_channel()

    def write_file_contents(self, name, content):
        data_len = len(content)
        self.__send_command(b'\x01\x00')
        self.__send_int_16(len(name))
        self.__send(name)
        self.__send_int_32(len(content))
        for i in range(1 + data_len // 256):
            self.__send(Monitor_PC.get_string_block(content, i, 256))
            self.request_ack()

    def write_file(self, local_name, remote_name=None):
        with open(local_name, 'r') as content_file:
            content = content_file.read()

        if remote_name == None:
            remote_name = b'/flash/' + local_name
        self.write_file_contents(remote_name, content)

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

    def sync(self, local, remote):
        s = Sync(local, remote)

        # delete unused files
        map(self.remove_file, s.filter_by_type(s.to_delete(), b'f'))

        # then delete unused directories
        map(self.remove_dir, s.filter_by_type_order_by_depth(s.to_delete(), b'd', True))

        # now create new directories
        map(self.create_dir, s.filter_by_type_order_by_depth(s.to_create(), b'd', False))

        # upload the new files
        map(self.write_file, s.filter_by_type(s.to_create(), b'f'))

        # and update the ones that changed
        map(self.write_file, s.filter_by_type(s.to_update(), b'f'))


    def sync_pyboard(self, local):
        remote = self.read_file("/flash/project.pymakr")
        if remote == None:
            remote = []
        else:
            remote = json.loads(remote)

        for i in range(len(remote)):
            remote[i] = tuple(remote[i])

        self.sync(local, remote)

        self.write_file_contents("/flash/project.pymakr", json.dumps(local))