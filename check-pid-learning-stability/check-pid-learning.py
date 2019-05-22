#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import numpy as np
from scipy import fftpack
from influxdb import InfluxDBClient

# some const
TS = 2  # second between 2 samples

# connect to influxdb DB
client = InfluxDBClient(host="influxdb", port=8086)
client.switch_database("mydb")

# select last value (to avoid null first value we must do time(xxs, now()) and no time(xxs))
req = "SELECT mean(\"out\") AS f1 FROM \"maquette_pid\" WHERE time < now() - 4s GROUP BY time(%ds, now()) fill(previous) ORDER BY time DESC LIMIT 150" % TS

# format data and check all data is available
l_points = []
for point in client.query(req).get_points():
    if point['f1'] is None:
        print("data unavailable, skip fft", file=sys.stderr)
        exit(1)
    l_points.append(point['f1'])

# number of samples
Ns = len(l_points)

# N samples, every sample is time value (in s)
# 0 -> t_max with Ns items
t_max = TS * Ns
t_samples = np.linspace(0.0, t_max, Ns)

# convert list to numpy array
y_samples = np.asarray(l_points)

# build signal
nb = len(y_samples)
x = np.linspace(0.0, (nb - 1) * TS, nb)

# compute fft
yf = fftpack.fft(y_samples)
xf = np.linspace(0.0, 1.0 / (2.0 * TS), nb // 2)
ya = 2.0 / nb * np.abs(yf[:nb // 2])

# normalize ya to % of signal
ya = ya * 100.0 / ya.sum()

# print peak higher than 3%
for i in np.argwhere(ya > 3.0).flatten():
    f = xf[i]
    m = ya[i]
    if f > 0:
        print("freq = %.4f Hz, level = %.2f %%,  period = %.2f s" % (f, m, 1/f))
    else:
        print("freq = %.4f Hz, level = %.2f %%" % (f, m))
