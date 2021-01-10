# -*- coding: utf-8 -*-
import smbus

bus = smbus.SMBus(1)
address_adt7410 = 0x48
register_adt7410 = 0x00
configration_adt7410 = 0x03

# 1６bitに設定して読み出し
bus.write_word_data(address_adt7410, configration_adt7410, 0x80)
word_data = bus.read_word_data(address_adt7410, register_adt7410)

# 2バイトの入れ替え
data = (word_data & 0xff00) >> 8 | (word_data & 0xff) << 8

# 128で割って温度に
print(data/128.)
