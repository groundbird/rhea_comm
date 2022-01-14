#!/usr/bin/env python3


## config
rate_kSPS_default   = 1 # 1 kSPS ~ downsample:200000
premea_leng_default = 10000
data_length_default = 1024
thre_sigma_default  = 3.
thre_count_default  = 1
trig_pos_default    = 100


## constant
from fpga_control import fpga_control
fpga = fpga_control()
MAX_CH = fpga.MAX_CH
TRIG_CH = fpga.TRIG_CH


## check firmware
from sys import stderr
if not TRIG_CH > 0:
    print(f'Firmware version: {fpga.info.get_version()}', file=stderr)
    print('Trigger function is disable!', file=stderr)
    exit(1)
    pass

## main
def measure_trg(dds_f_MHz, data_length, thre_sigma, thre_count, rate_kSPS, trig_pos, pre_length, fname):
    from math    import floor
    from struct  import pack
    from time    import sleep
    from numpy   import mean, std
    from packet_reader import read_iq_packet

    print('TRIGGER MEASUREMENT')
    for i, freq in enumerate(dds_f_MHz):
        print(f'ch{i:03d}: {freq} MHz')
        pass

    fpga.init()
    fpga.iq.set_read_width(len(dds_f_MHz))
    dds_f_Hz_multi  = [freq * 1e6 for freq in dds_f_MHz]
    dds_f_Hz_multi *= floor(float(MAX_CH) / float(len(dds_f_MHz))+0.5)
    fpga.dds.set_freqs(dds_f_Hz_multi)
    fpga.ds.set_rate(floor(200000 / rate_kSPS+0.1))
    fpga.trg.set_trig_pos(trig_pos)

    ## make dummpy packet
    dummy_packet  = b'\xff'
    dummy_packet += b'\x00' + pack('>I', rate_kSPS * 1000)
    for freq in dds_f_MHz:
        freq_Hz = int(floor(freq * 1e6 + 0.5))
        freq_packet = (b'\x00' * 3) if freq_Hz >= 0 else (b'\xff' * 3)
        freq_packet += pack('>i', freq_Hz)
        dummy_packet += freq_packet * 2
        pass
    dummy_packet += b'\xee'

    ## pre-measurement
    cnt = 0
    packet_size = 7 + 7 * 2 * len(dds_f_MHz)
    cnt_finish = packet_size * pre_length

    print('pre-measurement')
    fpga.tcp.clear()
    fpga.iq.iq_on()

    data_stock = [0 for i in range(pre_length)]
    cnt = 0
    try:
        for i in range(pre_length):
            cnt = i
            time, data = read_iq_packet(fpga.tcp.read(packet_size))
            data_stock[i] = data
            pass
    except:
        if cnt == 0:
            print('no data...')
            exit(1)
        pass
    fpga.iq.iq_off()

    print(f'read {cnt:d} events')
    data_stock = list(zip(*data_stock[0:cnt]))
    mean_set  = [mean(d) for d in data_stock]
    sigma_set = [std(d)  for d in data_stock]
    print('min:', end=' ')
    for m, s in zip(mean_set, sigma_set): print(int(m - thre_sigma * s), end=' ')
    print()
    print('max:', end=' ')
    for m, s in zip(mean_set, sigma_set): print(int(m + thre_sigma * s), end=' ')
    print()

    ## set threshold
    for i in range(floor(len(mean_set)/2)):
        Imean,  Qmean  = mean_set [2*i:2*i+2]
        Isigma, Qsigma = sigma_set[2*i:2*i+2]
        Imin = int(Imean - thre_sigma * Isigma)
        Imax = int(Imean + thre_sigma * Isigma)
        Qmin = int(Qmean - thre_sigma * Qsigma)
        Qmax = int(Qmean + thre_sigma * Qsigma)
        fpga.trg.set_threshold(i, [Imin, Imax], [Qmin, Qmax], trg_reset = False)
        pass
    fpga.trg.set_thre_count(thre_count, trg_reset = True)

    ## get trigger event
    print('main-measurement')
    fpga.tcp.clear()
    fpga.trg.start()

    print('wait trigger')
    cnt = 0
    while fpga.trg.state() == 1:
        cnt += 1
        if cnt % 10 == 0:
            print(cnt)
        else:
            print('.', end='')
            pass
        sleep(1)
        pass

    print('triggerd')

    f = open(fname, 'wb')
    f.write(dummy_packet)

    cnt = 0
    cnt_finish = packet_size * data_length

    while True:
        buff = fpga.tcp.read(min(1024, cnt_finish - cnt))
        f.write(buff)
        if not len(buff): break
        cnt += len(buff)
        if cnt >= cnt_finish: break
        pass

    f.close()
    fpga.iq.iq_off()
    fpga.dac.txenable_off()
    print(f'write raw data to {fname}')


