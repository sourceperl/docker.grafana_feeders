#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import sys
import time
import traceback
from influxdb import InfluxDBClient


class Devices(object):
    # init datasource
    # PLC TBox
    yun = ModbusTCPDevice("192.168.0.90", port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    yun.add_bits_table(0, 2)
    yun.add_floats_table(0, 6)


class Tags(object):
    # tags list
    # from Yun
    PID_AUTO = Tag(False, src=Devices.yun, ref={"type": "bit", "addr": 0})
    PID_MAN = Tag(False, src=Devices.yun, ref={"type": "bit", "addr": 1})
    PID_PV = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 0})
    PID_SP = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 2})
    PID_OUT = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 4})
    PID_KP = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 6})
    PID_KI = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 8})
    PID_KD = Tag(0.0, src=Devices.yun, ref={"type": "float", "addr": 10})

    @classmethod
    def update_tags(cls):
        # update tags
        pass


if __name__ == '__main__':
    # connect to influxdb DB
    client = InfluxDBClient(host="influxdb", port=8086)
    client.switch_database("mydb")

    # wait PyHMI modbus thread first polling (avoid default 0 value)
    time.sleep(2.0)

    # feed influxdb
    while True:
        try:
            # write to influx db
            l_metrics = [
                {
                    "measurement": "maquette_pid",
                    "fields": {
                        "pv": round(Tags.PID_PV.val, 2),
                        "sp": round(Tags.PID_SP.val, 2),
                        "out": round(Tags.PID_OUT.val, 2),
                    },
                },
            ]
            client.write_points(points=l_metrics)
            # wait for next update
            time.sleep(1.0)
        except KeyboardInterrupt:
            break
        except:
            # log except to stderr
            traceback.print_exc(file=sys.stderr)
            # wait before next try
            time.sleep(2.0)
