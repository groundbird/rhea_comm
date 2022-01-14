#!/usr/bin/env python3
# coding: utf-8

from raw_setting import raw_setting
from math import pi

FREQ_MAX = int(200e6)

class dds_setting(raw_setting):
    def __init__(self, rbcp_ins, MAX_CH = 2, verbose = True):
        raw_setting.__init__(self, rbcp_ins, verbose, 'DDS')
        self.MAX_CH = MAX_CH
        pass

    def trig_enable(self):
        self._write(0x40000000, 0x01)
        return

    def unset_periodic_sync(self):
        self._write(0x40000001, 0x00)
        return

    def set_periodic_sync(self):
        self._write(0x40000001, 0x01)
        return

    def get_periodic_sync(self):
        return self._read(0x40000001)

    def set_pinc(self, ch, phase, dds_reset = True):
        if not ch in range(self.MAX_CH):
            print(f'set_pinc error: ch = {ch:d}')
            return
        data  = int(phase)
        data %= (1<<32)
        self._write4(0x41000000 + (ch << 8) + (0 << 4), data)
        if not dds_reset: return
        self.trig_enable()
        return

    def get_pinc(self, ch):
        if not ch in range(self.MAX_CH):
            print(f'get_pinc error: ch = {ch:d}')
            return
        data = self._read4(0x41000000 + (ch << 8) + (0 << 4))
        return data

    def set_poff(self, ch, phase, dds_reset = True):
        if not ch in range(self.MAX_CH):
            print(f'set_pinc error: ch = {ch:d}')
            return
        data  = int(phase)
        data %= (1<<32)
        self._write4(0x41000000 + (ch << 8) + (1 << 4), data)
        if not dds_reset: return
        self.trig_enable()
        return

    def get_poff(self, ch):
        if not ch in range(self.MAX_CH):
            print(f'get_pinc error: ch = {ch:d}')
            return
        data = self._read4(0x41000000 + (ch << 8) + (1 << 4))
        return data

    def set_ampi(self, ch, amp, dds_reset = True):
        if not ch in range(self.MAX_CH):
            print ('set_amp error: ch = %d' % ch)
            return
        data  = int(amp)
        data %= (1<<32)
        self._write4(0x41000000 + (ch << 8) + (2 << 4), data)
        if not dds_reset: return
        self.trig_enable()
        return

    def get_ampi(self, ch):
        if not ch in range(self.MAX_CH):
            print ('get_amp error: ch = %d' % ch)
            return
        data = self._read4(0x41000000 + (ch << 8) + (2 << 4))
        return data

    def set_sync_span(self, span):
        if type(span) != int:
            print('set_sync_span: type(span) != int')
            return
        if span < 0:
            print('set_sync_span: span < 0')
            return
        if span >= (1<<32):
            print('set_sync_span: span >= (1<<32)')
            return
        if span == 0:
            self.unset_periodic_sync()
            return
        self._write4(0x41010000, span)
        self.set_periodic_sync()
        return

    def get_sync_span(self):
        return self._read4(0x41010000)

    def set_freq(self, ch, freq_Hz, dds_reset = True):
        phase = int(float(freq_Hz) / FREQ_MAX * (1<<32))
        self.set_pinc(ch, phase, dds_reset)
        return

    def set_freqs(self, freq_Hz_list):
        if len(freq_Hz_list) != self.MAX_CH:
            print(f'dds_setting.set_freqs: length of freq_Hz_list should be {self.MAX_CH}')
            return
        for i, f in enumerate(freq_Hz_list):
            self.set_freq(i, f, dds_reset = False)
            pass
        self.trig_enable()
        return

    def get_freq(self, ch):
        data = self.get_pinc(ch)
        return data * float(FREQ_MAX) / (1<<32)

    def set_phase(self, ch, phase, dds_reset = True):
        self.set_poff(ch, int(phase / 2 / pi * (1<<32)), dds_reset)
        return

    def get_phase(self, ch):
        data = self.get_poff(ch)
        return data * 2 * pi / (1<<32)

    def set_amp(self, ch, amp, dds_reset = True):
        ampi = int(float(amp) * ((1<<8)-1))
        self.set_ampi(ch, ampi, dds_reset)
        return 

    def get_amp(self, ch):
        data = self.get_ampi(ch)
        return float(data) / ((1<<16)-1)

    def set_amps(self, amp_list):
        if len(amp_list) != self.MAX_CH:
            print ('dds_setting.set_amps: length of amp_list should be', self.MAX_CH)
            return
        for i, a in enumerate(amp_list):
            self.set_amp(i, a, dds_reset = False)
            pass
        self.trig_enable()
        return

    def set_phases(self, phase_list):
        if len(phase_list) != self.MAX_CH:
            print ('dds_setting.set_phases: length of phase_list should be', self.MAX_CH)
            return
        for i, a in enumerate(phase_list):
            self.set_phase(i, a, dds_reset = False)
            pass
        self.trig_enable()
        return

    def reset(self):
        for ch in range(self.MAX_CH):
            self.set_freq(ch, 0.,  False)
            self.set_phase(ch, 0., False)
            pass
        self.set_sync_span(200000) # 1 kHz span
        self.trig_enable()
#        self.unset_periodic_sync()
    pass
