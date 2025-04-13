# -*- coding:utf-8 -*-
import sys

sys.path.append("../")

from Lib.ParmSetLib.setAllParm import *
from Lib.DevLib.SerialDev import Serial_tool
from Lib.ParmSetLib.parmSet import *

realParm = ParmList()
order = OrderList()


def set_flash():
    print("正在关闭docker...")
    # os.system('docker stop snowbot')
    os.system('sudo systemctl stop docker.socket;sudo systemctl stop docker')
    serial_tool = Serial_tool()
    MotherBoardDev = serial_tool.connectClientDev()
    if serial_tool.isConnectedDev(MotherBoardDev):
        print("主板串口已连接")
    else:
        print("未找到主板串口")
        sys.exit(0)

    setAllFlashParm(MotherBoardDev, realParm, order)

    MotherBoardDev.close()
    print("设备已断开")


if __name__ == '__main__':
    set_flash()
