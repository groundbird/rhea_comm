#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting

class trg_setting(raw_setting):
    def __init__(self, rbcp_ins, MAX_CH = 2, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'TRG')
        self.MAX_CH = MAX_CH
        pass

    def init(self):
        for i in range(self.MAX_CH):
            self.set_threshold(i, [0, 0], [0, 0],
                               trg_reset = False, set_en = False)
            self.set_disable(i, trg_reset = False)
            pass
        self.set_trig_pos(100, trg_reset = False)
        self.set_thre_count(1, trg_reset = True)
        return

    def reset(self):
        self._write(0x70000000, 0)
        return

    def start(self):
        self._write(0x70000000, 1)
        return

    def state(self):
        return self._read(0x70000000)

    def set_trig_pos(self, head_length = 100, trg_reset = True):
        if type(head_length) is not int:
            print('set_trig_pos: head_length should be int.')
            return
        if head_length > 1000 or head_length < 0:
            print('set_trig_pos: head_length is 0 -- 1000')
            return
        self._write2(0x70000010, head_length & 0xffff)
        if trg_reset: self.reset()
        return

    def get_trig_pos(self):
        return self._read2(0x70000010)

    def set_enable(self, channel, enable = True, trg_reset = True):
        if not channel in range(self.MAX_CH):
            print(f'set_enable: ch = {channel:d}')
            return
        enable = 1 if enable else 0
        addr  = 0x71000000
        addr += (channel << 8)
        self._write(addr, enable)
        if trg_reset: self.reset()
        return

    def set_disable(self, channel, trg_reset = True):
        self.set_enable(channel, enable = False, trg_reset = trg_reset)
        return

    def get_enable(self, channel):
        if not channel in range(self.MAX_CH):
            print(f'get_enable: ch = {channel:d}')
            return
        addr  = 0x71000000
        addr += (channel << 8)
        return self._read(addr) == 1

    def set_threshold(self, channel, i_val_range, q_val_range,
                      trg_reset = True, set_en = True):
        if not channel in range(self.MAX_CH):
            print(f'set_threshold: ch = {channel:d}')
            return
        val_range = [i_val_range[0],
                     q_val_range[0],
                     i_val_range[1],
                     q_val_range[1]]
        if len(val_range) != 4:
            print('set_threshold: i/q_val_range should be [min, max]')
            return
        for i, v in enumerate(val_range):
            if type(v) is not int:
                print('set_threshold: min/max_val should be int.')
                return
            if v < -(1<<55) or v >= (1<<55):
                print('set_threshold: min/max_val should be 56-bit-int.')
                return
            v_u = int((v >> 32) & 0x00ffffff)
            v_d = int((v >>  0) & 0xffffffff)
            addr  = 0x71000000
            addr += (channel << 8)
            addr += ((i+1) << 4)
            self._write4(addr + 0, v_u)
            self._write4(addr + 4, v_d)
            pass
        if set_en:    self.set_enable(channel, trg_reset = False)
        if trg_reset: self.reset()
        return

    def get_threshold(self, channel):
        if not channel in range(self.MAX_CH):
            print(f'set_threshold: ch = {channel:d}')
            return
        ret = []
        for i in range(4):
            addr  = 0x71000000
            addr += (channel << 8)
            addr += ((i+1) << 4)
            v_u = self._read4(addr + 0)
            v_d = self._read4(addr + 4)
            ret += [(v_u << 32) + v_d]
            pass
        return [ret[0:2], ret[2:4]]

    def set_thre_count(self, count, trg_reset = True):
        if type(count) is not int:
            print('set_thre_count: count should be int.')
            return
        if count > 1000 or count < 0:
            print('set_thre_count: count should be 0 -- 1000')
            return
        self._write2(0x70000020, count & 0xffff)
        if trg_reset: self.reset()
        return

    def get_thre_count(self):
        return self._read2(0x70000020)

    pass
