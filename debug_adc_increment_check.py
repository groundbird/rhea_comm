#!/usr/bin/env python3

from sys import stdin

a_res = 0
b_res = 0

t0, a0, b0 = (int(v) for v in stdin.readline().split())
if a0 < 0: a0 += (1<<14)
if b0 < 0: b0 += (1<<14)

a0 += 1
b0 += 1
if a0 >= (1<<14): a0 -= (1<<14)
if b0 >= (1<<14): b0 -= (1<<14)

for line in stdin:
    t, a, b = (int(v) for v in line.split())
    if a < 0: a += (1<<14)
    if b < 0: b += (1<<14)
    #if a != a0: print 'A:', t, a, a0
    #if b != b0: print 'B:', t, b, b0
    a_res |= (a ^ a0)
    b_res |= (b ^ b0)
    a0 += 1
    b0 += 1
    if a0 >= (1<<14): a0 -= (1<<14)
    if b0 >= (1<<14): b0 -= (1<<14)
    pass

a_res, b_res
print(format(a_res, '014b'))
print(format(b_res, '014b'))
