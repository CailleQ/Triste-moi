import serial
import serial.tools.list_ports
import time
import os, sys

sys.path.append("../")

from Lib.DevLib.SerialDev import Serial_tool
from Lib.LogicalTest.infoProcess import *
from Lib.CommandLib.contrlCmd import readCmd
from Lib.tool.docker_tool import check_docker, docker_close_power


def mow_main_loop():
    check_docker()
    serial_dev = Serial_tool()

    dev = serial_dev.ultrasoundDev()
    read = readCmd()
    if serial_dev.isConnectedDev(dev):
        print("主板串口已连接")
    else:
        print("未找到主板串口")
        sys.exit(0)
    docker_close_power(dev)
    while True:
        try:
            read.console_(dev, func1=Info.tail_ul, cycle=0)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    mow_main_loop()
