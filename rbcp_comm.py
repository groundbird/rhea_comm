#!/usr/bin/env python3

from sys import stderr
from rbcp import rbcp
from struct import pack, unpack

def conv_int(data):
    if type(data) == int: return data
    if type(data) != str: raise Exception('conv_int: value error: ' + str(type(data)))
    if data[0:2] == '0x': return int(data, 16)
    if data[0]   == '0' : return int(data,  8)
    return int(data)

def command_from_string(rbcp_ins, wds):
    '''
    ['read',  (byte), (address)]
    or
    ['write', (byte), (address), (value)]
    or
    ['exit']
    '''
    if len(wds) == 0: return False
    if wds[0] in ['r', 'read']:
        if len(wds) != 3: raise
        buff = rbcp_ins.read(conv_int(wds[2]), length = conv_int(wds[1]))
        buff_val = [unpack('B', c)[0] for c in buff]
        val = 0
        print()
        print('XX: DEC')
        for b in buff_val:
            val <<= 8
            val += b
            print(f'{b:02x}: {b:3d}')
            pass
        print(f'value ={val}')
        print()
        pass
    elif wds[0] in ['w', 'write']:
        if len(wds) != 4: raise
        data = conv_int(wds[3])
        buff = []
        for i in range(conv_int(wds[1])):
            buff += [pack('B', data & 0xFF)]
            data >>= 8
            pass
        buff.reverse()
        buff_s = b''
        for c in buff: buff_s += c
        rbcp_ins.write(conv_int(wds[2]), buff_s)
        print()
        print('OK')
        print()
        pass
    elif wds[0] in ['exit', 'quit', '.q']:
        return True
    else:
        raise
    return False

def interactive():
    from sys import stdin
    r = rbcp()
    try:
        print('> ', end=' ')
        while True:
            line = stdin.readline()
            if len(line) == 0:
                print()
                break
            wds = line.split()
            if len(wds) == 0:
                print()
                print('> ', end=' ')
                continue
            try:
                ret = command_from_string(r, wds)
                if ret: break
            except:
                #raise
                print()
                print('Usage:')
                print('  read  (byte) (address)')
                print('  write (byte) (address) (value)')
                print('  exit')
                print()
                pass
            print('> ', end=' ')
            pass
        pass
    except Exception as e:
        print(e.args)
    except KeyboardInterrupt:
        pass
    print('EXIT')
    return

def default_func():
    from sys import argv
    try:
        if len(argv) == 1: return interactive()
        return command_from_string(rbcp(), argv[1:])
    except:
        #print e.args
        print(f'Usage: {argv[0]} ([r/w] [byte] [address] ([value]))', file=stderr)
        pass
    return



if __name__ == '__main__':
    default_func()
    exit(0)
