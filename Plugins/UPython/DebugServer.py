from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from threading import Thread
import pyboard
import time

class DebugServer(QObject):
    clientOutput = pyqtSignal(str)
    statusChanged = pyqtSignal(str)

    def __init__(self):
        super(DebugServer, self).__init__()
        self.__shutdown = False

    def connect(self):
        try:
            if self.getStatus() == True:
                return True
        except:
            pass

        try:
            if self.__rxThread:
                return True
        except:
            pass

        try:
            if not self.__device:
                return False
            self.__rxThread = Thread(target=self.__recvBackground, args=())
            self.__rxThread.start()
        except:
            return False

        return True

    def disconnect(self):
        try:
            self.__shutdown = True
            self.__connection.close()
        except:
            pass

    def shutdown(self):
        self.__shutdown = True

    def setConnectionParameters(self, device, user, password):
        self.__device = device
        self.__user = user
        self.__password = password

    def isConfigured(self):
        # return False on empty or None
        return not not self.__device

    def getStatus(self):
        try:
            return self.__connection.check_connection()
        except:
            return False

    def __recvBackground(self):
        self.__shutdown = False
        while self.__shutdown == False:
            try:
                self.statusChanged.emit("connecting")
                self.__connection = pyboard.Pyboard(device=self.__device,
                    user=self.__user, password=self.__password, keep_alive=3)
                self.__connection.reset()
                self.statusChanged.emit("connected")
                self.__connection.recv(self.signalClientOutput)
                self.statusChanged.emit("disconnected")
            except pyboard.PyboardError as er:
                if str(er) == "Invalid credentials":
                    self.statusChanged.emit("invcredentials")
                    break
                elif str(er) == "\nInvalid address":
                    self.statusChanged.emit("invaddress")
                    break
                else:
                    self.statusChanged.emit("error")
            except:
                self.statusChanged.emit("error")

            if self.__keepTrying == False or self.__shutdown == True:
                break
            else:
                self.statusChanged.emit("reattempt")
                for t in xrange(0, 15 * 4):
                    time.sleep(1.0 / 4)
                    if self.__shutdown == True:
                        break
        self.__rxThread = None


    def signalClientOutput(self, text):
        self.clientOutput.emit(text)

    def send(self, text):
        try:
            self.__connection.send(text)
        except:
            pass

    def restart(self):
        try:
            if self.getStatus() == True:
                self.disconnect()
            if self.__keepTrying == True:
                time.sleep(0.25)
                self.connect()
        except:
            pass

    @pyqtSlot(bool)
    def tryConnecting(self, state):
        self.connect()
        self.__keepTrying = state
