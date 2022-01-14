#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class dac_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'DAC')
        self.flag_alarm = None
        self.flag_testmode = None
        self.en_4pin(force_reset = True)
        self.testmode_off(force_reset = True)
        pass

    def _write_reg(self, addr, data):
        self._write(0x20000000 + addr, data)
        return

    def _read_reg(self, addr):
        return self._read(0x20000000 + addr)

    def en_4pin(self, force_reset = False):
        if (not force_reset) and (not self.flag_alarm): return
        self.flag_alarm = False
        self._write_reg(0x17, 0x04)
        return

    def en_alarm(self, force_reset = False):
        if (not force_reset) and self.flag_alarm: return
        self.flag_alarm = True
        self._write_reg(0x17, 0x00)
        return

    def write_reg(self, addr, data):
        self._write_reg(addr, data)
        return

    def read_reg(self, addr):
        self.en_4pin()
        return self._read_reg(addr)

    def selfcheck(self):
        for i in range(0x20): self.read_reg(i)
        return

    def reset(self):
        self.write_reg(0x00, 0x70)
        self.write_reg(0x01, 0x01) # no filter
        self.write_reg(0x02, 0x00)
        #self.write_reg(0x03, 0x10)
        self.write_reg(0x03, 0x13) # alarm_2/1away_ena
        #self.write_reg(0x03, 0x03) # alarm_2/1away_ena
        self.write_reg(0x04, 0xff)
        self.write_reg(0x06, 0x00)
        self.write_reg(0x07, 0x00)
        self.write_reg(0x08, 0x00)
        self.write_reg(0x09, 0x00) # test pattern 0
        self.write_reg(0x0a, 0x00)
        self.write_reg(0x0b, 0x00)
        self.write_reg(0x0c, 0x00)
        self.write_reg(0x0d, 0x00)
        self.write_reg(0x0e, 0x00)
        self.write_reg(0x0f, 0x00)
        self.write_reg(0x10, 0x00) # test pattern 7
        self.write_reg(0x11, 0x24)
        self.write_reg(0x12, 0x02)
        self.write_reg(0x13, 0x02) # single_sync_source
        self.write_reg(0x14, 0x00)
        self.write_reg(0x15, 0x00)
        self.write_reg(0x16, 0x00)
        self.write_reg(0x17, 0x00)
        self.write_reg(0x14, 0x00) # again
        self.write_reg(0x18, 0x83)
        self.write_reg(0x19, 0x00)
        self.write_reg(0x1a, 0x00)
        self.write_reg(0x1b, 0x00)
        self.write_reg(0x1c, 0x00)
        self.write_reg(0x1d, 0x00)
        self.write_reg(0x1e, 0x24)
        self.write_reg(0x1b, 0x00) # again
        self.write_reg(0x1f, 0x12)
        self.en_4pin(force_reset = True)
        self.testmode_off(force_reset = True)

        self.txenable_off()
        self.trig_frame()
        self.channel_swap(False)
        self.dac_normal_input()
        return

    def alarm(self, clear = False):
        if clear: self.alarm_clear()
        self.read_reg(0x07)
        return

    def alarm_clear(self):
        self.write_reg(0x07, 0x00)
        return

    def set_fifo_offset(self, offset = 4):
        pt  = self.read_reg(0x03)
        pt &= 0xe3   # "11100011"
        pt += ((offset & 0x07) << 2)
        self.write_reg(0x03, pt)
        return

    def get_fifo_offset(self):
        return ((self.read_reg(0x03) >> 2) & 0x07)

    def testmode_on(self, force_reset = False):
        if (not force_reset) and self.flag_testmode: return
        self.flag_testmode = True
        pt = self.read_reg(0x01) | 0x04
        self.write_reg(0x01, pt)
        return

    def testmode_off(self, force_reset = False):
        if (not force_reset) and (not self.flag_testmode): return
        self.flag_testmode = False
        pt = self.read_reg(0x01) & 0xfb
        self.write_reg(0x01, pt)
        return

    def set_test_pattern(self, adc_a, adc_b):
        self.testmode_on()
        pt0 = (adc_a >> 8) & 0xff
        pt1 =  adc_a       & 0xff
        pt2 = (adc_b >> 8) & 0xff
        pt3 =  adc_b       & 0xff
        self.write_reg(0x09, pt0)
        self.write_reg(0x0a, pt1)
        self.write_reg(0x0b, pt2)
        self.write_reg(0x0c, pt3)
        self.write_reg(0x0d, pt0)
        self.write_reg(0x0e, pt1)
        self.write_reg(0x0f, pt2)
        self.write_reg(0x10, pt3)
        return

    def show_test_result(self, clear = False):
        if clear: self.write_reg(0x08, 0x00)
        for i in range(0x09, 0x11): self.read_reg(i)
        self.read_reg(0x08)
        return

    def txenable_on(self):
        self._write(0x22000000, 1);
        return

    def txenable_off(self):
        self._write(0x22000000, 0);
        return

    def channel_swap(self, value = None):
        if value == None:
            data = self._read(0x22000002)
            value = 0 if data  else 1 # swap
        else:
            value = 1 if value else 0
            pass
        self._write(0x22000002, value)
        return

    def trig_frame(self):
        self._write(0x22000001, 1);
        return

    def dac_dummy_input(self, ch_a, ch_b, chmode_skip = False):
        if not chmode_skip: self._write(0x22000003, 1)
        self._write2(0x23000100, ch_a & 0xffff)
        self._write2(0x23000102, ch_b & 0xffff)
        return

    def dac_normal_input(self):
        self._write(0x22000003, 0)
        return

    pass
