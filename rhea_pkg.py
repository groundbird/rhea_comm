#!/usr/bin/env python3

FREQ_CLK_HZ = 200_000_000

PHASE_WIDTH      = 32
SIN_COS_WIDTH    = 16
ADC_DATA_WIDTH   = 14
IQ_DATA_WIDTH    = SIN_COS_WIDTH + ADC_DATA_WIDTH + 1
IQ_DS_DATA_WIDTH = 56
DS_RATE_MIN      = 20
DS_RATE_MAX      = 200000

def main():
    '''Nothing to do'''
    print('Hi.')

if __name__ == '__main__':
    main()
