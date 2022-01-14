#!/usr/bin/env python3

from sys import stderr
from struct import pack, unpack
from time import time, sleep
import socket

class tcp_error(Exception): pass

class tcp(object):
    def __init__(self, ip_address = '192.168.10.16', port_num = 24):
        # setting
        self.error_try_count = 10
        self.buff_size       = 4096
        # make socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address, port_num))
        self.sock.settimeout(0.1)
        self.read_buff = b''
        #self.clear()
        return

    def __pull(self, byte):
        error_cnt = 0
        while error_cnt < self.error_try_count:
            if len(self.read_buff) >= byte: break
            error_cnt += 1
            try:
                self.read_buff += self.sock.recv(self.buff_size)
                error_cnt = 0
            except socket.timeout:
                pass
            pass
        if error_cnt >= self.error_try_count:
            raise tcp_error('tcp.__pull: receive error')
        buff = self.read_buff[0:byte]
        self.read_buff = self.read_buff[byte:]
        return buff

    def clear(self):
        try:
            while True: self.__pull(self.buff_size)
        except tcp_error:
            pass
        self.read_buff = b''
        return

    def read(self, byte = 1):
        try:
            buff = self.__pull(byte)
        except tcp_error:
            buff = self.read_buff
            self.read_buff = b''
            pass
        except TypeError:
            buff = self.read_buff
            self.read_buff = b''
            pass
        return buff

    pass



def test1():
    from time import time
    from math import floor
    r = tcp()
    r.clear()
    cnt = 0
    cnt_step  = 1000
    cnt_print = cnt_step
    t_step = 0.5
    t = (floor(time() / t_step) + 1) * t_step
    while True:
        #cnt += len(r.read(cnt_print - cnt))
        cnt += len(r.read(1024))
        if cnt >= cnt_print:
            #print cnt_print
            cnt_print += cnt_step
            pass
        if t < time():
            print(cnt)
            t = (floor(time() / t_step) + 1) * t_step
        pass
    return

def test2(filename):
    r = tcp()
    f = open(filename, 'wb')
    r.clear()
    cnt = 0
    cnt_step   = 1000
    #cnt_finish = 200000
    #cnt_finish = 1000000
    cnt_finish = 20000000
    cnt_print = cnt_step
    empty_count = 0
    while True:
        #cnt += len(r.read(cnt_print - cnt))
        buff = r.read(1024)
        f.write(buff)
        if len(buff):
            empty_count = 0
        else:
            f.flush()
            empty_count += 1
            if empty_count == 10: break  ## 10 sec
            pass
        cnt += len(buff)
        while cnt >= cnt_print:
            print(cnt_print)
            cnt_print += cnt_step
            pass
        if cnt >= cnt_finish: break
        pass
    return



if __name__ == '__main__':
    test2('snap6.tcpdata')
    exit(0)
