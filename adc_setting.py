#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class adc_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'ADC')
        self.flag_write = False
        self.write_mode()
        pass

    def _write_reg(self, addr, data):
        self._write(0x10000000 + addr, data)
        return

    def _read_reg(self, addr):
        return self._read(0x10000000 + addr)

    def reset(self):
        self._write_reg(0x00, 0x02)
        self.flag_write = True
        self.channel_swap(False)
        return

    def write_mode(self):
        if self.flag_write: return
        self.flag_write = True
        self._write_reg(0x00, 0x00)
        return

    def read_mode(self):
        if not self.flag_write: return
        self.flag_write = False
        self._write_reg(0x00, 0x01)
        return

    def write_reg(self, addr, data):
        self.write_mode()
        self._write_reg(addr, data)
        return

    def read_reg(self, addr):
        self.read_mode()
        data = self._read_reg(addr)
        return data

    def _reg_ch_bit(self, addr, bit_num, val):
        # bit_num: 0-7
        # val: 0-1 or True/False
        val  = 1 if val else 0
        data = self.read_reg(addr)
        bit  = (data >> bit_num) & 0x01
        if bit == val: return
        mask1 = (1 << bit_num)
        mask2 = 0xff ^ mask1
        data = (mask1 * val) + (mask2 & data)
        self.write_reg(addr, data)
        return

    def reg_ch_bit_up(self, addr, bit_num):
        self._reg_ch_bit(addr, bit_num, True)
        return

    def reg_ch_bit_down(self, addr, bit_num):
        self._reg_ch_bit(addr, bit_num, False)
        return

    def channel_swap(self, value = None):
        addr = 0x12000000
        if value == None:
            data = self._read(addr)
            value = 0 if data  else 1 # swap
        else:
            value = 1 if value else 0
            pass
        self._write(addr, value)
        return

    def degital_on(self):  self.reg_ch_bit_up(0x42, 3)
    def degital_off(self): self.reg_ch_bit_down(0x42, 3)

    pass


