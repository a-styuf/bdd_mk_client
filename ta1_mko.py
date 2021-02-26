from ctypes import *
import os
import time


class Device:
    """
    Device- класс устройства для общения по МКО/МПИ. Необходимо создавать по шаблону:
    метода на запись: send_to_rt(self, adr, subaddr, data, leng), возвращает ответное слово
    метода на чтение: read_from_rt(self, addr, subaddr, leng), возвращает данные с подадреса
    метода на запись команды управления: send_cntrl_command(self, addr, subaddr, leng), возвращает ответное слово

    параметр ответное слово: answer_word
    параметр командное слово: command_word

    параметр имени устройства: name
    параметр состояние устройства: state - 0-устройство подключилось,
                                           1-устройство не подключено,
                                           2-устройство не подключено к МКО ОУ
    параметр состояние устройства: bus_state -  0-неопределено,
                                                1-используется основная шина,
                                                2-используется резервная шина

    Важно, данная библиотека работает с dll, соответственно нельзя менять путь внутри рабочей программы
    """
    def __init__(self):
        self.name = "TA1-USB"
        self.bus_1, self.bus_2 = 0x00, 0x01
        self.bus_state = 0
        #
        self.state = 1
        # constants from API.h-file
        self.ALL_TMKS = 0x00FF

        self.DATA_BC_RT = 0x00
        self.DATA_BC_RT_BRCST = 0x08
        self.DATA_RT_BC = 0x01
        self.DATA_RT_RT = 0x02
        self.DATA_RT_RT_BRCST = 0x0A

        self.CTRL_C_A = 0x03
        self.CTRL_C_BRCST = 0x0B
        self.CTRL_CD_A = 0x04
        self.CTRL_CD_BRCST = 0x0C
        self.CTRL_C_AD = 0x05

        self.BUS_1, self.BUS_2 = 0, 1
        #
        self.bus = self.BUS_1
        self.read_status = 0x0000
        self.answer_word = 0xFFFF
        self.command_word = 0x0000
        #
        self.ta1_lib = windll.LoadLibrary(os.path.abspath(os.path.join(os.path.dirname(__file__), "WDMTMKv2.dll")))

    def init(self):
        #
        self.ta1_lib.TmkOpen.restype = c_uint16
        self.state = self.ta1_lib.TmkOpen()  # функция подключает драйвер к вызвавшему функцию процессу
        #
        self.ta1_lib.tmkdone(self.ALL_TMKS)
        #
        self.ta1_lib.tmkconfig(0)
        #
        self.ta1_lib.bcreset()
        #
        self.ta1_lib.bcgetstate()
        #
        self.ta1_lib.bcdefbase(1)
        #
        self.ta1_lib.bcgetbase()
        #
        self.ta1_lib.bcdefbus.argtypes = [c_ushort]
        self.ta1_lib.bcdefbus(c_ushort(0))
        #
        self.ta1_lib.bcgetbus.restype = c_ushort
        self.ta1_lib.bcgetbus()
        #
        self.ta1_lib.tmkgethwver()
        #
        return self.state

    def connect(self):
        return self.init()

    def disconnect(self):
        self.ta1_lib.TmkClose()
        self.state = 1
        return self.state

    def change_bus(self):
        if self.bus == self.BUS_2:
            self.bus = self.BUS_1
        else:
            self.bus = self.BUS_2
        # print(self.bus)
        self.ta1_lib.bcdefbus(self.bus)

    def send_to_rt(self, addr, subaddr, data, leng):
        self.bus_state = 1 if self.bus == self.BUS_1 else 2
        self.change_bus()
        if subaddr <= 0:
            subaddr = 1
        for i in range(36):
            self.ta1_lib.bcputw(i, 0xFEFE)
        control_word = ((addr & 0x1F) << 11) + (0x00 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        self.ta1_lib.bcdefbus(self.bus)
        self.ta1_lib.bcputw(0, control_word)
        for i in range(leng):
            self.ta1_lib.bcputw(i+1, data[i])
        self.ta1_lib.bcstart(1, self.DATA_BC_RT)
        time.sleep(0.001)
        #
        self.command_word = self.ta1_lib.bcgetw(0)
        self.answer_word = self.ta1_lib.bcgetw(1 + leng)  # self.ta1_lib.bcgetansw(DATA_BC_RT) & 0xFFFF
        # self.print_base()
        #
        if self.answer_word == 0xFEFE:
            self.bus_state = 1 if self.bus == self.BUS_1 else 2
            self.change_bus()
            self.ta1_lib.bcputw(0, control_word)
            self.ta1_lib.bcstart(1, self.DATA_BC_RT)
            time.sleep(0.001)
            self.command_word = self.ta1_lib.bcgetw(0)
            self.answer_word = self.ta1_lib.bcgetw(1+leng)  # self.ta1_lib.bcgetansw(DATA_BC_RT) & 0xFFFF
            # self.print_base()
        if self.answer_word == 0xFEFE:
            self.state = 2
        time.sleep(0.010)
        return self.answer_word

    def send_cntrl_command(self, addr, subaddr, leng):
        self.change_bus()
        control_word = ((addr & 0x1F) << 11) + (0x00 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        self.ta1_lib.bcputw(0, control_word)
        self.ta1_lib.bcstart(1, self.CTRL_C_A)
        self.command_word = self.ta1_lib.bcgetw(0)
        self.answer_word = self.ta1_lib.bcgetansw(self.CTRL_C_A) & 0xFFFF
        if self.answer_word == 0xFEFE:
            self.state = 2
        return self.answer_word

    def read_from_rt(self, addr, subaddr, leng):
        self.change_bus()
        if subaddr <= 0:
            subaddr = 1
        for i in range(36):
            self.ta1_lib.bcputw(i, 0xFEFE)
        control_word = ((addr & 0x1F) << 11) + (0x01 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        self.ta1_lib.bcdefbus(self.bus)
        self.ta1_lib.bcputw(0, control_word)
        self.ta1_lib.bcstart(1, self.DATA_RT_BC)
        #
        self.command_word = self.ta1_lib.bcgetw(0)
        self.answer_word = self.ta1_lib.bcgetansw(self.DATA_RT_BC) & 0xFFFF  # self.ta1_lib.bcgetw(1)
        #
        if self.answer_word == 0xFEFE:
            self.bus_state = 1 if self.bus == self.BUS_1 else 2
            self.change_bus()
            self.ta1_lib.bcputw(0, control_word)
            self.ta1_lib.bcstart(1, self.DATA_RT_BC)
            self.command_word = self.ta1_lib.bcgetw(0)
            self.answer_word = self.ta1_lib.bcgetansw(self.DATA_RT_BC) & 0xFFFF  # self.ta1_lib.bcgetw(1)
        if self.answer_word == 0xFEFE:
            self.state = 2
        frame = []
        for i in range(2, 2+leng):
            word = self.ta1_lib.bcgetw(i)
            frame.append(word)
        return frame

    def print_base(self):
        print_str = ""
        for i in range(35):
            print_str += "%04X " % self.ta1_lib.bcgetw(i)
        print(print_str)
        pass


class PollingProgram:
    """
        класс для разбора подпрограмм для создания циклограмм
        циклограмма согласно данному шаблону
        ["Name", [[Address, Subaddress, Wr/R, [Data], Data leng, Start time, Finish time, Interval, Delay], [...], [...]]]
           |          |          |        |      |         |          |           |          |         |
           |          |          |        |      |         |          |           |          |         -- Задержка отправки
           |          |          |        |      |         |          |           |          --- Интервал отправки
           |          |          |        |      |         |          |           - Время остановки посылок
           |          |          |        |      |         |          --- Время старта отправки от запуска программы
           |          |          |        |      |         --- Длина данных для приема/отправки
           |          |          |        |      ------------- Данные для отправки (при приеме не имеет значения)
           |          |          |        -------------------- Отправка - "0", Прием - "1"
           |          |          ----------------------------- Подадрес
           |          ---------------------------------------- Адрес ОУ
           --------------------------------------------------- Имя циклограммы
    """
    def __init__(self, program=None):
        program_def = ["None", [0, 0, 0, [0], 0, 0, 0, 0.1, 0]]
        self.program = program if program else program_def
        self.name = self.program[0]
        self.cycle = []
        self.parcer()

    def parcer(self):
        for i in range(len(self.program[1])):
            start_time = self.program[1][i][5]
            stop_time = self.program[1][i][6]
            interval = self.program[1][i][7]
            delay = self.program[1][i][8]
            try:
                tr_number = int((stop_time - start_time)//interval)
            except ZeroDivisionError:
                tr_number = 1
            for j in range(tr_number):
                time = start_time + j*interval + delay
                addr = self.program[1][i][0]
                subaddr = self.program[1][i][1]
                direct = self.program[1][i][2]
                data = self.program[1][i][3]
                leng = self.program[1][i][4]
                data_set = [time, addr, subaddr, direct, data, leng]
                # print(data_set)
                self.cycle.append(data_set)
        self.cycle.sort()
        # print(self.cycle)
        pass


if __name__ == '__main__':
    ta1_usb = Device()
    ta1_usb.disconnect()
    state = ta1_usb.init()
    state = ta1_usb.init()
    if state == 1:
        print("Не успешно: state = %d" % state)
    elif state == 0:
        print("Успешно: state = %d" % state)
    # чтение с адреса
    try:
        addr = int(input("Address(13):"))
    except ValueError:
        addr = 13
    try:
        subaddr = int(input("SubAddress(1):"))
    except ValueError:
        subaddr = 1
    frame = ta1_usb.read_from_rt(addr, subaddr, 32)
    frame_str = " ".join(["%04X" % var for var in frame])
    print("aw-%04X, cw-%04X, data-%s" % (ta1_usb.answer_word, ta1_usb.command_word, frame_str))
