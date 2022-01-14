#!/usr/bin/env python3

import fcntl

from rbcp          import rbcp
from info_setting  import info_setting
from adc_setting   import adc_setting
from dac_setting   import dac_setting
from dds_setting   import dds_setting
from iq_setting    import iq_setting
from ds_setting    import ds_setting
from snap_setting  import snap_setting
from trg_setting   import trg_setting
from debug_setting import debug_setting
from tcp           import tcp

class fpga_control(object):
    def __init__(self, verbose = False, ip_address='192.168.10.16'):
        verbose = True if verbose else False
        self.__LOCK_PATH = '/tmp/.'+ip_address+'.lock'
        if verbose: print(f'lock file: {self.__LOCK_PATH}')
        ## lock file
        try:
            import os
            if not os.path.isfile(self.__LOCK_PATH):
                self.__lockf = open(self.__LOCK_PATH, 'a')
                self.__lockf.close()
                import stat
                os.chmod(self.__LOCK_PATH, mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH) # chmod 666
                pass
            self.__lockf = open(self.__LOCK_PATH, 'a')
            fcntl.lockf(self.__lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            print(f"{self.__LOCK_PATH} is locked.")
            print(e)
            exit(1)
            pass

        self.rbcp = rbcp(ip_address=ip_address)
        self.tcp  = tcp(ip_address=ip_address)

        self.info = info_setting(self.rbcp, verbose = verbose)
        self.MAX_CH  = self.info.get_max_ch()
        self.EN_SNAP = self.info.get_en_snap()
        self.TRIG_CH = self.info.get_trig_ch()

        self.adc   = adc_setting(self.rbcp, verbose = verbose)
        self.dac   = dac_setting(self.rbcp, verbose = verbose)
        self.dds   = dds_setting(self.rbcp, self.MAX_CH, verbose = verbose)
        self.iq    = iq_setting(self.rbcp, verbose = verbose)
        self.ds    = ds_setting(self.rbcp, verbose = verbose)
        if self.EN_SNAP:
            self.snap  = snap_setting(self.rbcp, verbose = verbose)
            pass
        if self.TRIG_CH > 0:
            self.trg   = trg_setting(self.rbcp, self.TRIG_CH, verbose = verbose)
            pass
        self.debug = debug_setting(self.rbcp, verbose = verbose)

        return

    def init(self):
        print(f'Firmware version: {self.info.get_version():d}')

        self.adc.reset()
        self.dac.reset()

        self.dac.channel_swap()
#        self.adc.channel_swap()
        self.dac.txenable_on()

        self.ds.set_rate(200000)

        self.dds.reset()

        self.iq.set_read_width(0)
        self.iq.iq_off()
        self.iq.time_reset()
        self.iq.clear_fifo_fatal_error()

        if self.EN_SNAP:
            self.snap.snap_off()
            self.snap.time_reset()
            pass

        if self.TRIG_CH > 0:
            self.trg.init()
            pass

        return

    def _adc_test(self): ## for debug
        self.adc.write(0x42, (0<<6) + (0<<4)) # clock timing
        self.adc.degital_on() # test mode
        self.adc.write(0x25, 0x04) # chA: count up
        self.adc.write(0x2b, 0x04) # chB: count up
        #self.adc.write(0x25, 0x03) # chA: 0101 <-> 1010
        #self.adc.write(0x2b, 0x03) # chB: 0101 <-> 1010

    pass

