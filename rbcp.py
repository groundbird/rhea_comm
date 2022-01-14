#!/usr/bin/env python3

from sys import stderr
from struct import pack, unpack
from time import time, sleep
import socket

class rbcp_error(Exception): pass

class rbcp(object):
    def __init__(self, ip_address = '192.168.10.16', port_num = 4660):
        # setting
        self.error_try_count = 10
        self.buff_size       = 4096
        # sitcp parameter
        self.ver_type   = pack('B', 0xff)
        self.cmd_flag_r = pack('B', 0xc0)
        self.cmd_flag_w = pack('B', 0x80)
        self.flag_mask  = 0xf
        self.flag_check = 0x8
        self.packet_id  = int(time()) %  256
        self.read_buff  = b''
        # make socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((ip_address, port_num))
        self.sock.settimeout(0.1)
        #self.clear()
        return

    def __push(self, buff):
        error_cnt = 0
        while error_cnt < self.error_try_count:
            error_cnt += 1
            send_byte = self.sock.send(buff)
            buff = buff[send_byte:]
            if len(buff) == 0: break
            sleep(0.1)
            pass
        if error_cnt >= self.error_try_count:
            raise rbcp_error('rbcp.__push: send error')
        return

    def __pull(self, byte):
        error_cnt = 0
        while error_cnt < self.error_try_count:
            if len(self.read_buff) >= byte: break
            error_cnt += 1
            try:
                self.read_buff += self.sock.recv(self.buff_size)
            except socket.timeout:
                pass
            pass
        if error_cnt >= self.error_try_count:
            raise rbcp_error('rbcp.__pull: receive error')
        buff = self.read_buff[0:byte]
        self.read_buff = self.read_buff[byte:]
        return buff

    def clear(self):
        buff = b''
        error_cnt = 0
        while error_cnt < self.error_try_count:
            try:
                self.sock.recv(self.buff_size)
            except socket.timeout:
                error_cnt += 1
                pass
            pass
        return

    def _send(self, address, data = 1):
        ''' when type(data) == int, output read packet '''
        ## check data
        if type(data) == int:
            len_data = data
            data = b''
        else:
            len_data = len(data)
            pass
        ## make packet
        buff = b''
        ## header
        buff += self.ver_type
        if data == b'':
            buff += self.cmd_flag_r
        else:
            buff += self.cmd_flag_w
            pass
        ## packet ID
        self.packet_id += 1
        self.packet_id %= 256
        buff += pack('B', self.packet_id)
        ## data length
        if len_data > 0xFF:
            raise rbcp_error(f'rbcp._write: data length error: {len_data}')
        buff += pack('B', len_data)
        ## address
        if address > 0xFFFFFFFF or address < 0:
            raise rbcp_error(f'rbcp._write: address error: {address}')
        buff += pack('>I', address)
        ## data
        buff += data
        ## send
        self.__push(buff)
        return

    def _recv(self):
        while True:
            buff = self.__pull(8)
            data_len = unpack('B', buff[3:4])[0]
            buff += self.__pull(data_len)
            #self.__print_packet(buff) # for debug
            ver_type, cmd_flag, packet_id = unpack('BBB', buff[0:3])
            #print(f'ver_type={ver_type}, cmd_flag={cmd_flag}, packet_id={packet_id}')
            if buff[0:1] != self.ver_type:
                raise rbcp_error(f'rbcp._recv: ver_type error: {ver_type}')
            if cmd_flag & self.flag_mask != self.flag_check:
                raise rbcp_error(f'rbcp._recv: cmd_flag error: {cmd_flag}')
            if packet_id == self.packet_id: break
            #print 'ID error' # for debug
            pass
        return buff[8:]

    def __print_packet(self, buff):
        print(f'ver_type: {unpack("B",  buff[0:1])[0]:02x}', file=stderr)
        print(f'cmd_flag: {unpack("B",  buff[1:2])[0]:02x}', file=stderr)
        print(f'packetID: {unpack("B",  buff[2:3])[0]:02x}', file=stderr)
        print(f'data_len: {unpack("B",  buff[3:4])[0]}',     file=stderr)
        print(f'address : {unpack(">I", buff[4:8])[0]:02x}', file=stderr)
        data_no = 0
        for c in buff[8:]:
            print(f'Data{data_no:03d}: {unpack("B",c)[0]:02x}', file=stderr)
            data_no += 1
            pass
        return

    def read(self, address, length = 1):
        #self._send(address, length)
        #return self._recv()
        retry_cnt = 0
        while True:
            try:
                self._send(address, length)
                ret = self._recv()
                break
            except:
                retry_cnt += 1
                if retry_cnt > 30: raise
                print(f"rbcp.write: error! retry: {retry_cnt}", file=stderr)
                sleep(0.1)
                continue
            pass
        return ret

    def write(self, address, data):
#        if type(data) != str:
#            raise rbcp_error(f'rbcp.write: data type error: {type(data)}')
        # self._send(address, str(data))
        # ret = self._recv()
        retry_cnt = 0
        while True:
            try:
                self._send(address, data)
                ret = self._recv()
                break
            except:
                retry_cnt += 1
                if retry_cnt > 30: raise
                print(f"rbcp.write: error! retry: {retry_cnt}", file=stderr)
                sleep(0.1)
                continue
            pass
        return ret

    def read_int1(self, address):
        buff = self.read(address, length = 1)
        return unpack('B', buff)[0]

    def read_int2(self, address):
        buff = self.read(address, length = 2)
        return unpack('>H', buff)[0]

    def read_int4(self, address):
        buff = self.read(address, length = 4)
        return unpack('>I', buff)[0]

    def write_int1(self, address, data):
        return self.write(address, pack('B', data))

    def write_int2(self, address, data):
        return self.write(address, pack('>H', data))

    def write_int4(self, address, data):
        return self.write(address, pack('>I', data))


    pass



def test1():
    r = rbcp()
    r._send(0xFFFFFF00, 4)
    print(unpack('I', r._recv()))
    return

def test2():
    r = rbcp()
    r._send(0xFFFFFF18, 4)
    r._recv()
    print()
    r._send(0xFFFFFF1c, 2)
    r._send(0xFFFFFF1c, 2)
    r._recv()
    print()
    r._send(0xFFFFFF22, 2)
    r._recv()
    return

def test3():
    r = rbcp()
    print(r.read_int4(0xFFFFFF18))
    print(r.read_int1(0xFFFFFF18))
    print(r.read_int1(0xFFFFFF19))
    print(r.read_int1(0xFFFFFF1a))
    print(r.read_int1(0xFFFFFF1b))
    print(r.read_int2(0xFFFFFF1c))
    print(r.read_int2(0xFFFFFF22))
    return

def test4():
    r = rbcp()
    print('MAC address')
    print('%02x' % r.read_int1(0xFFFFFF12))
    print('%02x' % r.read_int1(0xFFFFFF13))
    print('%02x' % r.read_int1(0xFFFFFF14))
    print('%02x' % r.read_int1(0xFFFFFF15))
    print('%02x' % r.read_int1(0xFFFFFF16))
    print('%02x' % r.read_int1(0xFFFFFF17))
    return

def test5():
    r = rbcp()
    print(r.read_int2(0xFFFFFF1C))
    print(r.read_int2(0xFFFFFF1E))
    #r.write_int2(0xFFFFFF1C, 20)
    r.write_int2(0xFFFFFF1C, 24)
    print(r.read_int2(0xFFFFFF1C))
    print(r.read_int2(0xFFFFFF1E))
    return


if __name__ == '__main__':
    #test1()
    #test2()
    #test3()
    #test4()
    test5()
    exit(0)
