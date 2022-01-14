#!/usr/bin/env python3

## config
cnt_step_per_sec    = 1
rate_kSPS_default   = 1 # default: 1 kSPS ~ downsample:200000
data_length_default = rate_kSPS_default * 1000 * 10 # default: 10 sec

## constant
from fpga_control import fpga_control

## tool
def isPowerOf2(value): return value & (value-1)


## main
def measure_tod(fpga, MAX_CH, dds_f_MHz, data_length, rate_kSPS, power, fname, amps=None, phases=None):
    from math import floor
    from struct  import pack

    print('TOD MEASUREMENT')

    if amps is None:
        amps = [1.]*len(dds_f_MHz)
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz')
            pass
    else:
        for i, freq in enumerate(dds_f_MHz):
#            print(f'ch{i:03d}: {freq} MHz, scaled by amp')
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


    fpga.init()
    fpga.iq.set_read_width(len(dds_f_MHz))

    if power<0:
        dds_f_Hz_multi  = [freq * 1e6 for freq in dds_f_MHz]
        dds_f_Hz_multi *= floor(float(MAX_CH) / float(len(dds_f_MHz))+0.1)
#        print('Power: %d*%d/%d' % (len(dds_f_MHz), MAX_CH / len(dds_f_MHz), MAX_CH))
        #print dds_f_Hz_multi
    else:
        dds_f_Hz_multi = [freq * 1e6 for freq in dds_f_MHz] * int(power) + [0.] * (MAX_CH - int(power)*len(dds_f_MHz))
#        print('Power: %d*%d/%d' % (power, len(dds_f_MHz), MAX_CH))
        #print dds_f_Hz_multi

#    print("INPUT FREQ LIST")
#    print(dds_f_Hz_multi)
    fpga.dds.set_freqs(dds_f_Hz_multi)

    if amps is not None:
        if power<0:
            amp_multi  = [amp for amp in amps]
            amp_multi *= floor(float(MAX_CH) / float(len(dds_f_MHz))+0.1)
        else:
            amp_multi = [amp for amp in amps] * int(power) + [0.] * (MAX_CH - int(power)*len(dds_f_MHz))

#        print("INPUT SCALE LIST")
#        print(amp_multi)
        fpga.dds.set_amps(amp_multi)
        pass


    if phases is not None:
        if power<0:
            phase_multi = [phase for phase in phases]
            phase_multi *= floor(float(MAX_CH) / float(len(dds_f_MHz)) + 0.1)
        else:
            phase_multi =  [phase for phase in phases] * int(power) + [0.] * (MAX_CH - int(power)*len(dds_f_MHz))

#        print("phase list")
#        print(phase_multi)
        fpga.dds.set_phases(phase_multi)

## print [freq, amp, phase]
    print('INPUT list of freq, amp, phase')
    for i in range(len(dds_f_MHz)):
        print(f'ch{i:03d}: freq {dds_f_MHz[i]:7.4f}MHz, amp {amps[i]:.4f}, phase {phases[i]:7.4f}rad ')

    fpga.ds.set_rate(floor(200000 / rate_kSPS+0.5))

    f = open(fname, 'wb')

    ## write header
    dummy_packet  = b'\xff'
    dummy_packet += b'\x00' + pack('>I', rate_kSPS * 1000)
    for freq in dds_f_MHz:
        freq_Hz = int(floor(freq * 1e6 + 0.5))
        freq_packet = (b'\x00' * 3) if freq_Hz >= 0 else (b'\xff' * 3)
        freq_packet += pack('>i', freq_Hz)
        dummy_packet += freq_packet * 2
        pass
    dummy_packet += b'\xee'
    f.write(dummy_packet)

    cnt = 0
    packet_size = 7 + 7 * 2 * len(dds_f_MHz)
    cnt_finish = packet_size * data_length
    cnt_step = packet_size * rate_kSPS * 1000 * cnt_step_per_sec
    cnt_print = cnt_step

    fpga.tcp.clear()
    fpga.iq.iq_on()

    try:
        while True:
            buff = fpga.tcp.read(min(1024, cnt_finish - cnt))
            f.write(buff)
            if not len(buff): break
            cnt += len(buff)
            while cnt >= cnt_print:
                print(cnt_print / packet_size)
                cnt_print += cnt_step
                pass
            if cnt >= cnt_finish: break
            pass
    except KeyboardInterrupt:
        print('stop measurement')
    finally:
        f.close()
        fpga.iq.iq_off()
        fpga.dac.txenable_off()
        print(f'write raw data to {fname}')


