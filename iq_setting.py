#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class iq_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'IQ ')
        pass

    def get_iqstatus(self):
        addr = 0x50000000
        return self._read(addr)

    def iq_on(self, on_off = True):
        addr = 0x50000000
        data = 1 if on_off else 0
        self._write(addr, data)
        return

    def iq_off(self): return self.iq_on(on_off = False)

    def time_reset(self):
        addr = 0x50000001
        self._write(addr, 1)
        return

    def get_fifo_fatal_error(self):
        addr = 0x50000002
        return self._read(addr)

    def clear_fifo_fatal_error(self):
        addr = 0x50000002
        self._write(addr, 0)
        return

    def set_read_width(self, ch_width):
        addr = 0x50000010
        self._write(addr, ch_width)
        return

    def get_read_width(self):
        addr = 0x50000010
        return self._read(addr)

    pass
