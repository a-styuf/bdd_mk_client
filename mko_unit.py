import sys
from PyQt5 import QtWidgets, QtCore
import mko_unit_widget
import ta1_mko
import ta1_usb_client_widget
import configparser
import oai_data_parcer
import os


class Widget(QtWidgets.QFrame, mko_unit_widget.Ui_Frame):
    action_signal = QtCore.pyqtSignal([list])

    def __init__(self, parent, **kw):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        # инициаллизация МКО #
        self.num = 0
        self.name = "..."
        for key in sorted(kw):
            if key == "mko":
                self.mko = kw.pop(key)
            elif key == "num":
                self.num = kw.pop(key)
            elif key == "name":
                self.name = kw.pop(key)
            else:
                pass
        #
        self.ta1_mko = ta1_mko.Device()
        self.ta1_mko.init()
        # конфигурация
        self.cfg_dict = {"addr": "1",
                         "subaddr": "1",
                         "length": "32",
                         "data": "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
                         "name": "Test",
                         "type": "write",
                         }
        self.state = 0
        self.action_state = 0
        self.bus_state = 0
        self.addr = 0
        self.subaddr = 0
        self.leng = 0
        self.data = [0, 0]
        self.table_data = [["Нет данных", ""]]
        #
        self.load_cfg()
        #
        self.label.setText("%d" % self.num)
        self.ActionButton.clicked.connect(self.action)

    def set_num(self, n):
        self.num = n
        self.label.setText("%d" % self.num)

    def load_cfg(self, cfg_dict=None):
        if cfg_dict:
            self.cfg_dict = cfg_dict
        self.name = self.cfg_dict.get("name", "NA")
        self.NameLine.setText(self.name)
        self.addr = self.cfg_dict.get("addr", "1")
        self.AddrSpinBox.setValue(int(self.addr))
        self.subaddr = self.cfg_dict.get("subaddr", "1")
        self.SubaddrSpinBox.setValue(int(self.subaddr))
        self.leng = self.cfg_dict.get("length", "1")
        self.LengSpinBox.setValue(int(self.leng))
        data = self.cfg_dict.get("data", "0 0 0 0").split(" ")
        self.data = [int(var, 16) for var in data]
        self.insert_data(self.data)
        if self.cfg_dict.get("type", "read") in "read":
            self.action_state = 0
        elif self.cfg_dict.get("type", "read") in "write":
            self.action_state = 1
        else:
            self.action_state = 2
        if self.action_state == 0:
            self.RWBox.setCurrentText("Чтение")
        elif self.action_state == 1:
            self.RWBox.setCurrentText("Запись")
        else:
            self.RWBox.setCurrentText("КУ")

    def get_cfg(self):
        self.name = self.NameLine.text()
        self.cfg_dict["name"] = self.name
        self.addr = self.AddrSpinBox.value()
        self.cfg_dict["addr"] = "%d" % self.addr
        self.subaddr = self.SubaddrSpinBox.value()
        self.cfg_dict["subaddr"] = "%d" % self.subaddr
        self.leng = self.LengSpinBox.value()
        self.cfg_dict["length"] = "%d" % self.leng
        self.get_data()
        self.cfg_dict["data"] = " ".join(["%04X" % var for var in self.data])
        if self.RWBox.currentText() in "Чтение":
            self.cfg_dict["type"] = "read"
        elif self.RWBox.currentText() in "Запись":
            self.cfg_dict["type"] = "write"
        else:
            self.cfg_dict["type"] = "ctrl"
        return self.cfg_dict

    def write(self):
        self.connect()
        self.ta1_mko.send_to_rt(
                                int(self.AddrSpinBox.value()),
                                int(self.SubaddrSpinBox.value()),
                                self.get_data(),
                                int(self.LengSpinBox.value()))
        self.AWLine.setText("0x{:04X}".format(self.ta1_mko.answer_word))
        self.CWLine.setText("0x{:04X}".format(self.ta1_mko.command_word))
        self.state_check()
        self.ta1_mko.disconnect()
        pass

    def read(self):
        self.connect()
        self.data = self.ta1_mko.read_from_rt(int(self.AddrSpinBox.value()), int(self.SubaddrSpinBox.value()),
                                            int(self.LengSpinBox.value()))
        self.insert_data(self.data)
        self.AWLine.setText("0x{:04X}".format(self.ta1_mko.answer_word))
        self.CWLine.setText("0x{:04X}".format(self.ta1_mko.command_word))
        self.state_check()
        self.ta1_mko.disconnect()
        pass

    def ctrl(self):
        self.connect()
        self.data = self.ta1_mko.send_cntrl_command(int(self.AddrSpinBox.value()), int(self.SubaddrSpinBox.value()),
                                            int(self.LengSpinBox.value()))
        self.insert_data(self.data)
        self.AWLine.setText("0x{:04X}".format(self.ta1_mko.answer_word))
        self.CWLine.setText("0x{:04X}".format(self.ta1_mko.command_word))
        self.state_check()
        self.ta1_mko.disconnect()
        pass

    def action(self):
        if self.RWBox.currentText() in "Чтение":  # read
            self.read()
            self.table_data = oai_data_parcer.frame_parcer(self.data)
        elif self.RWBox.currentText() in "Запись":
            self.write()
            self.table_data = oai_data_parcer.frame_parcer(self.data)
        else:
            self.ctrl()
        pass

    def state_check(self):
        self.state = self.ta1_mko.state
        if self.state == 1:
            self.StatusLabel.setText("TA1-USB")
            self.StatusLabel.setStyleSheet('QLabel {background-color: orangered;}')
        elif self.state == 2:
            self.StatusLabel.setText("Аппаратура")
            self.StatusLabel.setStyleSheet('QLabel {background-color: coral;}')
        elif self.ta1_mko.bus_state == 1:
            self.StatusLabel.setText("Линия 1")
            self.StatusLabel.setStyleSheet('QLabel {background-color: coral;}')
        elif self.ta1_mko.bus_state == 2:
            self.StatusLabel.setText("Линия 2")
            self.StatusLabel.setStyleSheet('QLabel {background-color: coral;}')
        elif self.state == 0:
            self.StatusLabel.setText("Норма")
            self.StatusLabel.setStyleSheet('QLabel {background-color: seagreen;}')
        pass

    def connect(self):
        self.state = self.ta1_mko.init()
        return self.state

    def insert_data(self, data):
        for row in range(self.DataTable.rowCount()):
            for column in range(self.DataTable.columnCount()):
                try:
                    table_item = QtWidgets.QTableWidgetItem("%04X" % data[row*8 + column])
                except (IndexError, TypeError):
                    table_item = QtWidgets.QTableWidgetItem("0000")
                self.DataTable.setItem(row, column, table_item)
        pass

    def get_data(self):
        data = []
        for row in range(self.DataTable.rowCount()):
            for column in range(self.DataTable.columnCount()):
                data.append(int(self.DataTable.item(row, column).text(), 16))
        self.data = data
        return self.data


