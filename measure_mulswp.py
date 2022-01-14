#!/usr/bin/env python3


## constant
from fpga_control  import fpga_control

def two_div(val):
    if val < 2: return 0;
    return len(bin(val-1)) -2

## main
def measure_mulswp(fpga, MAX_CH, dds_f_MHz, width, step, fname, power, amps = None, phases = None, f_off=None):
    from packet_reader import read_packet_in_swp
    from numpy  import arange, floor
    from struct import pack
    from time   import sleep

    if power<0:
        num_list = floor(float(MAX_CH) / float(len(dds_f_MHz))+0.1)
    else:
        num_list = int(power)

    
    if amps is None:
        amps = [1.]*len(dds_f_MHz)
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz')
            pass
    else:
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz, scaled by amp')
            pass

    if amps is not None:
        if power<0:
            amp_multi  = [amp for amp in amps]
            amp_multi *= num_list
        else:
            amp_multi = [amp for amp in amps] * num_list + [0.] * (MAX_CH - len(dds_f_MHz)*num_list)
#        print("INPUT SCALE LIST")
#        print(amp_multi)
        pass


    if phases is None:
        phases = [0.]*len(dds_f_MHz)
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz')
            pass
    else:
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz, changed by phase')
            pass

    if phases is not None:
        if power<0:
            phase_multi = [phase for phase in phases]
            phase_multi *= num_list
        else:
            phase_multi =  [phase for phase in phases] * num_list + [0.] * (MAX_CH - len(dds_f_MHz)*num_list)

#        print("phase list")
#        print(phase_multi)
        pass

## print [freq, amp, phase]
    print('INPUT list of freq, amp, phase')
    for i in range(len(dds_f_MHz)):
        print(f'ch{i:03d}: freq {dds_f_MHz[i]:7.4f}MHz, amp {amps[i]:.4f}, phase {phases[i]:7.4f}rad')



    input_len = 2**two_div(len(dds_f_MHz)+(1 if f_off is not None else 0))
    packet_size = 7 + 7 * input_len * 2
    cnt_finish = 10 * packet_size
    header_list = [0xff, 0xf5]

    print('MULTI-SWEEP MEASUREMENT')
    print(f'SwpPower: {power:d}*{input_len}/{MAX_CH:d}')
    sleep(1)

    fpga.init()
    print(f'Input len: {input_len}')
    fpga.iq.set_read_width(input_len)

    f = open(fname, 'wb')
    fpga.tcp.clear()

    dfs = arange(-width/2, width/2, step)

    try:
        for df in dfs:
            print(f'{df:8.3f} MHz')
            freq_Hzs = [int(floor((freq+df) * 1e6 + 0.5)) for freq in dds_f_MHz]
            if power<0:
                input_freqs = freq_Hzs * num_list
            else:
                input_freqs = freq_Hzs * num_list + [0.] * (MAX_CH - len(dds_f_MHz)*num_list)
#            if f_off is not None:
#                freq_Hzs += [int(floor(f_off* 1e6 +  0.5))]
#            while len(freq_Hzs) != input_len:
#                freq_Hzs.append(int(0.))
            cnt = 0

            while True:
                input_freqs = freq_Hzs * power + [0] * (MAX_CH - power*input_len)
#               print('Power: %d*%d/%d' % (power, len(dds_f_MHz), MAX_CH))
                fpga.dds.set_freqs(input_freqs)
                fpga.dds.set_amps(amp_multi)
                fpga.dds.set_phases(phase_multi)
                fpga.iq.time_reset()
                fpga.iq.iq_on()

                try:
                    while True:
                        time = read_packet_in_swp(fpga.tcp.read(packet_size))
                        if time == 0: break
                        pass
                    break
                except KeyboardInterrupt:
                    print('stop reset timestamp')
                    raise KeyboardInterrupt
                else:
                    fpga.iq.iq_off()
                    fpga.tcp.clear()
                    print('... retry read_packet_in_swp()')
                    continue
                pass

#            freq_packs = [(b'\x00' * 3) if freq >= 0 else (b'\xff' * 3) for freq in freq_Hzs]
#            freq_packs = [freq_packs[i] + pack('>i', freq) for i, freq in enumerate(freq_Hzs)]
            freq_packs = [(b'\x00' * 3) if freq >= 0 else (b'\xff' * 3) for freq in freq_Hzs]
