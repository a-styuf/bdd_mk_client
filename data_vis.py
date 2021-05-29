# encoding: utf-8
# module data_vis
"""
    This module provides general way to data visualisation through special interface.
    Additional window are used.

    Data to visualisation transmit to this one in list form:
    vis_data_list =  [
                        ["Время_0, с", data_list],
                        ["Данные_1, ЕИ", data_list],
                        ....
                        ["Данные_N, ЕИ", data_list]
                    ]
"""
# ext imports
import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import copy
import threading
import time
# my imports
import data_vis_unit, data_vis_widget


# classes
class Unit(QtWidgets.QWidget, data_vis_unit.Ui_dataVisUnitOName):
    """
        Single graph with table
    """
    mouse_clicked_signal = QtCore.pyqtSignal(str)
    x_manual_range_signal = QtCore.pyqtSignal(list)
    x_auto_range_signal = QtCore.pyqtSignal()

    def __init__(self, parent, name):
        # unit-GUI initialization
        super().__init__(parent)
        self.setupUi(self)
        # general variables
        self.debug = True
        self.redraw_flag = False
        self.name = ""
        self.set_name(name)
        self.data_list = [
            ["Time, s", [0, 1, 2]],
            ["Example 1, SmTh", [2, 3, 0]],
            ["Example 2, SmTh", [2, 3, 1]]
            ]
        #
        self.copy_data_lock = threading.Lock()
        # создание графика с думя осями
        self._check_box_state_list = [[0, 0], [0, 0], [0, 0]]
        #
        self.pi = self.dataGraphGView.getPlotItem()  # для сокращения кода
        self.vb2 = pg.ViewBox()  # создаем ViewBox для отрисовки дополнительной оси и графика для него
        self.plot_data_item_list = []
        #
        self.left_label_style = {'color': self.clr_cd("or"), 'font-size': '10pt'}
        self.right_label_style = {'color': self.clr_cd("sb"), 'font-size': '10pt'}
        self.bottom_label_style = {'color': self.clr_cd("sb"), 'font-size': '10pt'}
        #
        self.init_graph()

    def init_graph(self):
        """
        создание мульти поля графики с несколькими осями
        """
        # work with first plotItem
        self.pi.showAxis('right')  # включаем отображение правой оси
        self.pi.scene().addItem(self.vb2)  # добавляем в сцену первого PloItem второй ViewBox
        self.pi.getAxis('right').linkToView(self.vb2)
        self.vb2.setXLink(self.pi)
        #
        self.pi.getAxis('left').setStyle(tickLength=10, tickTextWidth=10)
        self.pi.getAxis('right').setStyle(tickLength=10, tickTextWidth=10)
        self.pi.getAxis('bottom').setStyle(tickLength=10, tickTextWidth=10)
        self.pi.getAxis('left').setLabel('LY', **self.left_label_style)
        self.pi.getAxis('right').setLabel('RY', **self.right_label_style)
        self.pi.getAxis('bottom').setLabel('Time', value="s", **self.bottom_label_style)
        #
        self.pi.getAxis('left').setGrid(128)
        self.pi.getAxis('right').setGrid(64)
        self.pi.getAxis('bottom').setGrid(192)
        #
        self.pi.addLegend()
        #
        self.vb2.setBackgroundColor(self.clr_cd("chcl"))
        #
        self._update_views()
        #
        self.pi.vb.sigResized.connect(self._update_views)
        self.vb2.sigRangeChangedManually.connect(self._rise_auto_button)
        self.pi.vb.sigRangeChangedManually.connect(self._x_range_signal_emit)
        self.pi.autoBtn.clicked.connect(self._auto_button_signal)

    def _update_views(self):
        self.vb2.setGeometry(self.pi.vb.sceneBoundingRect())
        self.vb2.linkedViewChanged(self.pi.vb, self.vb2.XAxis)
        pass

    def _rise_auto_button(self):
        self.pi.vb.disableAutoRange()
        self.pi.showButtons()

    def _auto_button_signal(self):
        self.vb2.enableAutoRange()
        self.x_auto_range_signal.emit()

    def _x_range_signal_emit(self):
        # print(self.pi.vb.viewRange()[0])
        self.x_manual_range_signal.emit(self.vb2.viewRange()[0])

    def set_data(self, data_list):
        # create data
        if data_list is not None:
            with self.copy_data_lock:
                self.data_list = copy.deepcopy(data_list)
                self.redraw_flag = True

    def graph_plot(self):
        if self.redraw_flag:
            self.redraw_flag = False
            try:
                if self.plot_data_item_list:
                    self.plot_data_item_list = self.plot_data_item_list[:len(self.data_list)]
            except IndexError as error:
                return
            #
            try:
                for num, state in enumerate(self._check_box_state_list):
                    if self.data_list:
                        data_x = self.data_list[0][1]
                        data_y = self.data_list[num][1]
                        data_label = self.data_list[num][0]
                        #
                        if len(self.plot_data_item_list) < num+1:
                            self.plot_data_item_list.append([None, None])
                        #
                        if state[0]:
                            if self.plot_data_item_list[num][0] is None:
                                self.plot_data_item_list[num][0] = self.plot_item_from_num(data_x, data_y, data_label, 2*num+0)
                                self.pi.vb.addItem(self.plot_data_item_list[num][0])
                            else:
                                self.plot_data_item_list[num][0].setData(data_x, data_y)
                        else:
                            if self.plot_data_item_list[num][0]:
                                self.pi.vb.removeItem(self.plot_data_item_list[num][0])
                                self._rmv_legend_item_by_item(self.plot_data_item_list[num][0])
                                self.plot_data_item_list[num][0] = None
                        if state[1]:
                            if self.plot_data_item_list[num][1] is None:
                                self.plot_data_item_list[num][1] = self.plot_item_from_num(data_x, data_y, data_label,
                                                                                                2 * num + 1)
                                self.vb2.addItem(self.plot_data_item_list[num][1])
                            else:
                                self.plot_data_item_list[num][1].setData(data_x, data_y)
                        else:
                            if self.plot_data_item_list[num][1]:
                                self.vb2.removeItem(self.plot_data_item_list[num][1])
                                self._rmv_legend_item_by_item(self.plot_data_item_list[num][1])
                                self.plot_data_item_list[num][1] = None
                    pass
            except Exception as error:
                self._print(error)
            pass
        pass

    def set_ch_box_st_list(self, ch_b_st_list):
        self._check_box_state_list = copy.deepcopy(ch_b_st_list)

    def get_ch_box_st_list(self):
        ret_list = copy.deepcopy(self._check_box_state_list)
        return ret_list

    def _rmv_legend_item_by_item(self, item):
        """
        patch for difference between code in LegendItem.py and description on http://www.pyqtgraph.org/documentation/_modules/pyqtgraph/graphicsItems/LegendItem.html#LegendItem.removeItem
        :param item: PlotDataItem to remove
        """
        if self.pi.legend.items:
            for sample, label in self.pi.legend.items:
                if sample.item is item:
                    self.pi.legend.removeItem(label.text)

    @staticmethod
    def need_to_redraw(vis_data):
        """
        :return: True, if we need to redraw graphics
        """
        return True

    @staticmethod
    def clr_cd(color):
        """
        return color code in format #000000 from short name
        :param color: short name for RGB-color code
        :return: string with colorcode in format "#XXXXXX"
        """
        if color is None:
            raise ValueError("Parameter is absent")
        elif color == "r" or color == "red": return "#FF000D"
        elif color == "or" or color == "OrangeRed": return "#FF4500"
        elif color == "b" or color == "blue": return "#0000FF"
        elif color == "sb" or color == "SteelBlue": return "#4682B8"
        elif color == "g" or color == "green": return "#63B365"
        elif color == "c" or color == "cyan": return "#00FFFF"
        elif color == "m" or color == "magenta": return "#C20078"
        elif color == "y" or color == "yellow": return "#FFFF14"
        elif color == "k" or color == "black": return "#000000"
        elif color == "dn" or color == "DarkNavy": return "#000435"
        elif color == "chcl" or color == "charcoal": return "#343837"
        elif color == "wh" or color == "white": return "#FFFFFF"
        elif color == "gr" or color == "gray": return "#808080"
        elif color == "dgr" or color == "DarkGray": return "#2C3539"
        elif color == "sgr" or color == "StateGray": return "#708090"
        else:
            raise ValueError("Unknown Parameter")

    def plot_item_from_num(self, data_x, data_y, name, line_style_val):
        """
        return PlotCurveItem for insert in pyqtgraph.ViewBox with line_styli depending on "line_style_val"
        :param data_x
        :param data_y
        :param line_style_val: parameter for line style
        :return: pyqtgraph.PlotDataItem
        """
        plot_curve_item = pg.PlotDataItem(data_x, data_y)
        self.pi.legend.addItem(plot_curve_item, name)
        pen_color_list = ["or", "sb", "g", "c", "m", "y", "wh", "sgr"]
        pen_style_list = [QtCore.Qt.SolidLine,
                          QtCore.Qt.DashLine,
                          QtCore.Qt.DashDotLine,
                          QtCore.Qt.DashDotDotLine,
                          QtCore.Qt.DotLine,
                          QtCore.Qt.DashDotDotLine]
        pen_width = 2
        try:
            color = self.clr_cd(pen_color_list[line_style_val % len(pen_color_list)])
            style = pen_style_list[(line_style_val // len(pen_color_list)) % len(pen_style_list)]
            self._print("plot_item_from_num: ", color, style)
            plot_curve_item.setPen({"color": color, "style": style, "width": pen_width})
        except IndexError as error:
            plot_curve_item.setPen({"color": self.clr_cd("wh"), "style": QtCore.Qt.SolidLine, "width": pen_width})
            self._print("plot_item_from_num error: ", error)
        return plot_curve_item

    def set_name(self, name):
        try:
            self.name = str(name)
        except Exception as error:
            self._print("set name error: ", error)

    def select(self):
        self.vb2.setBackgroundColor(self.clr_cd("dgr"))
        pass

    def deselect(self):
        self.vb2.setBackgroundColor(self.clr_cd("chcl"))
        pass

    def mousePressEvent(self, event):
        # print(event.x(), event.y())
        self.mouse_clicked_signal.emit(self.name)
        pass

    def _print(self, *args):
        if self.debug:
            print_str = "dvu: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + " " + ("%.3f:" % time.perf_counter())


class Units(QtWidgets.QVBoxLayout):
    active_unit_mpr_signal = QtCore.pyqtSignal()  # active unit was pressed by mouse

    def __init__(self, parent):
        super().__init__(parent)
        self.debug = True
        self.parent = parent
        self.unit_list = []
        self._active_unit = None
        pass

    def add_unit(self):
        unit_to_add = Unit(self.parent, len(self.unit_list))
        self.unit_list.append(unit_to_add)
        self.addWidget(unit_to_add)
        for unit in self.unit_list:
            unit.deselect()
        self._active_unit = unit_to_add
        self._active_unit.select()
        unit_to_add.mouse_clicked_signal.connect(self._mouse_pres_multi_action)
        unit_to_add.x_manual_range_signal.connect(self._x_range_change)
        unit_to_add.x_auto_range_signal.connect(self._x_autorange_set)
        pass

    def delete_unit(self):
        try:
            if len(self.unit_list) > 1:
                try:
                    unit_to_dlt = self.unit_list.pop(-1)
                    try:
                        if unit_to_dlt == self._active_unit:
                            self._active_unit = self.unit_list[-1]
                            self._active_unit.select()
                    except IndexError as error:
                        self._print(error)
                        self._active_unit = None
                    #
                    unit_to_dlt.deleteLater()
                except IndexError as error:
                    self._print(error)
                    self._active_unit = None
            else:
                pass
            self.update()
            pass
        except Exception as error:
            self._print("dlt_unit: ", error)

    def delete_all_units(self):
        for unit in self.unit_list:
            if len(self.unit_list) == 1:
                self._active_unit = unit
                pass
            else:
                self.delete_unit()
        pass

    def redraw(self):
        self.update()
        pass

    def _x_range_change(self, x_range):
        for unit in self.unit_list:
            if unit != self._active_unit:
                unit.pi.vb.setXRange(x_range[0], x_range[1], padding=0.00)

    def _x_autorange_set(self):
        try:
            for unit in self.unit_list:
                if unit != self._active_unit:
                    unit.pi.vb.enableAutoRange(x=True)
        except Exception as error:
            self._print(error)

    def _mouse_pres_multi_action(self):
        try:
            for unit in self.unit_list:
                unit.deselect()
            self._active_unit = self.sender()
            self._active_unit.select()
            self.active_unit_mpr_signal.emit()
        except Exception as error:
            self._print(error)

    def get_active_unit(self):
        return self._active_unit

    def _print(self, *args):
        if self.debug:
            print_str = "dvus: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + " " + ("%.3f:" % time.perf_counter())


class Widget(QtWidgets.QWidget, data_vis_widget.Ui_dataVisWidgetOName):
    restart_graph_signal = QtCore.pyqtSignal()

    def __init__(self):
        # unit-GUI initialization
        super(Widget, self).__init__()
        self.debug = True
        self.setupUi(self)
        # general variables
        self.data_list = [
            ["Time, s", [0, 1, 2]],
            ["Example 1, SmTh", [2, 3, 0]],
            ["Example 2, SmTh", [2, 3, 1]]
        ]
        # test
        self.units = Units(self.gunitQFrame)
        self.setLayout(self.units)
        self.units.active_unit_mpr_signal.connect(self.set_active_unit_ch_box_list)
        self.units.add_unit()
        # table variables
        self.check_box_list = [[QtWidgets.QCheckBox(), QtWidgets.QCheckBox()]]
        self.check_item_changed_lock = 0
        self.table_ch_box_state_list = [[0, 0], [1, 0], [0, 1]]
        self.column_name = ["L", "R", "Name", "Val"]
        self.column_width = [30, 30, 150, 50]
        # pre-init table
        self.table_init()
        self.table_fill()
        self._set_check_button_state()
        # graphics units (gunit)
        self.gunit_list = []
        # работа с кнопками
        self.addUnitPButton.clicked.connect(self.add_unit)
        self.removeUnitPButton.clicked.connect(self.delete_unit)
        self.restartPButton.clicked.connect(self.restart_graph_signal.emit)
        # обновление gui
        self.redraw_period = 500
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.singleShot(1000, self.update_ui)

    # table
    def table_init(self):
        row_count = len(self.data_list)
        column_count = len(self.column_name)
        self.dataTableTWidget.setRowCount(row_count)
        self.dataTableTWidget.setColumnCount(column_count)
        #
        self.dataTableTWidget.setHorizontalHeaderLabels(self.column_name)
        [(self.dataTableTWidget.setColumnWidth(column, self.column_width[column])) for column in range(column_count)]
        #
        self.check_box_list = []
        for row in range(row_count):
            self.check_box_list.append([QtWidgets.QCheckBox(), QtWidgets.QCheckBox()])
            self.dataTableTWidget.setCellWidget(row, 0, self.check_box_list[row][0])
            self.dataTableTWidget.setCellWidget(row, 1, self.check_box_list[row][1])
            self.check_box_list[row][0].stateChanged.connect(self.check_item_changed)
            self.check_box_list[row][1].stateChanged.connect(self.check_item_changed)
        # заполняем имена
        for num, name in enumerate(self.get_data_names()):
            table_item = QtWidgets.QTableWidgetItem(name)
            self.dataTableTWidget.setItem(num, 2, table_item)
        pass

    def table_fill(self):
        if self._is_data_list_change():
            self.table_init()
        # заполняем данные
        for num, data in enumerate(self.get_data_last_val()):
            if num == 0:
                table_item = QtWidgets.QTableWidgetItem("%d" % data[-1])
            else:
                table_item = QtWidgets.QTableWidgetItem("%.4g" % data[-1])
            self.dataTableTWidget.setItem(num, 3, table_item)

    def get_data_names(self):
        name_list = [data[0] for data in self.data_list]
        return name_list

    def get_data_last_val(self):
        data_last_val_list = [data[1] for data in self.data_list]
        return data_last_val_list

    def check_item_changed(self, state):
        try:
            if self.check_item_changed_lock == 0:
                self.units.get_active_unit().set_ch_box_st_list(self._get_check_button_state())
        except AttributeError as error:
            self._print(error)
        pass

    def set_active_unit_ch_box_list(self):
        self.check_item_changed_lock = 1
        self.table_ch_box_state_list = self.units.get_active_unit().get_ch_box_st_list()
        self._set_check_button_state()
        self.check_item_changed_lock = 0
        pass

    def _is_data_list_change(self):  # todo: make another check to see if the list has changed
        if len(self.data_list) != self.dataTableTWidget.rowCount():
            return True
        else:
            return False

    def _get_check_button_state(self):
        row_count = len(self.data_list)
        self.table_ch_box_state_list = []
        for row in range(row_count):
            state = [self.check_box_list[row][0].isChecked(), self.check_box_list[row][1].isChecked()]
            self.table_ch_box_state_list.append(state)
        # print("get", self.table_ch_box_state_list)
        return self.table_ch_box_state_list

    def _set_check_button_state(self):
        for row in range(len(self.table_ch_box_state_list)):
            try:
                self.check_box_list[row][0].setChecked(self.table_ch_box_state_list[row][0])
                self.check_box_list[row][1].setChecked(self.table_ch_box_state_list[row][1])
            except IndexError as error:
                # self._print(error)
                break
        # print("set", self.table_ch_box_state_list)
        pass

    def _clear_state_check(self):
        for row in range(len(self.table_ch_box_state_list)):
            try:
                self.check_box_list[row][0].setChecked(0)
                self.check_box_list[row][1].setChecked(0)
            except IndexError as error:
                # self._print(error)
                break
        # print("set", self.table_ch_box_state_list)
        pass

    def set_graph_data(self, data):
        self.data_list = copy.deepcopy(data)
        self.reset_graph_data()

    def reset_graph_data(self):
        for unit in self.units.unit_list:
            unit.set_data(self.data_list)
        self.table_fill()

    def add_unit(self):
        self.units.add_unit()
        self.reset_graph_data()
        self._clear_state_check()

    def delete_unit(self):
        self.units.delete_unit()
        self.set_active_unit_ch_box_list()
        self.reset_graph_data()

    def update_ui(self):
        # перерисуем графики
        for unit in self.units.unit_list:
            unit.graph_plot()
        # перезапускаем отрисовку
        self.DataUpdateTimer.singleShot(self.redraw_period, self.update_ui)

    def _print(self, *args):
        if self.debug:
            print_str = "dvw: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + " " + ("%.3f:" % time.perf_counter())


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)
    ex = Widget()
    #
    data_list = [["Time, s", [0, 1, 2]]]
    data_list.extend(["Example 1, SmTh", [1, 2, 3+i*0.001]] for i in range(100))
    #
    ex.set_graph_data(data_list)
    ex.show()
    sys.exit(app.exec_())
