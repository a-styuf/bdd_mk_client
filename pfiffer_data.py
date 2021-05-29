import os
import time
import serial
import threading


class Pfiffer:
    def __init__(self, cnf={}, **kw):
        self.baudrate = kw.get("baudrate", 19200)
        self.port = kw.get("port", "COM4")
        self.timeout = kw.get("timeout", 0.1)
        # создание третьего окна для тестирования памяти БДД

        #  создание объекта для компорта
        self.ser = serial.Serial()

        self.pfiffer_state = ""
        self.pfiffer1_state = ""
        self.pfiffer2_state = ""

        self.name_list = ["Pfiffer1, Tr", "Pfiffer2, Tr"]
        self.data_list = ["0.0E0", "0.0E0"]

        self.read_thread = threading.Thread(target=self.pfiffer_polling, args=(), daemon=True)
        self.read_thread.start()
        self.read_thread_lock = threading.Lock()
        pass

    def pfiffer_polling(self):
        while 1:
            time.sleep(1)
            if self.ser.is_open:
                self.ser.write(b"PRX\r\n")
                time.sleep(0.1)
                self.receive_data()
            else:
                self.com_close()
                self.com_open()
        pass

    def receive_data(self):
        answer = b"0, 0, 0, 0"
        try:
            answer = self.ser.read(64)
            self.pfiffer_state = "Read is OK"
        except:
            self.pfiffer_state = "TimeoutError"
        if answer == b'\x06\r\n':
            self.ser.write(b"\x05")
            time.sleep(0.1)
            self.receive_data()
            pass
        else:
            answer_list = []
            try:
                answer_str = answer.decode()
                answer_str = answer_str[0:len(answer_str) - 2]
                answer_list = answer_str.split(",")
            except UnicodeDecodeError as error:
                print(error)
            if answer_list:
                if len(answer_list[0]) != 0:
                    if answer_list[0] == "\x15":
                        state1 = -1
                        state2 = -1
                    else:
                        try:
                            state1 = int(answer_list[0])
                            state2 = int(answer_list[2])
                            pr1 = float(answer_list[1].strip())
                            self.data_list[0] = "%02E" % pr1
                            pr2 = float(answer_list[3].strip().split("\r")[0])
                            self.data_list[1] = "%02E" % pr1

                        except:
                            state1 = -1
                            state2 = -1
                            pass
                    self.pfiffer1_state = self.state_def(state1)
                    self.pfiffer2_state = self.state_def(state2)
                else:
                    pass
                pass
        pass

    @staticmethod
    def state_def(state):
        if state == -1:
            return "Not acknowledge"
        elif state == 0:
            return "Measurement Data OK"
        elif state == 1:
            return "Underrange"
        elif state == 2:
            return "Overrange"
        elif state == 3:
            return "Sensor error"
        elif state == 4:
            return "Sensor off"
        elif state == 5:
            return "No sensor"
        elif state == 6:
            return "Identification error"
        else:
            return "Unknown"
        pass

    def com_close(self):
        self.ser.close()
        pass

    def com_open(self):
        self.ser.baudrate = self.baudrate
        self.ser.port = self.port
        self.ser.timeout = 0.001
        try:
            self.ser.open()
        except serial.serialutil.SerialException as error:
            print(error)
        pass
