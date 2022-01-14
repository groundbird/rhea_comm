#!/usr/bin/env python3


## constant
from fpga_control  import fpga_control
packet_size = 7 + 7 * 2

## main
def measure_swp(fpga, MAX_CH, f_start, f_end, f_step, fname, power):
    from packet_reader import read_packet_in_swp
    from numpy  import arange, floor
    from struct import pack
    from time   import sleep

    print('SWEEP MEASUREMENT')
    print(f'SwpPower: {power:d}/{MAX_CH:d}')
    sleep(1)

    fpga.init()
    fpga.iq.set_read_width(1)
    cnt_finish = packet_size * 10

    f = open(fname, 'wb')
    fpga.tcp.clear()

    try:
        for freq in arange(f_start, f_end, f_step):
            print(f'{freq:8.3f} MHz')
            freq_Hz = int(floor(freq * 1e6 + 0.5))
            cnt = 0
            
            #sleep(1)
            while True:
                fpga.dds.set_freqs([freq_Hz] * power + [0.] * (MAX_CH - power))
                fpga.dds.set_amps([1]*MAX_CH)
                fpga.iq.time_reset()
                fpga.iq.iq_on()
                
                try:
                    while True:
                        time = read_packet_in_swp(fpga.tcp.read(packet_size))
                        if time == 0: break
                        pass
                    break
                except KeyboardInterrupt:
                    print('stop timestamp reset')
                    raise KeyboardInterrupt
                else:
                    fpga.iq.iq_off()
                    fpga.tcp.clear()
                    print('... retry read_packet_in_swp()')
                    continue
                pass

            freq_pack  = (b'\x00' * 3) if freq_Hz >= 0 else (b'\xff' * 3)
            freq_pack += pack(">i", freq_Hz)
            dummy_packet  = b'\xff'        # header
            dummy_packet += b'\x00' * 5    # time
            dummy_packet += freq_pack * 2  # freq
            dummy_packet += b'\xee'        # footer
            f.write(dummy_packet)

            while True:
                buff = fpga.tcp.read(min(1024, cnt_finish - cnt))
                f.write(buff)
                if not len(buff): break
                cnt += len(buff)
                if cnt >= cnt_finish: break
                pass
        
            fpga.iq.iq_off()
            pass
    except KeyboardInterrupt:
        print('stop measurement')
        fpga.iq.iq_off()
    finally:
        f.close()
        fpga.dac.txenable_off()
        print(f'write raw data to {fname}')

if __name__ == '__main__':
    from os.path import isfile
    from time    import strftime
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('f_start',
                        type=float,
                        help='sweep start frequency_MHz.')

    parser.add_argument('f_end',
                        type=float,
                        help='sweep end frequency_MHz.')

    parser.add_argument('f_step',
                        type=float,
                        help='sweep start frequency_MHz.')

    parser.add_argument('-f', '--fname',
                        type=str,
                        default=None,
                        help='output filename. (default=swp_START_STOP_STEP_DATE.rawdata)')

    parser.add_argument('-p', '--power',
                        type=int,
                        default=1,
                        help=f'# of ch used for each comm.(<= max_ch in FPGA). default=1')

    parser.add_argument('-ip', '--ip_address',
                        type=str,
                        default='192.168.10.16',
                        help='IP-v4 address of target SiTCP. (default=192.168.10.16)')

    args = parser.parse_args()

    f_start     = args.f_start
    f_end       = args.f_end
    f_step      = args.f_step
    fname       = args.fname
    power       = args.power
    ip          = args.ip_address

    try:
        fpga = fpga_control(ip_address=ip)
        MAX_CH = fpga.MAX_CH

        if power < 1 or power > MAX_CH:
            raise Exception(f'Invalid SwpPower: {power:d} / {MAX_CH:d}')
        if fname is None:
            fname  = 'swp'
            fname += f'_{f_start:+08.3f}MHz'
            fname += f'_{f_end:+08.3f}MHz'
            fname += f'_{f_step:+08.3f}MHz'
            fname += strftime('_%Y-%m%d-%H%M%S')
            fname += '.rawdata'
        if isfile(fname):
            raise Exception(f'{fname!r} is existed.')
    except TimeoutError:
        print('connection to FAGA failed.')
        print(ip, 'is invalid ip address.')
        exit(1)
        pass
    except Exception as e:
        print(e)
        exit(1)
        pass

    measure_swp(fpga    = fpga,
                MAX_CH  = MAX_CH,
                f_start = f_start,
                f_end   = f_end,
                f_step  = f_step,
                fname   = fname,
                power   = power)

#####
    ## get argv
    # from sys     import argv, stderr
    # try:
    #     args = argv[1:]
    #     arg_val = []
    #     fname = None
    #     power = 1
    #     ip_addr = '192.168.10.32'
    #     while args:
    #         if args[0] == '-f':
    #             fname = args[1]
    #             args = args[2:]
    #         elif args[0] == '-p':
    #             power = int(args[1])
    #             args = args[2:]
    #         elif args[0] == '-ip':
    #             ip_addr = args[1]
    #             args = args[2:]
    #         elif args[0] == '-h':
    #             print('PRINT HELP::')
    #             raise
    #         else:
    #             arg_val += [args[0]]
    #             args = args[1:]
    #             pass
    #         pass

    #     fpga = fpga_control(ip_address=ip_addr)
    #     MAX_CH = fpga.MAX_CH

    #     if power < 1 or power > MAX_CH:
    #         print(f'Invalid SwpPower: {power:d}/{MAX_CH:d}', file=stderr)
    #         raise
    #     f_start = float(arg_val[0])
    #     f_end   = float(arg_val[1])
    #     f_step  = float(arg_val[2])
    #     if fname is None:
    #         fname  = 'swp'
    #         fname += f'_{f_start:+08.3f}MHz'
    #         fname += f'_{f_end:+08.3f}MHz'
    #         fname += f'_{f_step:+08.3f}MHz'
    #         fname += strftime('_%Y-%m%d-%H%M%S')
    #         fname += '.rawdata'
    #     if isfile(fname):
    #         print(f'{fname!r} is existed.', file=stderr)
    #         raise
    # except Exception as e:
    #     print( 'Usage: measure_swp.py [(float)freq_start_MHz] [(float)freq_end_MHz] [(float)freq_step_MHz]', file=stderr)
    #     print( '       option: -f [(str)filename] (default: swp_START_STOP_STEP_DATE.rawdata)', file=stderr)
    #     print( '                  >> output filename', file=stderr)
    #     print(f'             : -p [(int)num] (default: {power})', file=stderr)
    #     print(f'                  >> amplitude (<={MAX_CH})', file=stderr)
    #     print(e)
    #     exit(1)

    # measure_swp(fpga, MAX_CH, f_start, f_end, f_step, fname, power)
