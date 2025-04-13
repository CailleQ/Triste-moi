# -*- coding:utf-8 -*-
import serial
import serial.tools.list_ports
import time
import os, sys

sys.path.append("../")

from Lib.ParmSetLib.parmSet import ParmList
from Lib.DevLib.SerialDev import Serial_tool
from Lib.LogicalTest.infoProcess import *
from Lib.LogicalTest.LogicalFuncs import MowMenu,BodyMenu
from Lib.CommandLib.contrlCmd import Ctrl
from Lib.tool.docker_tool import check_docker, docker_close_power
from Lib.UnittestLib.mow_head import mow_ctrl
from Lib.UnittestLib.body import body_ctrl

''' 设置 '''
timeInfo = 0.8


def mow_main_loop():
    check_docker()
    serial_dev = None
    choose = int(input("选择波特率：\n0.默认115200;1.460800\n>"))
    if choose == 0:
        serial_dev = Serial_tool()
    elif choose == 1:
        serial_dev = Serial_tool(baudrate=460800)

    dev = serial_dev.connectClientDev()
    ctrl = Ctrl()
    if serial_dev.isConnectedDev(dev):
        print("主板串口已连接")
    else:
        print("未找到主板串口")
        sys.exit(0)
    docker_close_power(dev)
    Info.getVerInfo(dev, 3)
    while True:
        try:
            parent = MowMenu.dispMenu()
            child = BodyMenu.dispMenu(parent)
            code = int(input(">"))
            if code == 0:
                MowMenu.dispMenu()

            if code == 100:
                break
            elif 0 < code <= parent:
                mow_ctrl(dev, code, ctrl)
            elif parent < code <= child + parent:
                body_ctrl(dev, code, ctrl, parent)
            else:
                print("请按照提示输入参数")
        except KeyboardInterrupt:
            break
        except ValueError:
            print("请按照提示输入参数")

    dev.close()
    print("设备已断开")


if __name__ == '__main__':
    mow_main_loop()