#            print(freq_packs)
            freq_packs = [freq_packs[i] + pack('>i', freq) for i, freq in enumerate(freq_Hzs)]
  
            dummy_packet  = b'\xff'        # header
            dummy_packet += b'\x00' * 5    # time
            for fp in freq_packs:
                dummy_packet += fp * 2     # freq
                pass
            dummy_packet += b'\xee'        # footer
            f.write(dummy_packet)

            while True:
                buff = fpga.tcp.read(min(1024, cnt_finish - cnt))
                f.write(buff)
                if not len(buff): break
                cnt += len(buff)
                if cnt >= cnt_finish: break
                pass





#                buff = fpga.tcp.read(min(1024, cnt_finish - cnt))
#                f.write(buff)
#                if not len(buff): break
#                cnt += len(buff)
#                if cnt >= cnt_finish: break
#                pass

            fpga.iq.iq_off()
            pass
    except KeyboardInterrupt:
        print('stop measurement')
        fpga.iq.iq_off()
    finally:
        f.close()
        fpga.dac.txenable_off()
        print(f'write raw data to {fname}')
        pass

if __name__ == '__main__':
    from os.path import isfile
    from time    import strftime
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('fcenters',
                        type=float,
                        nargs='+',
                        help='list of sweep center frequency_MHz.')

    parser.add_argument('-f', '--fname',
                        type=str,
                        default=None,
                        help='output filename. (default=mulswp_WIDTH_STEP_INPUTFREQ_DATE.rawdata)')

    parser.add_argument('-p', '--power',
                        type=int,
                        default=1,
                        help=f'# of ch used for each comm.(<= max_ch in FPGA). default=1')

    parser.add_argument('-w', '--width',
                        type=float,
                        default=3.0,
                        help=f'frequency width in MHz(frequency range = freq +/- width/2). default=3.0')


    parser.add_argument('-s', '--step',
                        type=float,
                        default=0.001,
                        help=f'frequency step in MHz. default=0.01')

    parser.add_argument('-o', '--offreso_tone',
                        type=float,
                        default=None,
                        help=f'off resonance frequency fixed to same value during sweeping. default=None')

    parser.add_argument('--amplitude',
                        type=float,
                        nargs='+',
                        default=None,
                        help='''list of amplitude scale (0 to 1.0).
                        # of amplitude scale must be same as # of input freqs.''')

    parser.add_argument('--phase',
                        type=float,
                        nargs='+',
                        default=None,
                        help='''list of phase scale[rad].
                        # of phase scale must be same as # of input freqs''')

    parser.add_argument('-ip', '--ip_address',
                        type=str,
                        default='192.168.10.16',
                        help='IP-v4 address of target SiTCP. (default=192.168.10.16)')

    args = parser.parse_args()

    dds_f_MHz = args.fcenters
    fname     = args.fname
    power     = args.power
    width     = args.width
    step      = args.step
    f_off     = args.offreso_tone
    amps      = args.amplitude
    phases    = args.phase
    ip        = args.ip_address

    try:
        fpga = fpga_control(ip_address=ip)
        MAX_CH = fpga.MAX_CH
    
        input_len = 2**two_div(len(dds_f_MHz)+(1 if f_off is not None else 0))
        if power < 1 or power*input_len > MAX_CH:
            raise Exception(f'exceeding max # of channels = {input_len}*{power} > {MAX_CH}')
        if fname == None:
            fname  = 'mulswp'
            fname += f'_{width:+08.3f}MHzWidth'
            fname += f'_{step:+08.3f}MHzStep'
            for f_cen in dds_f_MHz:
                fname += f'_{f_cen:+08.3f}MHz'
            if f_off is not None:
                fname += f'_{f_off:+08.3f}MHzOffTone'
            fname += strftime('_%Y-%m%d-%H%M%S')
            fname += '.rawdata'
        if isfile(fname):
            raise Exception(f'{fname} is existed.')
        if amps is not None and len(amps) != len(dds_f_MHz):
            raise Exception(f'# of input amp must be same as # of input freqs.')
        if phases is not None and len(phases) != len(dds_f_MHz):
            raise Exception(f'# of input phase must be same as # of input freqs.')

    except TimeoutError:
        print('connection to FAGA failed.')
        print(ip, 'is invalid ip address.')
        exit(1)
        pass
    except Exception as e:
        print(e)
        exit(1)
        pass

    while len(dds_f_MHz) & (len(dds_f_MHz)-1):
        dds_f_MHz.append(0.)
        if amps is not None: amps.append(0.)
        if phases is not None: phases.append(0.)
        pass


    measure_mulswp(fpga      = fpga,
                   MAX_CH    = MAX_CH,
                   dds_f_MHz = dds_f_MHz,
                   width     = width,
                   step      = step,
                   fname     = fname,
                   power     = power,
                   amps      = amps,
                   phases    = phases,
                   f_off     = f_off)

