import sys

sys.path.append("../")

from Lib.DevLib.SerialDev import Serial_tool
from Lib.LogicalTest.infoProcess import *
from Lib.LogicalTest.LogicalFuncs import BlowLeavesMenu,BodyMenu
from Lib.CommandLib.contrlCmd import Ctrl
from Lib.tool.docker_tool import check_docker, docker_close_power
from Lib.UnittestLib.body import body_ctrl
from Lib.UnittestLib.blow_leaves_head import blow_ctrl
''' 设置 '''
timeInfo = 0.8


def blow_main_loop():
    check_docker()
    serial_dev = Serial_tool(baudrate=460800)
    dev = serial_dev.connectClientDev()
    ctrl = Ctrl()
    if serial_dev.isConnectedDev(dev):
        print("主板串口已连接")
    else:
        print("未找到主板串口")
        sys.exit(0)
    docker_close_power(dev)
    Info.getVerInfo(dev, 2)
    while True:
        try:
            parent = BlowLeavesMenu.blow_menu()
            child = BodyMenu.dispMenu(parent)
            code = int(input(">"))
            if code == 100:
                break
            elif 0 < code <= parent:
                blow_ctrl(dev, code, ctrl)
            elif parent < code <= child+parent:
                body_ctrl(dev, code, ctrl, parent)
            else:
                print("请按照提示输入参数")
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    blow_main_loop()
