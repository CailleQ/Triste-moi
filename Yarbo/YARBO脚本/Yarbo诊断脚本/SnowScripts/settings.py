import sys
import time

sys.path.append("../")

from Lib.ParmSetLib.parmSet import ParmList, parmSet
from Lib.DevLib.SerialDev import Serial_tool
from Lib.CommandLib.contrlCmd import ctrlCmd, readCmd
from Lib.tool.docker_tool import check_docker, docker_close_power


def run():
    check_docker()
    serial_dev = Serial_tool(baudrate=460800)
    dev = serial_dev.connectClientDev()
    ctrl = ctrlCmd()
    if serial_dev.isConnectedDev(dev):
        print("主板串口已连接")
    else:
        print("未找到主板串口")
        sys.exit(0)
    docker_close_power(dev)
    ctrl.accelerate_decelerate_settings(dev, 1, 0.8, 1)
    time.sleep(0.1)
    parmSet(0, 0, dev, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


if __name__ == '__main__':
    run()
