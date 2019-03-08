from socket import *
from datetime import date
import logging
import sys
import queue
import threading
from classes.device import Device


class SaveMessageToDb(object):

    @staticmethod
    def save(dataMessages):
        from db.connect import pgconn, cursor
        query = "INSERT INTO contacts (name, subject, description, image, email, created_at, updated_at) VALUES (%s, %s, %s,%s,%s,%s,%s);"
        data = ('sassss', 'testt', 'my subject', '', 'my@mail.ru', '1992-12-12', '1992-12-11')
        cursor.execute(query, data)
        pgconn.commit()


class LogData(object):

    @staticmethod
    def receiveLog(nameFile, datalog):
        path = str('loggers/receives/') + str(nameFile) + str('.log')
        logging.basicConfig(filename=path, level=logging.DEBUG)
        logging.info(f' Receive Message: {datalog}')

class Main(threading.Thread):
    def __init__(self, host, port, message_queue, output_queue, data=[]):
        self.__message_queue = message_queue
        self.__output_queue = output_queue
        self.__host = host
        self.__port = port
        self.__data = data
        self.udp_socket = None
        self.addr = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            udp_socket.bind((self.__host, self.__port))
            today = date.today()
            while True:
                conn, addr = udp_socket.recvfrom(10240)
                print('socket start')
                self.udp_socket = udp_socket
                self.addr = addr
                if conn:
                    self.__output_queue.put_nowait(conn)
                    dataList = bytearray(b'{}'.format(conn))
                    if dataList:
                        data = []
                        for line in dataList:
                            data.append(line)
                        self.__data = data
                        LogData.receiveLog(today, Runner)
                        # SaveMessageToDb.save(data)
                        self.receiver()
            udp_socket.close()
        except Exception:
            print("Error:")
            print(sys.exc_info())
            print("Stopping socket server")
            pass

    def receiver(self):
        args = self.__data
        if (args[0] & 0x80) == 0:
            at = 2
            id = int((args[0] << 8) | args[1]) + 7560000
            if id > 7589999:
                return
        else:
            if args[0] >= 0x90:
                return
            at = 3
            id = int((args[0] << 16) | (args[1] << 8) | args[2])
            id -= 0x800000 - 7590000

            if id > 7999999:
                return

        if at >= len(args):
            return

        try:
            device = Device(id)
            if device != None:
                tx = device.process(args, at)
                if tx != None:
                    print('start send socket')
                    self.udp_socket.sendto(tx, self.addr)
                    print('end send socket')
        except Exception:
            print('device not exist')


class Runner:
    def __init__(self, host, port):
        self.__output_queue = queue.Queue(0)
        self.__message_queue = queue.Queue(0)
        self.host = host
        self.port = port

    def run(self):
        server = Main(self.host, self.port, self.__message_queue, self.__output_queue)
        server.start()
        print("Starting main server thread")

    def read(self):
        try:
            return self.__output_queue.get_nowait()
        except queue.Empty:
            print("Empty queue")
            return False

    def stop(self):
        print("Sending exit message to socket thread")
        self.__message_queue.put("exit")
