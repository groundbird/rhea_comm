#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class ds_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'DS ')
        pass

    def set_rate(self, rate_num):
        ## DS_RATE_MIN(10) <= rate_num <= DS_RATE_MAX(200000)
        addr = 0x61000000
        data = rate_num
        self._write4(addr, data)
        return

    def get_rate(self):
        addr = 0x61000000
        data = self._read4(addr)
        return data

    pass