class Widgets(QtWidgets.QVBoxLayout):
    action = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.list = []
        self.table_data = []
        pass

    def add_unit(self):
        widget_to_add = Widget(self.parent, num=len(self.list))
        self.list.append(widget_to_add)
        self.addWidget(widget_to_add)
        widget_to_add.ActionButton.clicked.connect(self.multi_action)
        pass

    def multi_action(self):
        sender = self.sender().parentWidget()
        self.table_data = sender.table_data
        self.action.emit()

    def delete_unit_by_num(self, n):
        try:
            widget_to_dlt = self.list.pop(n)
            widget_to_dlt.deleteLater()
            # self.unit_layout.removeWidget(widget_to_dlt)
            for i in range(len(self.list)):
                self.list[i].set_num(i)
        except IndexError:
            pass
        self.update()
        pass

    def delete_all_units(self):
        for i in range(self.count()):
            self.itemAt(0).widget().close()
            self.takeAt(0)
        self.list = []
        pass

    def redraw(self):
        self.update()
        pass

    def get_cfg(self, config):
        for i in range(len(self.list)):
            cfg_dict = self.list[i].get_cfg()
            config[str(i)] = cfg_dict
        return config

    def load_cfg(self, config):
        units_cfg = config.sections()
        self.delete_all_units()
        for i in range(len(units_cfg)):
            self.add_unit()
            self.list[-1].load_cfg(config[units_cfg[i]])
        return config


