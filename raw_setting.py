#!/usr/bin/env python3
# coding: utf-8

from sys    import stderr
from rbcp   import rbcp
from struct import pack, unpack

class raw_setting(object):
    def __init__(self, rbcp_ins, verbose = True, LABEL = 'RAW'):
        self.LABEL = LABEL
        self.r = rbcp_ins
        self.verbose = verbose
        pass

    def _write_n(self, byte, addr, data):
        data_byte = [(data >> (8 * (byte-i-1))) & 0xff for i in range(byte)]
        data_str  = b''
        for d in data_byte: data_str += pack('B', d)
        self.r.write(addr, data_str)
        for i, d in enumerate(data_byte):
            if self.verbose:
                print(f'{self.LABEL}: write 0x{addr+i:08x} <== 0x{d:02x} ({d:3d})')
                pass
            pass
        return

    def _read_n(self, byte, addr):
        data_str  = self.r.read(addr, byte)
        data_byte = [s for s in data_str] # [int]
        data = 0
        for i, d in enumerate(data_byte):
            if self.verbose:
                print(f'{self.LABEL}: read  0x{addr+i:08x} ==> 0x{d:02x} ({d:3d})')
                pass
            data <<= 8
            data += d
            pass
        return data

    def _write(self, addr, data):  self._write_n(1, addr, data)
    def _write2(self, addr, data): self._write_n(2, addr, data)
    def _write4(self, addr, data): self._write_n(4, addr, data)
    def _read(self, addr):  return self._read_n(1, addr)
    def _read2(self, addr): return self._read_n(2, addr)
    def _read4(self, addr): return self._read_n(4, addr)

    def set_verbose(self):   self.verbose = True
    def unset_verbose(self): self.verbose = False

    pass