if __name__ == '__main__':
    ## get argv
    from sys     import argv, stderr
    from os.path import isfile
    from time    import strftime

    try:
        args = argv[1:]
        arg_val = []
        fname = None
        data_length = data_length_default
        thre_sigma  = thre_sigma_default
        thre_count  = thre_count_default
        rate_kSPS   = rate_kSPS_default
        trig_pos    = trig_pos_default
        pre_length  = premea_leng_default
        while args:
            if args[0] == '-f':
                fname = args[1]
                args = args[2:]
            elif args[0] == '-l':
                data_length = int(args[1])
                args = args[2:]
            elif args[0] == '-t':
                thre_sigma = abs(float(args[1]))
                args = args[2:]
            elif args[0] == '-c':
                thre_count = int(args[1])
                args = args[2:]
            elif args[0] == '-r':
                rate_kSPS = int(args[1])
                args = args[2:]
            elif args[0] == '-p':
                trig_pos = int(args[1])
                args = args[2:]
            elif args[0] == '-m':
                pre_length = int(args[1])
                args = args[2:]
            else:
                arg_val += [args[0]]
                args = args[1:]
                pass
            pass
        if len(arg_val) > TRIG_CH : raise
        if len(arg_val) == 0      : raise
        dds_f_MHz = [float(v) for v in arg_val]
        if 200000 % rate_kSPS != 0: raise
        if fname == None:
            fname  = 'tod_trg'
            for f in dds_f_MHz: fname += f'_{f:+08.3f}MHz'
            fname += strftime('_%Y-%m%d-%H%M%S')
            fname += '.rawdata'
            pass
        if isfile(fname):
            print(f'{fname:s} is existed.', file=stderr)
            raise
        while len(dds_f_MHz) & (len(dds_f_MHz)-1): dds_f_MHz.append(0.)
    except:
        print( 'Usage: measure_trg.py [freq0_MHz] [freq1_MHz] ...', file=stderr)
        print( '       option: -f [filename]            (mandantory)', file=stderr)
        print( '                  output filename', file=stderr)
        print(f'               -l [(int)length]         (default: {data_length_default:d})', file=stderr)
        print( '                  data length of triggered event (<= 1024)', file=stderr)
        print(f'               -t [(float)thre(sigma)]  (default: {thre_sigma_default:f})', file=stderr)
        print( '                  trigger threshold whose unit is standard deviation', file=stderr)
        print(f'               -c [(int)thre_count]     (defalut: {thre_count_default:d})', file=stderr)
        print( '                  trigger threshold in time-axis', file=stderr)
        print(f'               -r [(int)rate(kSPS)]     (defalut: {rate_kSPS_default:d})', file=stderr)
        print( '                  sample rate of measurement', file=stderr)
        print(f'               -p [(int)trig_pos]       (defalut: {rate_kSPS_default:d})', file=stderr)
        print( '                  data length before trigger time (<= data length)', file=stderr)
        print(f'               -m [(int)length]         (default: {premea_leng_default:d})', file=stderr)
        print( '                  data length of pre-measurement for estimation of mean/sigma', file=stderr)
        exit(1)

    measure_trg(dds_f_MHz, data_length, thre_sigma, thre_count, rate_kSPS, trig_pos, pre_length, fname)
