#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class info_setting(raw_setting):
    def __init__(self, rbcp_ins, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'INF')
        pass

    def get_version(self):
        try:
            ret = self._read4(0x00000000)
        except:
            ret = 0
            pass
        return ret

    def get_max_ch(self):
        try:
            ret = self._read(0x00000010)
        except:
            ret = 2
            pass
        return ret

    def get_en_snap(self):
        try:
            ret = (self._read(0x00000011) == 1)
        except:
            ret = True
            pass
        return ret

    def get_trig_ch(self):
        ret = None
        try:
            ret = self._read(0x00000012)
        except:
            if self.get_version() >= 2016091600:
                ret = self.get_max_ch()
            else:
                ret = 0
            pass
        return ret

    pass
