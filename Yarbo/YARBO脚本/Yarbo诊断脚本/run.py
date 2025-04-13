# -*- coding:utf-8 -*-
from SnowScripts.snow_unittest import snow_main_loop
from MowScripts.mow_unittest import mow_main_loop
from SnowScripts.set_flash_param import set_flash
from BlowLeavesScripts.blow_leaves_unittest import blow_main_loop

if __name__ == '__main__':
    while True:
        try:
            print("========选择操作=========")
            print("0.启动扫雪单项测试控制")
            print("1.启动除草单项测试控制")
            print("2.启动吹落叶单项测试控制")
            print("3.设置flash参数")
            print("100.退出系统")
            order = int(input(">>>"))
            if order == 0:
                snow_main_loop()
            elif order == 1:
                mow_main_loop()
            elif order == 2:
                blow_main_loop()
            elif order == 3:
                set_flash()
            elif order == 100:
                break
            else:
                print("输入有误，请按照序号请重新输入")
        except KeyboardInterrupt:
            break
