import time

import os
import struct
import binascii
import json

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
        return [i[0] for i in l if i[1] == by]


class Monitor_PC():
    def __init__(self, pyb):
        f = open(os.path.dirname(os.path.realpath(__file__)) + '/monitor.py', 'rb')
        monitor_code = f.read()
        f.close()

        self.pyb = pyb
        self.pyb.connection.enable_binary()
        self.pyb.enter_raw_repl_no_reset()
        self.pyb.exec_raw_no_follow(monitor_code)
        time.sleep(0.2)

    def __del__(self):
        try:
            self.pyb.connection.disable_binary()
            self.exit_monitor()
        except:
            pass

    @staticmethod
    def get_string_block(string, block, block_size):
        return string[block * block_size: (block + 1) * block_size]

    def get_record(self):
        return self.pyb.read_until('\x1F')[:-1]
        
    def send_command_mark(self):
        self.pyb.send('\x1B')

    def send_record(self, content):
        self.pyb.send(content)
        self.pyb.send('\x1F')
        time.sleep(0.1)

    def exit_monitor(self):
        self.send_command_mark()
        self.send_record("monitor.exit")
        self.pyb.exit_raw_repl()
        self.pyb.flush()
        
    def keep_alive(self, c):
        self.send_command_mark()
        self.send_record("monitor.keepalive")
        self.send_record(str(c))

    def write_file_contents(self, name, content):
        data_len = len(content)

        self.send_command_mark()
        self.send_record("file.write")
        self.send_record(name)
        self.send_record(str(data_len))
        
        for i in xrange(1 + data_len // 2048):
            # remove trailing char (\n) to deal with micropython bug in a2b
            self.send_record(binascii.b2a_base64(Monitor_PC.get_string_block(content, i, 2048))[:-1]) 

    def write_file(self, local_name, remote_name=None):
        with open(local_name, 'r') as content_file:
            content = content_file.read()

        if remote_name == None:
            remote_name = '/flash/' + local_name
        self.write_file_contents(remote_name, content)

    def read_file(self, name):
        self.send_command_mark()
        self.send_record("file.read")
        self.send_record(name)
        data_len = int(self.get_record())
        if data_len == -1:
            return None

        buf = ""
        
        for i in xrange(1 + data_len // 2048):
            buf += binascii.a2b_base64(self.get_record())
        return buf

    def remove_file(self, name):
        self.send_command_mark()
        self.send_record("file.remove")
        self.send_record(name)

    def create_dir(self, name):
        self.send_command_mark()
        self.send_record("dir.create")
        self.send_record(name)

    def remove_dir(self, name):
        self.send_command_mark()
        self.send_record("dir.remove")
        self.send_record(name)
        
    def list_dir(self, name):
        self.send_command_mark()
        self.send_record("dir.list")
        self.send_record(name)
        items = int(self.get_record())
        result = [''] * items
        for i in range(items):
            result[i] = self.get_record()
        return result

    def sync(self, local, remote):
        s = Sync(local, remote)

        # delete unused files
        map(self.remove_file, s.filter_by_type(s.to_delete(), 'f'))

        # then delete unused directories
        map(self.remove_dir, s.filter_by_type(s.to_delete(), 'd'))

        # now create new directories
        map(self.create_dir, s.filter_by_type(s.to_create(), 'd'))

        # upload the new files
        map(self.write_file, s.filter_by_type(s.to_create(), 'f'))

        # and update the ones that changed
        map(self.write_file, s.filter_by_type(s.to_update(), 'f'))


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