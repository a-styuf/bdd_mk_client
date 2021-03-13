
# модуль собирающий в себе стандартизованные функции разбора данных
# Стандарт:
# параметры:
#     frame - в виде листа с данными
# возвращает:
#     table_list - список подсписков (подсписок - ["Имя", "Значение"])

import threading
import crc16

# замок для мультипоточного запроса разбора данных
data_lock = threading.Lock()
mbkap_dev_num = 206


def frame_parcer(frame):
    try:
        with data_lock:
            data = []
            #
            while len(frame) < 3:
                frame.append(0xFEFE)
                pass
            #
            if frame[0] == 0x0FF1 or frame[0] == 0xF10F:  # проверка на метку кадра
                b_order = 'big' if frame[0] == 0xF10F else 'little'
                if 0x4461 == val_from(frame, 2, 2, byteorder=b_order):  # БДД_МК системный кадр
                    #
                    data.append(["Метка кадра", "0x%04X" % val_from(frame, 0*2, 2, byteorder=b_order)])
                    data.append(["Определитель", "0x%04X" % val_from(frame, 1*2, 2, byteorder=b_order)])
                    data.append(["Ввремя, с", "%d" % val_from(frame, 3 * 2, 4, byteorder=b_order)])
                    #
                    data.append(["Давление, мм рт.ст.", "%.2E" % val_from(frame, 4 * 2, 2, byteorder=b_order)])
                    data.append(["Температура, °С", "%.1f" % val_from(frame, 5 * 2, 2, byteorder=b_order, k=1/256)])
                    data.append(["Потребление HV, мА", "%.1f" % val_from(frame, 6 * 2, 2, byteorder=b_order, k=1/256)])
                    data.append(["Давление ДД1, мм", "%.2E" % val_from(frame, 7 * 2, 2, byteorder=b_order)])
                    data.append(["Давление ДД2, мм", "%.2E" % val_from(frame, 8 * 2, 2, byteorder=b_order)])
                    data.append(["Давление ИМД, мм", "%.2E" % val_from(frame, 9 * 2, 2, byteorder=b_order)])
                    data.append(["Температура ДД1, °С", "%.1f" % val_from(frame, 10 * 2, 2, byteorder=b_order, k=1/256)])
                    data.append(["Температура ДД2, °С", "%.1f" % val_from(frame, 11 * 2, 2, byteorder=b_order, k=1/256)])
                    data.append(["Температура ИМД, °С", "%.1f" % val_from(frame, 12 * 2, 2, byteorder=b_order, k=1/256)])
                    data.append(["Режим БДД", "%02X" % val_from(frame, 13 * 2, 1, byteorder=b_order)])
                    data.append(["Состояние БДД", "%02X" % val_from(frame, 13 * 2+1, 1, byteorder=b_order)])
                    data.append(["Флаг ошибок", "%02X" % val_from(frame, 14 * 2, 1, byteorder=b_order)])
                    data.append(["Счетчик ошибок, шт", "%d" % val_from(frame, 14 * 2+1, 1, byteorder=b_order)])
                    #
                    pass
                elif 0x4462 == val_from(frame, 2, 2, byteorder=b_order):  # БДД_МК кадр с подробными данными
                    data.append(["Метка кадра", "0x%04X" % val_from(frame, 0 * 2, 2, byteorder=b_order)])
                    data.append(["Определитель", "0x%04X" % val_from(frame, 1 * 2, 2, byteorder=b_order)])
                    data.append(["Ввремя, с", "%d" % val_from(frame, 3 * 2, 4, byteorder=b_order)])
                    # oai dd 1 and 2
                    rs = 26  # repport size
                    for i in range(2):
                        data.append(["%d: Режим" % (i+1), "0x%02X" % val_from(frame, 2 * 5 + i*rs, 1, byteorder=b_order)])
                        data.append(["%d: Статус" % (i+1), "0x%02X" % val_from(frame, 2 * 5 + 1 + i*rs, 1, byteorder=b_order)])
                        data.append(["%d: P дд, мм рт.ст." % (i+1), "%.2E" % val_from(frame, 2 * 6 + i*rs, 2, byteorder=b_order)])
                        data.append(["%d: T, °C." % (i+1), "%.2f" % val_from(frame, 2 * 7 + i*rs, 2, byteorder=b_order, k=1/256)])
                        data.append(["%d: U ЦАП, В" % (i+1), "%.3f" % val_from(frame, 2 * 8 + i*rs, 2, byteorder=b_order, k=1/256)])
                        data.append(["%d: U дд, В" % (i+1), "%.3f" % val_from(frame, 2 * 9 + i*rs, 2, byteorder=b_order, k=1/256)])
                        data.append(["%d: I дд, мА" % (i+1), "%.3f" % val_from(frame, 2 * 10 + i*rs, 2, byteorder=b_order, k=1/256)])
                        data.append(["%d: R дд, Ом" % (i+1), "%.3f" % val_from(frame, 2 * 11 + i*rs, 2, byteorder=b_order, k=1/256)])
                        data.append(["%d: U_mean, мА" % (i + 1), "%.3f" % val_from(frame, 2 * 12 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                        data.append(["%d: I_mean, мА" % (i + 1), "%.3f" % val_from(frame, 2 * 13 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                        data.append(["%d: R_mean, Ом" % (i + 1), "%.3f" % val_from(frame, 2 * 14 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                        data.append(["%d: U пост.вр., с" % (i + 1), "%.3f" % val_from(frame, 2 * 15 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                        data.append(["%d: I пост.вр., с" % (i + 1), "%.3f" % val_from(frame, 2 * 16 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                        data.append(["%d: R пост.вр., с" % (i + 1), "%.3f" % val_from(frame, 2 * 17 + i * rs, 2, byteorder=b_order, k=1 / 256)])
                    #
                    pass
                else:
                    data.append(["Неизвестный определитель", "0"])
            else:
                data.append(["Данные не распознаны", "0"])
            return data
    except Exception as error:
        print("oai_dd_parcer", error)
        return []


def val_from(frame, offset, length, byteorder="little", signed=False, debug=False, k=None):
    """
    обертка для функции сбора переменной из оффсета и длины, пишется короче и по умолчанию значения самые используемые
    :param frame: лист с данными кадра
    :param offset: оффсет переменной в байтах от начала кадра
    :param length: длина переменной в байтах
    :param byteorder: порядок следования байт в срезе ('little', 'big')
    :param signed: знаковая или не знаковая переменная (True, False)
    :param debug: вывод отладочной информации
    :param k: коэффициент для параметра
    :return: итоговое значение переменной
    """
    # делаем из списка слов список байт
    byte_list = []
    for i in range(len(frame)*2):
        byte_list.append((frame[i//2] >> (8 * (i % 2))) & 0xFF)
    bytes_frame = bytearray(byte_list)
    ret_val = int.from_bytes(bytes_frame[offset + 0:offset + length], byteorder=byteorder, signed=signed)
    if debug:
        print(bytes_frame)
        print(bytes_frame[offset + 0:offset + length],
              " %04X" % int.from_bytes(bytes_frame[offset + 0:offset + length], byteorder=byteorder, signed=signed))
    if k:
        return k*ret_val
    else:
        return int(ret_val)


def frame_definer(modificator=0, dev_num=0, zav_num=0, type=0):
    fr_defer = 0x0000
    if modificator == 0:  # модификатор кадра для больших аппаратур
        fr_defer = ((modificator & 0x3) << 14) + \
                        ((dev_num & 0x03FF) << 4) + \
                        ((type & 0xF) << 0)
        pass
    elif modificator == 1:  # модификатор кадра для малых приборов с большим количеством зав. номеров
        fr_defer = ((modificator & 0x03) << 14) + \
                        ((dev_num & 0x0F) << 10) + \
                        ((zav_num & 0x7F) << 3) + \
                        ((type & 0x07) << 0)
        pass
    return fr_defer


def _int_to_time(sec):
    return [sec//3600, (sec//60) % 60, sec % 60]


def dep_field(data, a=0.1, b=0):
    scale = data >> 15
    mantissa = (data & 0x3FF)
    if (mantissa & 0x200) == 0:
        mantissa = - mantissa
    else:
        mantissa = (((~mantissa) + 1) & 0x3FF)
    degree = (data >> 10) & 0x1F
    sign = (data >> 9) & 1
    field = (mantissa * (2 ** (23 - degree)) * (10 ** (-scale)) / (2 ** 18)) * a + b
    return (-1**sign) * field


def dep_freq(data):
        if data > 127:
            data -= 256
        freq = 5e6 / (33333 + (data * (2 ** 7)))
        return freq

