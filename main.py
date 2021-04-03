# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QColor
import main_win
import mko_unit
import time
import configparser
import os
import data_vis
import bdd_data
import pfiffer_data


class MainWindow(QtWidgets.QMainWindow, main_win.Ui_main_win):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        #
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('main_icon.png'))
        # второе окно с графиками
        self.graph_window = data_vis.Widget()
        self.graph_window.restart_graph_signal.connect(self.restart_graph)
        self.openGraphPButton.clicked.connect(self.open_graph_window)
        # МКО #
        self.bdd = bdd_data.BddDevice(mko_addr=13)
        # ОАИ ДД #
        self.setParamOAIDD1PushButton.clicked.connect(self.set_settings_oaidd_channeel_1)
        self.setParamOAIDD2PushButton.clicked.connect(self.set_settings_oaidd_channeel_2)
        #
        self.config = None
        self.config_file = None
        self.log_file = None
        self.recreate_log_files()
        # контейнеры для вставки юнитов
        self.gridLayout = QtWidgets.QGridLayout(self.mkoFrame)
        self.ta1_widget = mko_unit.MainWindow(None)
        self.gridLayout.addWidget(self.ta1_widget, 0, 0, 1, 1)
        # # buttons
        #
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.timeout.connect(self.data_update_process)
        self.DataUpdateTimer.start(1000)
        # ## Общие ## #
        self.logsUpdatePButt.clicked.connect(self.recreate_log_files)
        # self.connectPButt.clicked.connect(self.reconnect)
        # self.disconnectPButt.clicked.connect(self.disconnect)

    # общие
    def data_update_process(self):
        self.bdd.get_dd_frame()
        self.fill_table()
        # отправка данных в график
        if self.graph_window.isVisible():
            self.graph_window.set_graph_data(self.bdd.oai_dd_graph_data)
        # сохранение данных в лог
        self.log_file.write(self.bdd.get_log_data(mode="data"))
        pass

    def init_table(self):
        self.dataOAIDD1TableWidget.setColumnCount(2)
        self.dataOAIDD1TableWidget.setRowCount(len(self.bdd.oai_dd_channels[0].name_list))
        self.dataOAIDD2TableWidget.setColumnCount(2)
        self.dataOAIDD2TableWidget.setRowCount(len(self.bdd.oai_dd_channels[1].name_list))
        pass

    def fill_table(self):
        self.init_table()
        # first channel
        for row in range(len(self.bdd.oai_dd_channels[0].name_list)):
            self.__fill_single_socket(self.dataOAIDD1TableWidget, row, 0, self.bdd.oai_dd_channels[0].name_list[row])
            self.__fill_single_socket(self.dataOAIDD1TableWidget, row, 1, self.bdd.oai_dd_channels[0].data_list[row])
        # second channel
        for row in range(len(self.bdd.oai_dd_channels[1].name_list)):
            self.__fill_single_socket(self.dataOAIDD2TableWidget, row, 0, self.bdd.oai_dd_channels[1].name_list[row])
            self.__fill_single_socket(self.dataOAIDD2TableWidget, row, 1, self.bdd.oai_dd_channels[1].data_list[row])

    @staticmethod
    def __fill_single_socket(table, row, column, value, color=None):
        """
        fill the socket of table by value and color
        :param table: the table for filling
        :param row: the table row of item for filling
        :param column: the table column of item for filling
        :param value: value to put in table socket
        :param color: color of table item
        :return: nothing
        """
        if type(value) == str:
            table_item = QtWidgets.QTableWidgetItem(value)
        elif type(value) == float:
            table_item = QtWidgets.QTableWidgetItem("%.3f V" % value)
        else:
            table_item = QtWidgets.QTableWidgetItem("%s" % value)
        table_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if color:
            table_item.setBackground(QtGui.QColor(color))
        table.setItem(row, column, table_item)
        pass

    # graph
    def restart_graph(self):
        self.bdd.oai_dd_channels[0].init_graph_data()
        self.bdd.oai_dd_channels[1].init_graph_data()
        pass

    def open_graph_window(self):
        if self.graph_window.isVisible():
            self.graph_window.close()
        elif self.graph_window.isHidden():
            self.graph_window.show()
        pass

    # OAI_DD #
    def set_settings(self, channel=1):
        #
        if channel == 1:
            if self.buttonGroup.checkedButton().text() == "Отключен":
                mode = 0x00
            elif self.buttonGroup.checkedButton().text() == "R":
                mode = 0x01
            elif self.buttonGroup.checkedButton().text() == "I":
                mode = 0x02
            else:
                raise(ValueError, "Incorrect mode parameter")
            #
            des_res = self.desValueResOAIDD1SpinBox.value()
            des_curr = self.desValueCurrOAIDD1SpinBox.value()
            PID_R = [self.PidCurrOAIDD1SpinBox.value(),
                     self.pIdCurrOAIDD1SpinBox.value(),
                     self.piDCurrOAIDD1SpinBox.value()]
            PID_I = [self.PidCurrOAIDD1SpinBox.value(),
                     self.pIdCurrOAIDD1SpinBox.value(),
                     self.piDCurrOAIDD1SpinBox.value()]
            #
            time_const_R = self.constTimeResOAIDD1SpinBox.value()
            time_const_I = self.constTimeCurrOAIDD1SpinBox.value()
            time_const_U = self.constTimeCurrOAIDD2SpinBox.value()
        elif channel == 2:
            if self.buttonGroup_2.checkedButton().text() == "Отключен":
                mode = 0x00
            elif self.buttonGroup_2.checkedButton().text() == "R":
                mode = 0x01
            elif self.buttonGroup_2.checkedButton().text() == "I":
                mode = 0x02
            else:
                raise(ValueError, "Incorrect mode parameter")
            #
            des_res = self.desValueResOAIDD2SpinBox.value()
            des_curr = self.desValueCurrOAIDD2SpinBox.value()
            PID_R = [self.PidCurrOAIDD2SpinBox.value(),
                     self.pIdCurrOAIDD2SpinBox.value(),
                     self.piDCurrOAIDD2SpinBox.value()]
            PID_I = [self.PidCurrOAIDD2SpinBox.value(),
                     self.pIdCurrOAIDD2SpinBox.value(),
                     self.piDCurrOAIDD2SpinBox.value()]
            #
            time_const_R = self.constTimeResOAIDD2SpinBox.value()
            time_const_I = self.constTimeCurrOAIDD2SpinBox.value()
            time_const_U = self.constTimeCurrOAIDD2SpinBox.value()
        else:
            raise (ValueError, "Incorrect mode parameter")
        ##
        self.bdd.set_oai_dd_mode(channel=channel, mode=mode)
        self.bdd.set_oai_dd_filter(channel=channel, time_const_R=time_const_R, time_const_I=time_const_I, time_const_U=time_const_U)
        self.bdd.set_oai_dd_pid(channel=channel, R_desired=des_res, I_desired=des_curr, PID_R=PID_R, PID_I=PID_I)
        pass

    def set_settings_oaidd_channeel_1(self):
        self.set_settings(channel=1)

    def set_settings_oaidd_channeel_2(self):
        self.set_settings(channel=2)

    # LOGs #
    @staticmethod
    def create_log_file(file=None, prefix="", extension=".csv"):
        dir_name = "Logs"
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d", time.localtime()) + " БДД МК"
        sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                               time.localtime()) + "БДД МК"
        try:
            os.makedirs(sub_sub_dir_name)
        except (OSError, AttributeError) as error:
            pass
        try:
            if file:
                file.close()
        except (OSError, NameError, AttributeError) as error:
            pass
        file_name = sub_sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                            time.localtime()) + prefix + " БДД МК" + extension
        file = open(file_name, 'a', encoding="utf-8")
        return file

    @staticmethod
    def close_log_file(file=None):
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                pass
        pass

    def recreate_log_files(self):
        self.log_file = self.create_log_file(prefix="BDD_data")
        self.log_file.write(self.bdd.get_log_data(mode="title"))
        pass

    def closeEvent(self, event):
        self.close()
        self.close_log_file(file=self.log_file)
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # os.environ["QT_SCALE_FACTOR"] = "1.0"
    #
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