#####
    ## get argv
    # from sys     import argv, stderr

    # try:
    #     args = argv[1:]
    #     arg_val = []
    #     fname = None
    #     power = 1
    #     width = 3.0 # MHz
    #     step = 0.01 # MHz
    #     f_off = None
    #     ip_addr = '192.168.10.32'
    #     while args:
    #         if args[0] == '-f':
    #             fname = args[1]
    #             args = args[2:]
    #         elif args[0] == '-p':
    #             power = int(args[1])
    #             args = args[2:]
    #         elif args[0] == '-w':
    #             width = float(args[1])
    #             args = args[2:]
    #         elif args[0] == '-s':
    #             step = float(args[1])
    #             args = args[2:]
    #         elif args[0] == '-o':
    #             f_off = float(args[1])
    #             args = args[2:]
    #         elif args[0] == '-ip':
    #             ip_addr = args[1]
    #             args = args[2:]
    #         else:
    #             arg_val += [args[0]]
    #             args = args[1:]
    #             pass
    #         pass

    #     fpga = fpga_control(ip_address=ip_addr)
    #     MAX_CH = fpga.MAX_CH

    #     input_len = 2**two_div(len(arg_val)+(1 if f_off is not None else 0))

    #     if power < 1 or power*input_len > MAX_CH:
    #         raise Exception(f'exceeding max # of channels = {input_len}*{power} > {MAX_CH}')
    #     f_centers   = [float(f_str) for f_str in arg_val]
    #     if len(f_centers) == 0:
    #         raise Exception('F center should be specified')
    #     if fname == None:
    #         fname  = 'mulswp'
    #         fname += f'_{width:+08.3f}MHzWidth'
    #         fname += f'_{step:+08.3f}MHzStep'
    #         for f_cen in f_centers:
    #             fname += f'_{f_cen:+08.3f}MHz'
    #         if f_off is not None:
    #             fname += f'_{f_off:+08.3f}MHzOffTone'
    #         fname += strftime('_%Y-%m%d-%H%M%S')
    #         fname += '.rawdata'
    #     if isfile(fname):
    #         raise Exception(f'{fname} is existed.')
    # except Exception as e:
    #     print( 'Usage: measure_mulswp.py [(float)freq0_MHz] [(float)freq1_MHz] ...', file=stderr)
    #     print( '       option: -f [(str)filename] (default: swp_WIDTH_STEP_INPUTFREQ_DATE.rawdata)', file=stderr)
    #     print( '                  >> output filename', file=stderr)
    #     print(f'             : -p [(int)num] (default: {power})', file=stderr)
    #     print(f'                  >> amplitude (<={MAX_CH})', file=stderr)
    #     print(f'             : -w [(float)width] (default: {width} MHz)', file=stderr)
    #     print(f'                  >> frequency width (frequency range = freq +/- width/2)', file=stderr)
    #     print(f'             : -s [(float)step] (default: {step} MHz)', file=stderr)
    #     print(f'                  >> frequency step', file=stderr)
    #     print(f'             : -o [(float)off-resonance tone] (default: None)', file=stderr)
    #     print(f'                  >> off resonance frequency fixed to same value during sweeping', file=stderr)
    #     print(e)
    #     exit(1)

    # measure_mulswp(fpga, MAX_CH, f_centers, width, step, fname, power, f_off=f_off)

