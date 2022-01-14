#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class debug_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'DBG')
        pass

    def probe(self, addr):
        return self._read(0xf1000000 + addr)

    def drive(self, addr, data):
        self._write(0xf2000000 + addr, data)
        return

    def drive_read(self, addr):
        return self._read(0xf2000000 + addr)

    pass