if __name__ == '__main__':
    from time    import strftime
    from os.path import isfile
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('freqs',
                        type=float,
                        nargs='+',
                        help='list of target frequency_MHz.')

    parser.add_argument('-f', '--fname',
                        type=str,
                        default=None,
                        help='output filename. (default=tod_INPUTFREQ_RATE_DATE.rawdata)')

    parser.add_argument('-l', '--length',
                        type=int,
                        default=data_length_default,
                        help=f'data length. (default={data_length_default})')

    parser.add_argument('-r', '--rate',
                        type=int,
                        default=rate_kSPS_default,
                        help=f'sample rate of measurement (kSPS). (default={rate_kSPS_default}kSPS)')

    parser.add_argument('-p', '--power',
                        type=int,
                        default=1,
                        help=f'# of ch used for each comm.(<= max_ch in FPGA). default=1')

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

    freqs       = args.freqs
    fname       = args.fname
    data_length = args.length
    rate_kSPS   = args.rate
    power       = args.power
    amps        = args.amplitude
    phases      = args.phase
    ip          = args.ip_address

    try:
        fpga = fpga_control(ip_address=ip)
        MAX_CH = fpga.MAX_CH

        if len(freqs) > MAX_CH:
            raise Exception(f'too many frequencies! = {len(freqs)} / {MAX_CH}')
        if power>0 and len(freqs)*power > MAX_CH:
            raise Exception(f'exceeding max # of channels = {len(freqs)}*{power} > {MAX_CH}')

        def two_div(val):
            if val < 2: return 0;
            return len(bin(val-1)) -2

        input_len = 2**two_div(len(freqs))
        if power >0 and power*input_len > MAX_CH:
            raise Exception(f'exceeding max # of channels = {input_len}*{power} > {MAX_CH}')
        if 200000 % rate_kSPS != 0:
            raise Exception(f'sampling rate [kSPS] should be a divisor of 2000000: input rate = {rate_kSPS} kSPS')
        dds_f_MHz = [float(v) for v in freqs]
        if fname is None:
            fname  = 'tod'
            for f in dds_f_MHz: fname += f'_{f:+08.3f}MHz'
            fname += f'_{rate_kSPS:04d}kSPS'
            fname += strftime('_%Y-%m%d-%H%M%S')
            fname += '.rawdata'
        if isfile(fname):
            raise Exception(f'{fname} is existed.')
        if amps is not None and len(amps) != len(freqs):
            raise Exception(f'# of input amp must be same as # of input freqs.')
        if phases is not None and len(phases) != len(freqs):
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

    measure_tod(fpga        = fpga,
                MAX_CH      = MAX_CH,
                dds_f_MHz   = dds_f_MHz,
                data_length = data_length,
                rate_kSPS   = rate_kSPS,
                power       = power,
                fname       = fname,
                amps        = amps,
                phases       = phases)

