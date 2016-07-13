import sys
import struct
import os
import binascii

# monitor mode, using a trivial protocol
#
# 0x1b means start of command. If another command was already in progress, abort it and restart
# 0x00 marks an end of a string
#
# All fields are strings. The first field (the one preceded with 0x1b) will be the command name
# The field processing and decoding is done within each command method


try:
    import micropython
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def spy(x):
        try:
            s.sendto(str(x) + '\n', ("192.168.192.11", 3000))
            return x
        except:
            pass

except:
    def spy(x):
        return x

class InbandCommunication():
    def __init__(self, stream):
        self.stream = stream

    def read_field(self):
        buf = bytearray()
        is_command = False

        while True:
            data = self.stream.read(1)
            if data == '\x1F':
                break
            if data == '\x1B':
                is_command = True
                buf = bytearray()
            else:
                buf.extend(data)
        return bytes(buf), is_command

class Monitor():
    def __init__(self):
        self.stream = InbandCommunication(sys.stdin)
        self.inside_command = False
        self.commands = {
            b"monitor.exit": self.exit_monitor,
            b"file.write": self.write_to_file,
            b"file.read": self.read_from_file,
            b"file.remove": self.remove_file,
            b"dir.create": self.create_dir,
            b"dir.remove": self.remove_dir,
            b"dir.list": self.list_dir,
        }

    def read_data_or_commands(self):
        result, command = self.stream.read_field()
        if command == True:
            try:
                if self.inside_command == True:
                    raise Exception("truncated command")
                else:
                    self.inside_command = True
                self.commands[result]()
                self.inside_command = False
            except:
                pass
        return result

    def send_record(self, data):
        sys.stdout.write(data)
        sys.stdout.write('\x1F')

    @staticmethod
    def block_split_helper(length):
        if length > 2048:
            return (2048, length - 2048)
        else:
            return (length, 0)

    def exit_monitor(self):
        self.__listening = False
        
    def write_to_file(self):
        f = open(self.read_data_or_commands(), "w")
        data_len = int(self.read_data_or_commands())
        while data_len > 0:
            buf = binascii.a2b_base64(self.read_data_or_commands())
            data_len -= len(buf)
            f.write(buf)
        f.close()

    def read_from_file(self):
        filename = self.read_data_or_commands()
        try:
            data_len = os.stat(filename)[6]
        except OSError:
            self.send_record(str(-1))
            return
        self.send_record(str(data_len))
        f = open(filename, 'r')
        while data_len != 0:
            to_read, data_len = Monitor.block_split_helper(data_len)
            self.send_record(binascii.b2a_base64(f.read(to_read)))
        f.close()

    def remove_file(self):
        try:
            os.remove(self.read_data_or_commands())
        except OSError:
            pass
            
    def create_dir(self):
        os.makedirs(self.read_data_or_commands())

    def remove_dir(self):
        os.rmdir(self.read_data_or_commands())

    def list_dir(self):
        files = os.listdir(self.read_data_or_commands())
        self.send_record(str(len(files)))
        for el in files:
            self.send_record(el)

    def start_listening(self):
        self.__listening = True
        while (self.__listening):
            self.read_data_or_commands()

if __name__ == '__main__':
    monitor = Monitor()
    monitor.start_listening()