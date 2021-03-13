# -*- coding: utf-8 -*-
import ta1_mko
import oai_data_parcer


class OaiDDChannel:
    def __init__(self, channel_num=1):
        self.channel_num = channel_num
        self.name_list = [
            f"Ввремя, с",
            f"{self.channel_num}: Режим",
            f"{self.channel_num}: Статус",
            f"{self.channel_num}: P дд, мм рт.ст.",
            f"{self.channel_num}: T, °C.",
            f"{self.channel_num}: U ЦАП, В",
            f"{self.channel_num}: U дд, В",
            f"{self.channel_num}: I дд, мА",
            f"{self.channel_num}: R дд, Ом",
            f"{self.channel_num}: U_mean, мА",
            f"{self.channel_num}: I_mean, мА",
            f"{self.channel_num}: R_mean, Ом",
            f"{self.channel_num}: U пост.вр., с",
            f"{self.channel_num}: I пост.вр., с",
            f"{self.channel_num}: R пост.вр., с",
        ]
        self.data_list = ["0" for i in range(len(self.name_list))]
        self.graph_data = None
        self.max_graph_len = 10000
        #
        self.row_frame = [0 for i in range(64)]
        pass

    def parcing(self, frame):
        self.row_frame = frame
        parcing_result = oai_data_parcer.frame_parcer(frame=self.row_frame)
        for num, name in enumerate(self.name_list):
            self.data_list[num] = self.find_value(name, parcing_result)
        #
        if self.graph_data is None:
            self.init_graph_data()
        if self.find_value(self.name_list[0], parcing_result) != 0:
            self.create_graph_data()
        pass

    @staticmethod
    def _get_number_from_str(str_var):
        try:
            try:
                number = float(str_var)
            except ValueError:
                number = int(str_var, 16)
            return number
        except Exception as error:
            print(error, str_var)
        return 0

    def create_graph_data(self):
        """
        Creation of data with following format
            vis_data_list = [
                ["Время_0, с", data_list],
                ["Данные_1, ЕИ", data_list],
                ....
                ["Данные_N, ЕИ", data_list]
            ]
        :return: nothing
        """
        for num, pair in enumerate(self.graph_data):
            pair[1].append(self._get_number_from_str(self.data_list[num]))
            while len(pair) >= self.max_graph_len:
                pair[1].pop(0)
        pass

    def init_graph_data(self):
        self.graph_data = [[name, [self._get_number_from_str(self.data_list[i])]]
                           for i, name in enumerate(self.name_list)]

    @staticmethod
    def find_value(name, parcing_result):
        for value_pair in parcing_result:
            if name in value_pair[0]:
                return value_pair[1]
        return "0"


class BddDevice:
    def __init__(self, *args, **kwargs):
        self.state = 0
        #
        self.mko_a = kwargs.get("mko_addr", 13)
        self.ta1 = ta1_mko.Device()
        self.ta1.init()
        #
        self.sys_fr_sa = 15
        self.dd_fr_sa = 1
        self.settings_fr_sa = 30
        #
        if self.ta1 is None:
            self.state = -1
        self.bdd_sys_frame = []
        self.bdd_sys_parsed_data = []
        #
        self.bdd_dd_frame = [0x00 for i in range(32)]
        self.oai_dd_channel = [OaiDDChannel(channel_num=num) for num in range(1, 3)]
        #
        pass

    def get_sys_frame(self):
        self.bdd_sys_frame = self.ta1.read_from_rt(self.mko_a, self.sys_fr_sa, 32)
        self.bdd_sys_parsed_data = oai_data_parcer.frame_parcer(self.bdd_sys_frame)
        pass

    def get_dd_frame(self):
        self.bdd_dd_frame = self.ta1.read_from_rt(self.mko_a, self.dd_fr_sa, 32)
        for oai_dd in self.oai_dd_channel:
            oai_dd.parcing(self.bdd_dd_frame)
        if self.bdd_dd_frame[1] == 0xFEFE:
            self.ta1.disconnect()
            self.ta1.connect()
        pass

    def set_oai_dd_mode(self, channel=1, mode=0x00):
        """
        oai_dd mode setup
        :param channel: number of dd channel (1, 2)
        :param mode: opertaion mode (0-off, 1-resistance, 2-current, 3-automative)
        :return: nothing
        """
        data = [0x0000 for i in range(32)]
        data[0] = 0x0FF1
        if channel == 1:
            data[5] = 0x0001
        elif channel == 2:
            data[5] = 0x0002
        else:
            raise(ValueError, "Incorrect channel number")
        data[6] = mode & 0x000F
        self.ta1.send_to_rt(self.mko_a, self.settings_fr_sa, data, 32)
        pass

    def set_oai_dd_filter(self, channel=1, time_const_R=1.0, time_const_I=1.0, time_const_U=1.0):
        """
        oai_dd filter setting for ouput values
        :param channel: number of dd channel (1, 2)
        :param time_const: filter time constant [s]
        :return: nothing
        """
        data = [0x0000 for i in range(32)]
        data[0] = 0x0FF1
        if channel == 1:
            data[5] = 0x0003
        elif channel == 2:
            data[5] = 0x0004
        else:
            raise(ValueError, "Incorrect channel number")
        data[6] = int(time_const_R * 256) & 0xFFFF
        data[7] = int(time_const_I * 256) & 0xFFFF
        data[8] = int(time_const_U * 256) & 0xFFFF
        self.ta1.send_to_rt(self.mko_a, self.settings_fr_sa, data, 32)
        pass

    def set_oai_dd_pid(self, channel=1, R_desired=75.0, I_desired=20.0, PID_R=None, PID_I=None):
        """
        oai_dd pid settings for resistance and current
        :param channel: number of dd channel (1, 2)
        :param R_desired: desired resistance value [Ohm]
        :param I_desired: desired current value [mA]
        :param PID_R: coefficients for resistance regulation
        :param PID_I: coefficients for resistance regulation
        :return: nothing
        """
        data = [0x0000 for i in range(32)]
        data[0] = 0x0FF1
        if channel == 1:
            data[5] = 0x0005
        elif channel == 2:
            data[5] = 0x0006
        else:
            raise(ValueError, "Incorrect channel number")
        #
        data[6] = int(R_desired * 256)
        data[7] = int(I_desired * 256)
        #
        if PID_R is None:
            PID_R = [1.0, 0.005, 0.0]
        if PID_I is None:
            PID_I = [1.0, 0.005, 0.0]
        for i, var in enumerate(PID_R):
            data[8+i] = int(var * 256) & 0xFFFF
        for i, var in enumerate(PID_I):
            data[11+i] = int(var * 256) & 0xFFFF
        self.ta1.send_to_rt(self.mko_a, self.settings_fr_sa, data, 32)
        pass

    def get_log_data(self, mode="data"):
        ret_str = ""
        for channel in self.oai_dd_channel:
            if mode == "title":
                ret_str += ";".join(channel.name_list)
            elif mode == "data":
                ret_str += ";".join(channel.data_list)
            else:
                raise(ValueError, "Incorrect <mode> parameter")
        return ret_str + "\n"

    def __repr__(self):
        repr_str = ""
        return repr_str


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    bdd = BddDevice(mko_addr=13)
    bdd.get_sys_frame()
    print(bdd.bdd_sys_parsed_data)
    bdd.get_dd_frame()
    print(bdd.oai_dd_channel[0].data_list)
    print(bdd.oai_dd_channel[1].data_list)

