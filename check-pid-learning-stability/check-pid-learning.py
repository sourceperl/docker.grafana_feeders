#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import traceback
import numpy as np
from scipy import fftpack
from influxdb import InfluxDBClient

# some const
UPDATE_DELAY = 30
TS = 2  # second between 2 samples
N = 150

if __name__ == '__main__':
    # connect to influxdb DB
    client = InfluxDBClient(host="influxdb", port=8086)
    client.switch_database("mydb")

    # main loop
    while True:
        try:
            # select last value (to avoid null first value we must do time(xxs, now()) and no time(xxs))
            req = "SELECT mean(\"out\") AS f1 FROM \"maquette_pid\" " \
                  "WHERE time < now() - 4s " \
                  "GROUP BY time(%ds, now()) fill(previous) " \
                  "ORDER BY time DESC LIMIT %d" % (TS, N)

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

            # remove mean of signal
            y_samples -= y_samples.mean()

            # build signal
            nb = len(y_samples)

            # compute fft
            yf = fftpack.fft(y_samples)
            xf = np.linspace(0.0, 1.0 / (2.0 * TS), nb // 2)
            ya = 1.0 / nb * np.abs(yf[:nb // 2])

            # normalize ya to % of signal
            norm_ya = 100.0 * ya / ya.sum()

            # detect peak in fft (higher than 5%)
            fft_ya_high_ids = np.argwhere(norm_ya > 5).flatten()
            fft_xf_high_vals = xf[fft_ya_high_ids]
            # group by frequency (allow 2 freq min step)
            max_f_step = xf[1] * 2
            freq_groups = np.split(fft_xf_high_vals, np.where(np.diff(fft_xf_high_vals) > max_f_step)[0]+1)
            mean_freq_groups = np.array([])
            print(freq_groups)
            if len(freq_groups[0]) > 0:
                mean_freq_groups = np.array([group.mean() for group in freq_groups])

            # write status to stdout
            print("-------------------------------------------------------------------")
            print("FFT thresholding status:")
            for i in fft_ya_high_ids:
                if xf[i] > 0:
                    print("freq = %6.4f Hz, level = %6.2f %% (%5.2f),  period = %.2f s" % (xf[i], norm_ya[i], ya[i], 1/xf[i]))
                else:
                    print("freq = %6.4f Hz, level = %6.2f %% (%5.2f)" % (xf[i], norm_ya[i], ya[i]))

            h_peaks_nb = np.sum(mean_freq_groups > 0.05)
            print("group peak: %s number of peak greater than 0.05 Hz: %d" % (mean_freq_groups, h_peaks_nb))
            status_str = "stable" 
            status_nb = 0
            if h_peaks_nb == 1:
                status_str = "pumping" 
                status_nb = 2
            elif h_peaks_nb == 2:
                status_str = "level change" 
                status_nb = 1
            print("PID status: %s" % status_str)
            print("-------------------------------------------------------------------\n")

            # write status to influx db
            l_metrics = [
                {
                    "measurement": "pid_status",
                    "fields": {
                        "status": status_nb,
                    },
                },
            ]
            client.write_points(points=l_metrics)

            # wait for next update
            time.sleep(UPDATE_DELAY)
        except KeyboardInterrupt:
            break
        except:
            # log except to stderr
            traceback.print_exc(file=sys.stderr)
            # wait before next try
            time.sleep(UPDATE_DELAY)
