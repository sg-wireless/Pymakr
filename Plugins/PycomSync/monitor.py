import sys
import struct
import os
import select
import hashlib

# This file implements a simple binary protocol for Monitor mode

# Normally, a stream of bytes will flow normally, except for 0x1b, that is used to indicate the start of a RPC
# real (esc) chars need to be escaped.

class SerialPortConnection():
    def __init__(self):
        import machine
        self.__original_term = os.dupterm()
        os.dupterm(None) # disconnect the current serial port connection
        self.__serial = machine.UART(0, 115200)
        self.__poll = select.poll()
        self.__poll.register(self.__serial, select.POLLIN)
        self.write = self.__serial.write

    def destroy(self):
        os.dupterm(self.__original_term)

    def read(self, l):
        self.__poll.poll()
        return self.__serial.read(l)

class SocketConnection():
    def __init__(self):
        from network import Server
        import socket
        server = Server()
        self.__is_telnet_running = server.isrunning()
        server.deinit()
        self.__poll = select.poll()
        listening = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening.bind(('0.0.0.0', 23))
        listening.listen(1)
        self.__socket = listening.accept()[0]
        listening.close()
        self.__poll.register(self.__socket, select.POLLIN)
        self.__socket.setblocking(False)
        self.write = self.__socket.write

    def destroy(self):
        self.__socket.close()
        if self.__is_telnet_running == True:
            from network import Server
            Server().init(login=telnet_login)

    def read(self, l):
        self.__poll.poll()
        return self.__socket.read(l)

class TransferError(Exception):
    def __init__(self, value, str_val):
        self.value = value
        self.str_val = str_val

    def __str__(self):
        return self.str_val

class InbandCommunication():
    def __init__(self, stream, callback):
        self.__stream = stream
        self.__carry_over = b''
        self.__callback = callback

    def read(self, size):
        data = self.__stream.read(size)
        if self.__carry_over != b'': # check if a previous call generated a surplus
            data = self.__carry_over + data
            self.__carry_over = b''
        max_idx = len(data) - 1
        esc_pos = data.find(b'\x1b') # see if there is any ESC in the bytestream
        while esc_pos != -1:
            if esc_pos != max_idx:
                # the ESC is not at the end
                if data[esc_pos + 1] == 0x1b:
                    # this is an escaped ESC
                    data = data[:esc_pos] + data[esc_pos + 1:]
                    esc_pos += 1
                else:
                    # process a real ESC here
                    if max_idx - esc_pos < 2:
                        # no enough bytes to continue
                        # save the ones that belong to the command
                        self.__carry_over = data[esc_pos:max_idx + 1]
                        data = data[0:esc_pos]
                    else:
                        # get the command name
                        command = data[esc_pos + 1:esc_pos + 3]
                        # and store the rest for the next round
                        self.__carry_over = data[esc_pos + 3:max_idx + 1]
                        cont = self.__callback(command)
                        if cont == True:
                            data = data[0:esc_pos]
                        else:
                            raise(TransferError(0, 'aborted'))
                    break

                esc_pos = data.find(b'\x1b', esc_pos)
            else:
                data = data[:-1]
                self.__carry_over = b'\x1b' # buffer the lonely ESC for the future
                break
        return data

    def read_exactly(self, size):
        data = b''
        while 1:
            data += self.read(size)
            if len(data) == size:
                return data

            if len(data) < size:
                continue

            # if in here, len(data) > size, store the surplus bytes
            self.__carry_over = data[size:] + self.__carry_over
            return data[:size]

    def send(self, data):
        self.__stream.write(data)

class Monitor():
    def __init__(self):
        if connection_type == 'u':
            self.__connection = SerialPortConnection()
        else:
            self.__connection = SocketConnection()
        self.__stream = InbandCommunication(self.__connection, self.process_command)
        self.__commands = {
            b"\x00\x00": self.ack,
            b"\x00\xFE": self.reset_board,
            b"\x00\xFF": self.exit_monitor,
            b"\x01\x00": self.write_to_file,
            b"\x01\x01": self.read_from_file,
            b"\x01\x02": self.remove_file,
            b"\x01\x03": self.hash_last_file,
            b"\x01\x04": self.create_dir,
            b"\x01\x05": self.remove_dir,
        }

    def process_command(self, cmd):
        return self.__commands[cmd]()

    def read_int16(self):
        return struct.unpack('>H', self.__stream.read_exactly(2))[0]

    def read_int32(self):
        return struct.unpack('>L', self.__stream.read_exactly(4))[0]

    def write_int16(self, x):
        self.__stream.send(struct.pack('>H', x))

    def write_int32(self, x):
        self.__stream.send(struct.pack('>L', x))

    def init_hash(self, length):
        self.last_hash = hashlib.sha256(b'', length)

    @staticmethod
    def block_split_helper(length):
        if length > 1024:
            return (1024, length - 1024)
        else:
            return (length, 0)

    def ack(self):
        self.__stream.send(b'\x1b\x00\x00')
        return True

    def reset_board(self):
        import machine
        machine.reset()

    def exit_monitor(self):
        self.__running = False
        self.__connection.destroy()

    @staticmethod
    def encode_str_len32(contents):
        return struct.pack('>L', len(contents))

    @staticmethod
    def encode_str_len16(string):
        return struct.pack('>H', len(string))

    def write_to_file(self):
        f = open(self.__stream.read_exactly(self.read_int16()), "w")
        data_len = self.read_int32()
        self.init_hash(data_len)
        while data_len != 0:
            data = self.__stream.read(min(data_len, 256))
            f.write(data)
            self.last_hash.update(data)
            data_len -= len(data)
        f.close()

    def read_from_file(self):
        filename = self.__stream.read_exactly(self.read_int16())
        try:
            data_len = os.stat(filename)[6]
        except OSError:
            self.write_int32(0xFFFFFFFF)
            return
        self.write_int32(data_len)
        self.init_hash(data_len)
        f = open(filename, 'r')
        while data_len != 0:
            to_read, data_len = Monitor.block_split_helper(data_len)
            data = f.read(to_read)
            self.__stream.send(data)
            self.last_hash.update(data)
        f.close()

    def remove_file(self):
        try:
            os.remove(self.__stream.read_exactly(self.read_int16()))
        except OSError:
            pass

    def hash_last_file(self):
        h = self.last_hash.digest()
        self.write_int16(len(h))
        self.__stream.send(h)

    def create_dir(self):
        try:
            os.mkdir(self.__stream.read_exactly(self.read_int16()))
        except OSError:
            pass

    def remove_dir(self):
        try:
            os.rmdir(self.__stream.read_exactly(self.read_int16()))
        except OSError:
            pass

    def start_listening(self):
        self.__running = True
        while self.__running == True:
            try:
                self.__stream.read(1)
            except TransferError:
                pass

if __name__ == '__main__':
    monitor = Monitor()
    monitor.start_listening()