#######
    # from sys     import argv, stderr

    # try:
    #     args        = argv[1:]
    #     arg_val     = []
    #     fname       = None
    #     data_length = data_length_default
    #     rate_kSPS   = rate_kSPS_default
    #     power       = -1
    #     amps_val    = None
    #     nch         = 0
    #     ip_addr     = '192.168.10.32'
    #     while args:
    #         if args[0] == '-f':
    #             fname = args[1]
    #             args = args[2:]
    #         elif args[0] == '-l':
    #             data_length = int(args[1])
    #             args = args[2:]
    #         elif args[0] == '-r':
    #             rate_kSPS = int(args[1])
    #             args = args[2:]
    #         elif args[0] == '-p':
    #             power = int(args[1])
    #             args = args[2:]
    #         elif args[0] == '-a':
    #             print(f'AMPLITUDE SCALING IS ENABLED')
    #             if nch == 0:
    #                 raise Exception(f'ERROR:: \'-a\' option shuold be put after input frequency list')
    #             if nch+1 > len(args):
    #                 raise Exception(f'ERROR:: # of input amp should be same as # of input freqs.')
    #             amps_val = args[1:nch+1]
    #             def is_num(s):
    #                 try: float(s)
    #                 except ValueError: return False
    #                 else: return True
    #             if not all([is_num(x) for x in amps_val]):
    #                 raise Exception(f'ERROR:: non-digit input in amplitude list: {amps_val}')
    #             args = args[nch+1:]
    #         elif args[0] == '-ip':
    #             ip_addr = args[1]
    #             args = args[2:]
    #         elif args[0] == '-h':
    #             print('PRINT HELP::')
    #             raise
    #         else:
    #             arg_val += [args[0]]
    #             args = args[1:]
    #             nch += 1
    #             pass
    #         pass

    #     fpga = fpga_control(ip_address=ip_addr)
    #     MAX_CH = fpga.MAX_CH

    #     def is_num(s):
    #         try: float(s)
    #         except ValueError: return False
    #         else: return True
    #     if not all([is_num(x) for x in arg_val]):
    #         raise Exception(f'non-digit input in frequency list: {arg_val}')
    #     if len(arg_val) > MAX_CH:
    #         raise Exception(f'too many frequencies! = {len(arg_val)} / {MAX_CH}')
    #     if power>0 and len(arg_val)*power > MAX_CH:
    #         raise Exception(f'exceeding max # of channels = {len(arg_val)}*{power} > {MAX_CH}')
    #     if len(arg_val) == 0    :
    #         raise Exception(f'no input frequencies!')
    #     def two_div(val):
    #         return len(bin(val-1)) -2
    #     input_len = 2**two_div(len(arg_val))
    #     if power >0 and power*input_len > MAX_CH:
    #         raise Exception(f'exceeding max # of channels = {input_len}*{power} > {MAX_CH}')
    #     dds_f_MHz = [float(v) for v in arg_val]
    #     if 200000 % rate_kSPS != 0:
    #         raise Exception(f'sampling rate [kSPS] should be a divisor of 2000000: input rate = {rate_kSPS} kSPS')
    #     if fname is None:
    #         fname  = 'tod'
    #         for f in dds_f_MHz: fname += f'_{f:+08.3f}MHz'
    #         fname += f'_{rate_kSPS:04d}kSPS'
    #         fname += strftime('_%Y-%m%d-%H%M%S')
    #         fname += '.rawdata'
    #     if isfile(fname):
    #         raise Exception(f'{fname} is existed.')
    #     if amps_val is not None and len(amps_val) != len(dds_f_MHz):
    #         raise Exception(f'# of input amp should be same as # of input freqs.')

    #     while len(dds_f_MHz) & (len(dds_f_MHz)-1):
    #         dds_f_MHz.append(0.)
    #         if amps_val is not None: amps_val.append(0.)
    # except Exception as e:
    #     print( 'Usage: measure_tod.py [(float)freq0_MHz] [(float)freq1_MHz] ...', file=stderr)
    #     print(f'       option: -f [(str)filename] (default: tod_INPUTFREQ_RATE_DATE.rawdata)', file=stderr)
    #     print( '                  >> output filename', file=stderr)
    #     print(f'               -l [(int)length] (default: {data_length_default:d})', file=stderr)
    #     print( '                  >> data length of event', file=stderr)
    #     print(f'               -r [(int)rate(kSPS)] (defalut: {rate_kSPS_default:d})', file=stderr)
    #     print( '                  >> sample rate of measurement', file=stderr)
    #     print(f'               -a [(float)scale0] [(float)scale1] ... (default: None)', file=stderr)
    #     print(f'                  >> amplitude scale (0.0 to 1.0). This option should be put after the frequency list.', file=stderr)
    #     print(f'                     # of amplitude scale should be same as # of input freqs.', file=stderr)
    #     print(f'               -ip [(str)ip-v4] (default: {ip_addr})', file=stderr)
    #     print(f'                  >> ip address of target SiTCP', file=stderr)
    #     print(f'               -p [(int)num] (default: {power:d})', file=stderr)
    #     print(f'                  >> amplitude (<={MAX_CH:d})', file=stderr)
    #     print(e)
    #     exit(1)

    # measure_tod(fpga, MAX_CH, dds_f_MHz, data_length, rate_kSPS, power, fname, amps=amps_val)
