#!/usr/bin/env python3
# coding: utf-8
'''Description on the ADC setting.'''

from raw_setting import RawSetting

ADC_SWAP_ADDR = 0x1200_0000
ADS_OFFSET = 0x1000_0000

ADS_

class ADCSetting(RawSetting):
    '''Class to handle ADS4249 chip'''
    def __init__(self, rbcp_inst, verbose=True):
        RawSetting.__init__(self, rbcp_inst, verbose, 'ADC')
        self.flag_write = False
        self.write_mode()

    def _write_reg(self, addr, data):
        self._write(ADS_OFFSET + addr, data)

    def _read_reg(self, addr):
        return self._read(ADS_OFFSET + addr)

    def reset(self):
        self._write_reg(0x00, 0x02)
        self.flag_write = True
        self.channel_swap(False)
        return

    def write_mode(self):
        if self.flag_write:
            return

        self.flag_write = True
        self._write_reg(0x00, 0x00)


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

    @property
    def swapped(self):
        '''Tell whether channel definition is swapped.

        Parameters
        ----------
        swapped : bool
            True if swapped.
        '''
        return self._read(ADC_SWAP_ADDR) == 1

    def channel_swap(self, value=None):
        '''Swap channel A and B.

        Parameters
        ----------
        value : int, optional
            0...normal
            1...inverted
            If not specified, read the current value and then swap.
        '''
        if value is None:
            value = 0 if self.swapped  else 1 # swap
        else:
            value = 1 if value else 0

        assert isinstance(value, int)

        self._write(ADC_SWAP_ADDR, value)


    def set_digital(self, on_off):
        '''Turn on/off digital function.

        Parameters
        ----------
        on_off : bool
            True to turn on the digital function.
        '''
        self._reg_ch_bit()
        if on_off:
            self.reg_ch_bit_up(0x42, 3)
        else:
            self.reg_ch_bit_down(0x42, 3)




    def digital_on(self):
        

    def degital_off(self): 