class MainWindow(QtWidgets.QWidget, ta1_usb_client_widget.Ui_Form):
    def __init__(self, parent):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        #
        self.config = None
        self.config_file = None
        # контейнеры для вставки юнитов
        self.units_widgets = Widgets(self.scrollAreaWidgetContents)
        self.units_widgets.action.connect(self.data_table_slot)
        self.setLayout(self.units_widgets)
        # привязка сигналов к кнопкам
        self.AddUnitPButt.clicked.connect(self.units_widgets.add_unit)
        self.DltUnitPButt.clicked.connect(self.dlt_unit)
        self.DltAllUnitsPButt.clicked.connect(self.units_widgets.delete_all_units)
        self.LoadCfgPButt.clicked.connect(self.load_cfg)
        self.SaveCfgPButt.clicked.connect(self.save_cfg)
        #
        self.load_init_cfg()

    def dlt_unit(self):
        n = self.DltUnitNumSBox.value()
        self.units_widgets.delete_unit_by_num(n)
        pass

    def data_table_slot(self):
        # на всякий пожарный сохраняем текущую конфигурацию
        self.save_init_cfg()
        #
        table_data = self.units_widgets.table_data
        self.DataTable.setRowCount(len(table_data))
        for row in range(len(table_data)):
            for column in range(self.DataTable.columnCount()):
                try:
                    table_item = QtWidgets.QTableWidgetItem(table_data[row][column])
                    self.DataTable.setItem(row, column, table_item)
                except IndexError:
                    pass
        pass

    def load_init_cfg(self):
        self.config = configparser.ConfigParser()
        file_name = "init.cfg"
        self.config.read(file_name)
        # print(self.config.sections())
        if self.config.sections():
            self.units_widgets.load_cfg(self.config)
        else:
            self.units_widgets.add_unit()
        pass

    def save_init_cfg(self):
        self.config = configparser.ConfigParser()
        self.config = self.units_widgets.get_cfg(self.config)
        # print(self.config)
        file_name = "init.cfg"
        try:
            with open(file_name, 'w') as configfile:
                self.config.write(configfile)
        except FileNotFoundError:
            pass
        pass

    def load_cfg(self):
        config = configparser.ConfigParser()
        home_dir = os.getcwd()
        try:
            os.mkdir(home_dir + "\\Config")
        except OSError as error:
            print(error)
            pass
        file_name = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Открыть файл конфигурации",
            home_dir + "\\Config",
            r"config(*.cfg);;All Files(*)"
        )[0]
        config.read(file_name)
        self.units_widgets.load_cfg(config)
        pass

    def save_cfg(self):
        home_dir = os.getcwd()
        config = configparser.ConfigParser()
        config = self.units_widgets.get_cfg(config)
        try:
            os.mkdir(home_dir + "\\Config")
        except OSError:
            pass
        file_name = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить файл конфигурации",
            home_dir + "\\Config",
            r"config(*.cfg);;All Files(*)"
        )[0]
        try:
            with open(file_name, 'w') as configfile:
                config.write(configfile)
        except FileNotFoundError:
            pass
        pass

    def closeEvent(self, event):
        self.save_init_cfg()
        self.close()
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow(None)  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
