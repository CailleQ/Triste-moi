import os.path
import sys
import time

# 解决linux下导报无法识别的问题
sys.path.append("../")
from Lib.LogicalTest.infoProcess import cutter_info
from Lib.DevLib.SerialDev import Serial_tool
from Lib.tool.logger import logger
from Lib.tool.docker_tool import check_docker, docker_close_power
from Lib.tool.common import print_with_color
from Lib.MathLib.DataCoversion import Coversion
from Lib.SelfCheck.selfClass import *
from Lib.LogicalTest.LogicalClass import *
from Lib.CommandLib.contrlCmd import mowCtrlCmd
from typing import Dict


def check_data(data: bytes, tup: tuple, index: int, other: str = '其他'):
    result = tup[data[index]] if len(tup) >= data[index] + 1 else other
    return result


def base_write(dev, cmd: list):
    Coversion.loadChksum(cmd)
    dev.write(bytes(cmd))


class mower_self_check:
    result: dict = {"success": [], "fail": []}
    # 刀盘信号值
    # cur_flag: int = 1  # 刀盘电流
    pwm_flag: int = 1  # 刀盘pwm
    route_flag: int = 1  # 刀盘转速
    temp_flag: int = 1  # 刀盘温度
    temp_status_flag: int = 1  # 刀盘温度状态
    over_flag: int = 1  # 刀盘过流
    default_flag: int = 1  # 故障状态
    # 升降电机信号值
    pos_flag = 1  # 位置运行超时
    # end_flag = 0  # 升降电机运行结束位
    ele_cur_flag = 1  # 升降电机电流
    ele_over_flag = 1  # 升降电机过流

    def __init__(self):
        self.dev = None
        self.ctrl = mowCtrlCmd()

    def response(self, *args) -> None:
        """
        集合所有单项测试结果，汇总到result测试结果中，以便于后续处理
        :param args: 单项测试结果，用于解析成功失败结果汇总
        :return: None
        """
        for i in args:
            if i is not None:
                if isinstance(i.get("success"), list):
                    self.result.get("success").extend([v for v in i.get("success") if v is not None and v != ''])
                else:
                    self.result.get("success").append(i.get("success"))
                if isinstance(i.get("fail"), list):
                    self.result.get("fail").extend([v for v in i.get("fail") if v is not None and v != ''])
                else:
                    self.result.get("fail").append(i.get("fail"))
        from datetime import datetime
        filename = "logs/" + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".txt"

        with open(filename, 'a', newline='') as f:
            print_with_color("==========成功结果==========", "green")
            f.write("==========成功结果==========\n")
            for i in self.result.get("success"):
                if i != '':
                    f.write(i)
                    # f.write("\n")
                    print_with_color(i, "green", end=1)
        with open(filename, 'a', newline='') as f:
            print_with_color("==========失败结果==========", "red")
            f.write("==========失败结果==========\n")
            for i in self.result.get("fail"):
                if i != '':
                    f.write(i)
                    # f.write("\n")
                    print_with_color(i, "red", end=1)

    def _communication(self) -> Dict[str, str]:
        """
        版本测试
        :return:
        """
        t0 = time.time()
        result = {"success": '', "fail": ''}
        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                if rawLine[0] == 0xAA and rawLine[1] == 0xB0:
                    SelfCheckVerInfo.body_version[0] = int(rawLine[10])
                    SelfCheckVerInfo.body_version[1] = int(rawLine[11])
                    SelfCheckVerInfo.body_version[2] = int(rawLine[12])
                    SelfCheckVerInfo.body_version[3] = int(rawLine[13])
                elif rawLine[0] == 0xAA and rawLine[1] == 0xB1:
                    SelfCheckVerInfo.head_version[0] = int(rawLine[2])
                    SelfCheckVerInfo.head_version[1] = int(rawLine[3])
                    SelfCheckVerInfo.head_version[2] = int(rawLine[4])
                    SelfCheckVerInfo.head_version[3] = int(rawLine[5])
                if time.time() - t0 > 3:
                    SelfCheckVerInfo.headVersion = f"{SelfCheckVerInfo.head_version[1]}.{SelfCheckVerInfo.head_version[2]}.{SelfCheckVerInfo.head_version[3]}"
                    SelfCheckVerInfo.bodyVersion = f"{SelfCheckVerInfo.body_version[1]}.{SelfCheckVerInfo.body_version[2]}.{SelfCheckVerInfo.body_version[3]}"
                    print(f">车头固件版本：{SelfCheckVerInfo.headVersion}")
                    print(f">车身固件版本：{SelfCheckVerInfo.bodyVersion}")
                    result['success'] += f"车头固件版本：{SelfCheckVerInfo.headVersion}\n" \
                                         f"车身固件版本：{SelfCheckVerInfo.bodyVersion}\n"
                    if SelfCheckVerInfo.headVersion == "0.0.0":
                        result['fail'] += "车头未连接或固件版本过低\n"
                        while True:
                            try:
                                print(">车头未连接或固件版本过低，无法自检车头部分，是否继续？")
                                res = int(input("0:否，1:是<"))
                                if res == 0:
                                    sys.exit(0)
                                elif res == 1:
                                    break
                                else:
                                    print("输入有误")
                                    continue
                            except KeyboardInterrupt:
                                break
                            except NameError:
                                print("输入有误")
                                continue
                            except ValueError:
                                print("输入有误")
                                continue
                    else:
                        while True:
                            try:
                                print(">请确认版本是否正确")
                                res = int(input("0:否，1:是<"))
                                if res == 0:
                                    result['fail'] += "固件版本异常\n"
                                    sys.exit(0)
                                elif res == 1:
                                    result['success'] += "固件版本正常\n"
                                    break
                                else:
                                    print("输入有误")
                                    continue
                            except KeyboardInterrupt:
                                break
                            except NameError:
                                print("输入有误")
                                continue
                            except ValueError:
                                print("输入有误")
                                continue
                    break
            except KeyboardInterrupt:
                break
            except NameError:
                print("输入有误请重新输入")
                continue
            except ValueError:
                print("输入有误请重新输入")
                continue
            except IndexError:
                print("输入有误请重新输入")
                continue
        return result

    def _IMU(self) -> Dict[str, str]:
        """
        陀螺仪测试
        :return:
        """
        result = {"success": '', "fail": ''}
        data_list = []
        data_key = ["x_ang", "y_ang", "z_ang", "x_acc", "y_acc", "z_acc"]

        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                rawData = cutter_info.mower_imu(rawLine)
                data = {}
                if rawData:
                    init_data = [
                        MowerImu.gyro_x_ang,
                        MowerImu.gyro_y_ang,
                        MowerImu.gyro_z_ang,
                        MowerImu.gyro_x_acc,
                        MowerImu.gyro_y_acc,
                        MowerImu.gyro_z_acc,
                    ]
                    if all(arg is not None for arg in init_data):
                        for index, value in enumerate(init_data):
                            data[data_key[index]] = value / 10 ** 6
                        data_list.append(data)
                    if len(data_list) == 50:
                        break
            except KeyboardInterrupt:
                break
        data_key_res_num = {
            "val_0_num": 0,
            "ang_gt_1_num": 0,
            "acc_no_9_11_num": 0
        }
        if len(data_list) == 50:
            for imu_data in data_list:
                for imu_info, val in imu_data.items():
                    if val == 0:
                        data_key_res_num["val_0_num"] += 1
                    elif imu_info == 'x_ang' or imu_info == 'y_ang' or imu_info == 'z_ang':
                        if val > 1:
                            data_key_res_num["ang_gt_1_num"] += 1
                    elif imu_info == 'z_acc':
                        if val < 9 or val > 11:
                            data_key_res_num["acc_no_9_11_num"] += 1
            if data_key_res_num["val_0_num"] > 20:
                print(f">陀螺仪有{data_key_res_num['val_0_num']}个值数据为0，陀螺仪测试失败")
                result['fail'] += f"陀螺仪有{data_key_res_num['val_0_num']}个值数据为0，陀螺仪测试失败\n"
            else:
                print(">陀螺仪数据反馈测试成功")
                result['success'] += "陀螺仪数据反馈测试成功\n"

            if data_key_res_num["ang_gt_1_num"] > 5:
                print(">陀螺仪角速度大于1的数量超过5个，陀螺仪测试失败")
                result['fail'] += "陀螺仪角速度大于1的数量超过5个，陀螺仪测试失败\n"
            else:
                print(">陀螺仪角速度数据反馈测试成功")
                result['success'] += "陀螺仪角速度数据反馈测试成功\n"

            if data_key_res_num["acc_no_9_11_num"] > 0:
                print(f">陀螺仪z轴加速度为不在9-11m/s²，陀螺仪测试失败")
                result[
                    'fail'] += f"陀螺仪z轴加速度数据{data_key_res_num['acc_no_9_11_num']}个不在9-11m/s²，陀螺仪加速度测试失败\n"
            else:
                print(">陀螺仪加速度数据反馈测试成功")
                result['success'] += "陀螺仪加速度数据反馈测试成功\n"
        return result

    def _cutter(self) -> Dict[str, str]:
        """
        刀盘电机自检
        :return:
        """
        result = {"success": '', "fail": ''}
        t = time.time()
        left_route_list = []
        right_route_list = []
        left_cur_num = 0
        right_cur_num = 0
        while time.time() - t < 20:
            try:
                if time.time() - t > 0.01:
                    self.ctrl.cutter_ctrl(self.dev, 0, 100, 100)
                rawline = Coversion.read17BytesInfo(self.dev)
                if rawline[0] == 0xAA and rawline[1] == 0x8C:
                    # 左刀盘电流
                    left_cutter_cur = Coversion.bytes_to_uint16(rawline, 2) / 100
                    if 0 < left_cutter_cur <= 2:
                        left_cur_num += 1
                    else:
                        pass

                    # 左刀盘pwm
                    if time.time() - t > 2:
                        left_cutter_pwm = Coversion.bytes_to_uint16(rawline, 4)
                        if left_cutter_pwm > 0:
                            pass
                        else:
                            self.pwm_flag = 0
                    # 左刀盘转速
                    left_cutter_route = Coversion.bytes_to_uint16(rawline, 6)
                    left_route_list.append(left_cutter_route)
                    # if time.time() - t > 4:
                    #     if 1800 < (left_cutter_route * 3.5 - 3500) < 2000:
                    #         pass
                    #     else:
                    #         self.route_flag = 0
                    # 左刀盘电机温度
                    left_cutter_temp = rawline[8] - 40
                    if left_cutter_temp > 0:
                        pass
                    else:
                        self.temp_flag = 0
                    # 左刀盘温度状态
                    left_cutter_temp_status = rawline[10]
                    if left_cutter_temp_status == 0 or left_cutter_temp_status == 1:
                        pass
                    else:
                        self.temp_status_flag = 0
                    # 左刀盘过流信息
                    left_cutter_over_cur = rawline[11]
                    if left_cutter_over_cur == 0:
                        pass
                    else:
                        self.over_flag = 0
                    # 左刀盘故障状态
                    left_cutter_default_status = rawline[12]
                    if left_cutter_default_status == 0:
                        pass
                    else:
                        self.default_flag = 0

                if rawline[0] == 0xAA and rawline[1] == 0x8D:
                    # 右刀盘电流
                    right_cutter_cur = Coversion.bytes_to_uint16(rawline, 2) / 100
                    if 0 < right_cutter_cur <= 2:
                        right_cur_num += 1
                    else:
                        pass

                    # 右刀盘pwm
                    if time.time() - t > 2:
                        right_cutter_pwm = Coversion.bytes_to_uint16(rawline, 4)
                        if right_cutter_pwm > 0:
                            pass
                        else:
                            self.pwm_flag = 0
                    # 右刀盘转速
                    right_cutter_route = Coversion.bytes_to_uint16(rawline, 6)
                    right_route_list.append(right_cutter_route)
                    # if time.time() - t > 4:
                    #     if 1800 < (right_cutter_route * 3.5 - 3500) < 2000:
                    #         pass
                    #     else:
                    #         self.route_flag = 0
                    # 左刀盘电机温度
                    right_cutter_temp = rawline[8] - 40
                    if right_cutter_temp > 0:
                        pass
                    else:
                        self.temp_flag = 0
                    # 左刀盘温度状态
                    right_cutter_temp_status = rawline[10]
                    if right_cutter_temp_status == 0 or right_cutter_temp_status == 1:
                        pass
                    else:
                        self.temp_status_flag = 0
                    # 左刀盘过流信息
                    right_cutter_over_cur = rawline[11]
                    if right_cutter_over_cur == 0:
                        pass
                    else:
                        self.over_flag = 0
                    # 左刀盘故障状态
                    right_cutter_default_status = rawline[12]
                    if right_cutter_default_status == 0:
                        pass
                    else:
                        self.default_flag = 0
                # time.sleep(0.01)
            except KeyboardInterrupt:
                break
        if left_cur_num > 100 and right_cur_num > 100:
            # print(left_cur_num, right_cur_num)
            print(">左右刀盘电流值测试成功")
            result['success'] += '左右刀盘电流值测试成功\n'
        else:
            # print(left_cur_num, right_cur_num)
            print(">左右刀盘电流值异常,请检查")
            result['fail'] += '左右刀盘电流值异常,请检查\n'
        if self.pwm_flag:
            print(">左右刀盘pwm测试成功")
            result['success'] += '左右刀盘pwm测试成功\n'
        else:
            print(">左右刀盘pwm异常,请检查")
            result['fail'] += '左右刀盘pwm异常,请检查\n'
        if all(3400 < i < 3800 for i in left_route_list[round(len(left_route_list) / 4) * 3:]):
            # 1440
            print(">左刀盘转速测试成功")
            result['success'] += '左刀盘转速测试成功\n'
        else:
            print(">左刀盘转速异常,请检查")
            result['fail'] += '左刀盘转速异常,请检查\n'

        if all(3400 < i < 3800 for i in right_route_list[round(len(right_route_list) / 4) * 3:]):
            # 1560
            print(">右刀盘转速测试成功")
            result['success'] += '右刀盘转速测试成功\n'
        else:
            print(">右刀盘转速异常,请检查")
            result['fail'] += '右刀盘转速异常,请检查\n'

        if self.temp_flag:
            print(">左右刀盘温度测试成功")
            result['success'] += '左右刀盘温度测试成功\n'
        else:
            print(">左右刀盘温度异常,请检查")
            result['fail'] += '左右刀盘温度异常,请检查\n'

        if self.temp_status_flag:
            print(">左右刀盘温度状态测试成功")
            result['success'] += '左右刀盘温度状态测试成功\n'
        else:
            print(">左右刀盘温度状态异常,请检查")
            result['fail'] += '左右刀盘温度状态异常,请检查\n'

        if self.over_flag:
            print(">左右刀盘未过流")
            result['success'] += '左右刀盘未过流\n'
        else:
            print(">左右刀盘过流或其他异常,请检查")
            result['fail'] += '左右刀盘过流或其他异常,请检查\n'

        if self.default_flag:
            print(">左右刀盘故障状态正常")
            result['success'] += '左右刀盘故障状态正常\n'
        else:
            print(">左右刀盘发生故障或其他异常,请检查")
            result['fail'] += '左右刀盘发生故障或其他异常,请检查\n'
        return result

    def _elevator(self) -> Dict[str, str]:
        """
        升降电机自检
        :return:
        """
        result = {"success": '', "fail": ''}
        ele_cur_num = 0
        print(">升降电机即将运行到0%位置")
        self.ctrl.elevator_ctrl(self.dev, 0)
        t1 = time.time()
        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                    if rawLine[9] == 0:
                        print('>升降电机运行到0%成功')
                        result['success'] += '升降电机运行到0%成功\n'
                        while True:
                            try:
                                order = input('>请测量刀盘离地高度是否102mm\n0.否;1.是>')
                                if order == "1":
                                    result['success'] += '升降电机距离地面102mm\n'
                                    break
                                elif order == '0':
                                    result['fail'] += '升降电机距离地面不是102mm\n'
                                    break
                                else:
                                    print("输入有误")
                                    continue
                            except KeyboardInterrupt:
                                break
                            except NameError:
                                print("输入有误")
                                continue
                            except ValueError:
                                print("输入有误")
                                continue
                        break
                if time.time() - t1 > 40:
                    self.pos_flag = 0
                    print('升降电机运行到0%时超时，请检查!!!')
                    result['fail'] += '升降电机运行到0%时超时，请检查!!!\n'
                    break
            except NameError:
                print("输入有误请重新输入")
                continue
            except ValueError:
                print("输入有误请重新输入")
                continue
            except IndexError:
                print("输入有误请重新输入")
                continue
            except KeyboardInterrupt:
                break
        print(">升降电机即将运行到100%位置")
        time.sleep(0.1)
        self.ctrl.elevator_ctrl(self.dev, 100)
        t2 = time.time()
        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                    # 升降电机电流
                    elevator_cur = Coversion.bytes_to_uint16(rawLine, 7) / 100
                    if 0 < elevator_cur < 2:
                        ele_cur_num += 1

                    # 升降电机过流
                    elevator_over_cur = rawLine[12]
                    if elevator_over_cur == 0:
                        pass
                    else:
                        self.ele_over_flag = 0
                    # 判断位置退出
                    if rawLine[9] == 100:
                        print(">升降电机运行到100%成功")
                        result["success"] += "升降电机运行到100%成功"
                        self.end_flag = 1
                        while True:
                            try:
                                order = input('>请测量刀盘离地高度是否30mm\n0.否;1.是>')
                                if order == "1":
                                    result['success'] += '升降电机距离地面30mm\n'
                                    break
                                elif order == '0':
                                    result['fail'] += '升降电机距离地面不是30mm\n'
                                    break
                                else:
                                    print("输入有误")
                                    continue
                            except KeyboardInterrupt:
                                break
                            except NameError:
                                print("输入有误")
                                continue
                            except ValueError:
                                print("输入有误")
                                continue
                        break
                if time.time() - t2 > 40:
                    self.pos_flag = 0
                    self.end_flag = 1
                    result['fail'] += '升降电机运行到100%时超时，请检查!!!\n'
                    print(">升降电机运行到100%超时，请检查")
                    break
            except NameError:
                print("输入有误请重新输入")
                continue
            except ValueError:
                print("输入有误请重新输入")
                continue
            except IndexError:
                print("输入有误请重新输入")
                continue
            except Exception:
                break
        if self.pos_flag:
            pass
        else:
            result['fail'] += '升降电机运行超时,请检查\n'
        if ele_cur_num >= 200:
            result['success'] += '升降电机电流值正常\n'
        else:
            result['fail'] += '升降电机电流值范围异常，请检查\n'
        if self.ele_over_flag:
            result['success'] += '升降电机电流值正常\n'
        else:
            result['fail'] += '升降电机可能过流或其他异常，请检查\n'
        return result

    def _proximity(self) -> Dict[str, str]:
        """
        抬起传感器
        :return:
        """
        result = {"success": '', "fail": ''}
        pro_list = []
        t = time.time()
        self.dev.flushInput()
        print(">检测抬起传感器默认状态，请不要抬起车头")
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                pro_list.append(rawLine[2])

        if 0 in pro_list[round(len(pro_list) / 2):]:
            print(">抬起传感器默认状态信号测试通过")
            result['success'] += '抬起传感器默认状态信号测试通过\n'
        else:
            print(">抬起传感器默认状态信号测试不通过")
            result['fail'] += '抬起传感器默认状态信号测试不通过\n'
        print(">检测抬起传感器左侧信号，请抬起左轮")
        input("请确认已经抬起左轮，按回车键继续...")
        self.dev.flushInput()
        pro_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                pro_list.append(rawLine[2])
        if 1 in pro_list[round(len(pro_list) / 2):]:
            print(">抬起传感器左侧抬起信号测试通过")
            result['success'] += '抬起传感器左侧抬起信号测试通过\n'
        else:
            print(">抬起传感器左侧抬起信号测试不通过")
            result['fail'] += '抬起传感器左侧抬起信号测试不通过\n'
        self.dev.flushInput()
        print(">检测抬起传感器右侧信号，请抬起右轮")
        input("请确认已经抬起右轮，按回车键继续...")
        pro_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                pro_list.append(rawLine[2])

        if 2 in pro_list[round(len(pro_list) / 2):]:
            print(">抬起传感器右侧抬起信号测试通过")
            result['success'] += '抬起传感器右侧抬起信号测试通过\n'
        else:
            print(">抬起传感器右侧抬起信号测试不通过")
            result['fail'] += '抬起传感器右侧抬起信号测试不通过\n'
        self.dev.flushInput()
        print(">检测抬起传感器双轮信号，请抬起双轮")
        input("请确认已经抬起双轮，按回车键继续...")
        pro_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                pro_list.append(rawLine[2])
        if 3 in pro_list[round(len(pro_list) / 2):]:
            print(">抬起传感器全部抬起信号测试通过")
            result['success'] += '抬起传感器全部抬起信号测试通过\n'
        else:
            print(">抬起传感器全部抬起信号测试不通过")
            result['fail'] += '抬起传感器全部抬起信号测试不通过\n'
        return result

    def _hooks(self) -> Dict[str, str]:
        """
        锁扣传感器
        :return:
        """
        result = {"success": '', "fail": ''}
        print(">检测钩锁传感器默认状态，请放上锁全部锁扣")
        input("请确认已上锁全部锁扣，按回车键继续...")
        self.dev.flushInput()
        hook_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                hook_list.append(rawLine[4])
        if 0 in hook_list[round(len(hook_list) / 2):]:
            print("钩锁传感器默认状态信号测试通过")
            result['success'] += '钩锁传感器默认状态信号测试通过\n'
        else:
            print("钩锁传感器默认状态信号测试不通过")
            result['fail'] += '钩锁传感器默认状态信号测试不通过\n'

        print(">检测左侧锁扣单独解锁状态，请抬起左侧锁扣")
        input("请确认已经抬起左侧锁扣，按回车键继续...")
        self.dev.flushInput()
        hook_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                hook_list.append(rawLine[4])
        if 1 in hook_list[round(len(hook_list) / 2):]:
            print("钩锁传感器左侧抬起信号测试通过")
            result['success'] += '钩锁传感器左侧抬起信号测试通过\n'
        else:
            print("钩锁传感器左侧抬起信号测试不通过")
            result['fail'] += '钩锁传感器左侧抬起信号测试不通过\n'
        return result

    def _rain(self) -> Dict[str, str]:
        """
        雨水传感器
        :return:
        """
        result = {"success": '', "fail": ''}
        print(">检测雨水传感器默认状态")
        rain_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                rain_list.append(rawLine[3])
        if 0 in rain_list[round(len(rain_list) / 2):]:
            print("雨水传感器默认状态信号测试通过")
            result['success'] += '雨水传感器默认状态信号测试通过\n'
        else:
            print("雨水传感器默认状态信号测试不通过")
            result['fail'] += '雨水传感器默认状态信号测试不通过\n'

        print(">检测雨水传感器触发状态，请在传感器处浇水")
        input("请确认已经触发雨水传感器，按回车键继续...")
        rain_list = []
        t = time.time()
        while time.time() - t < 2:
            rawLine = Coversion.read17BytesInfo(self.dev)
            if rawLine[0] == 0xAA and rawLine[1] == 0x8A:
                rain_list.append(rawLine[3])

        if 1 in rain_list[round(len(rain_list) / 2):]:
            print("雨水传感器触发状态信号测试通过")
            result['success'] += '雨水传感器触发状态信号测试通过\n'
        else:
            print("雨水传感器触发状态信号测试不通过")
            result['fail'] += '雨水传感器触发状态信号测试不通过\n'
        return result

    def _light(self) -> Dict[str, str]:
        result = {"success": '', "fail": ''}
        print("即将打开车头灯")
        self.ctrl.light_control(self.dev, 0, R=200)
        while True:
            try:
                open_res = int(input("请判断车头灯是否已经打开，0:否，1:是<"))
                if open_res == 1:
                    print("车头灯已经打开，测试成功")
                    result["success"] += "车头灯已经打开，测试成功\n"
                    break
                else:
                    print("车头灯打开失败，请检查")
                    result["fail"] += "车头灯打开失败，请检查\n"
                    break
            except NameError:
                print("输入有误请重新输入")
                continue
            except ValueError:
                print("输入有误请重新输入")
                continue
            except IndexError:
                print("输入有误请重新输入")
                continue
            except KeyboardInterrupt:
                break
        time.sleep(0.1)

        print("即将关闭车头灯")
        self.ctrl.light_control(self.dev, 0, R=0)
        while True:
            try:
                open_res = int(input("请判断车头灯是否已经关闭，0:否，1:是<"))
                if open_res == 1:
                    print("车头灯已经关闭，测试成功")
                    result["success"] += "车头灯已经关闭，测试成功\n"
                    break
                else:
                    print("车头灯关闭失败，请检查")
                    result["fail"] += "车头灯关闭失败，请检查\n"
                    break
            except NameError:
                print("输入有误请重新输入")
                continue
            except ValueError:
                print("输入有误请重新输入")
                continue
            except IndexError:
                print("输入有误请重新输入")
                continue
            except KeyboardInterrupt:
                break
        return result

    def _term(self) -> Dict[str, str]:
        """
        急停自检
        :return:
        """
        result = {"success": '', "fail": ''}

        # 按下急停测试
        head_term_status = None
        body_term_status = None
        input(">请确认急停按钮已按下，按回车键继续...")
        t = time.time()
        self.dev.flushInput()
        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                if rawLine[0] == 0xAA and rawLine[1] == 0xB2:
                    head_term_status = check_data(rawLine, ("正常", "触发判断中", "急停"), 4)
                if rawLine[0] == 0xAA and rawLine[1] == 0xB3:
                    body_term_status = check_data(rawLine, ("正常", "急停", "恢复正常中"), 8)
                if time.time() - t > 3 and head_term_status == body_term_status:
                    print(head_term_status, body_term_status)
                    if head_term_status and body_term_status:
                        if head_term_status == body_term_status == "急停":
                            print(">车头车身或按钮急停状态一致")
                            result["success"] += "车头车身或按钮急停状态一致，测试成功\n"
                            break
                        else:
                            print(">车头车身或按钮急停状态不一致，测试失败")
                            result["fail"] += "车头车身或按钮急停状态不一致，测试失败\n"
                            break
                if time.time() - t > 5:
                    print(">急停按钮已按下测试超时")
                    result["fail"] += "急停按钮已按下测试超时\n"
                    break
            except KeyboardInterrupt:
                break
        # 拉起急停测试
        head_term_status = None
        body_term_status = None
        input(">请确认急停按钮已拉起，按回车键继续...")
        t1 = time.time()
        self.dev.flushInput()
        while True:
            try:
                rawLine = Coversion.read17BytesInfo(self.dev)
                if rawLine[0] == 0xAA and rawLine[1] == 0xB2:
                    head_term_status = check_data(rawLine, ("正常", "触发判断中", "急停"), 4)
                if rawLine[0] == 0xAA and rawLine[1] == 0xB3:
                    body_term_status = check_data(rawLine, ("正常", "急停", "恢复正常中"), 8)
                if time.time() - t1 > 3 and head_term_status == body_term_status:
                    if head_term_status and body_term_status:
                        if head_term_status == body_term_status == "正常":
                            print(">拉起急停时车头车身或按钮急停状态一致")
                            result["success"] += "拉起急停时车头车身或按钮急停状态一致，测试成功\n"
                            break
                        else:
                            print(">拉起急停时车头车身或按钮急停状态不一致，测试失败")
                            result["fail"] += "拉起急停时车头车身或按钮急停状态不一致，测试失败\n"
                            break
                if time.time() - t1 > 5:
                    print(">急停按钮已拉起测试超时")
                    result["fail"] += "急停按钮已拉起测试超时\n"
                    break
            except KeyboardInterrupt:
                break

        return result

    def _crash(self) -> Dict[str, str]:
        result = {"success": '', "fail": ''}

        # 触发碰撞
        # 使能0
        input("请确认已捏住左侧碰撞条不要松手，按回车键继续...")
        res_list: list[dict] = [self._crash_crash(
            5, "触发碰撞时，左侧反馈碰撞状态测试成功;",
            "触发碰撞时，左侧反馈碰撞状态测试失败;")]
        input("请确认已捏住前侧碰撞条不要松手，按回车键继续...")
        res_list.append(self._crash_crash(
            6, "触发碰撞时，前侧反馈碰撞状态测试成功;",
            "触发碰撞时，前侧反馈碰撞状态测试失败;"))
        input("请确认已捏住右侧碰撞条不要松手，按回车键继续...")
        res_list.append(self._crash_crash(
            7, "触发碰撞时，右侧反馈碰撞状态测试成功;",
            "触发碰撞时，右侧反馈碰撞状态测试失败;"))

        # 未触发碰撞
        # 使能0,1
        input("请确认已松开碰撞条，按回车键继续...")
        res_list.append(self._set_crash(1, "正常", "未触发碰撞时，不反馈碰撞状态测试成功;",
                                        "未触发碰撞时，不反馈碰撞状态测试失败;"))
        # 收集所有结果
        for res in res_list:
            result["success"] += res["success"]
            result["fail"] += res["fail"]
        return result

    def _set_crash(self, enable, res, s_msg, f_msg) -> Dict[str, str]:
        result = {"success": '', "fail": ''}
        t = time.time()
        crash_list = []
        self.dev.flushInput()
        cmd = [0xAA, 0x45, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF]
        Coversion.int16_to_bytes(cmd, enable, 6)
        base_write(self.dev, cmd)
        time.sleep(0.5)
        while time.time() - t < 3:
            try:
                while time.time() - t < 3:
                    rawLine = Coversion.read17BytesInfo(self.dev)
                    if rawLine[0] == 0xAA and rawLine[1] == 0xB2:
                        crash_list.append(check_data(rawLine, ("正常", "急停"), 5))
                        break
            except KeyboardInterrupt:
                break
        if res in crash_list:
            result["success"] += s_msg + '\n'
        else:
            result["fail"] += f_msg + '\n'

        return result

    def _crash_crash(self, index, s_msg, f_msg) -> Dict[str, str]:
        result = {"success": '', "fail": ''}
        t = time.time()
        crash_list = []
        self.dev.flushInput()
        while time.time() - t < 3:
            try:
                while time.time() - t < 3:
                    rawLine = Coversion.read17BytesInfo(self.dev)
                    if rawLine[0] == 0xAA and rawLine[1] == 0x8E and rawLine[2] == 3:
                        # print(rawLine)
                        # print(check_data(rawLine, ("正常", "急停"), index))
                        crash_list.append(check_data(rawLine, ("正常", "急停"), index))
                        break
            except KeyboardInterrupt:
                break
        if "急停" in crash_list:
            result["success"] += s_msg + '\n'
        else:
            result["fail"] += f_msg + '\n'

        return result

    def run(self) -> None:
        check_docker()
        serial_tool = Serial_tool(baudrate=460800)
        self.dev = serial_tool.connectClientDev()
        if serial_tool.isConnectedDev(self.dev):
            print("主板串口已连接")
            logger.info(">>>>>>>>>>>主板串口已连接>>>>>>>>>>>")
        else:
            print("未找到主板串口")
            logger.info(">>>>>>>>>>>未找到主板串口<<<<<<<<<<<")
            sys.exit(0)
        docker_close_power(self.dev)
        self.response(*[
            self._communication(),
            self._IMU(),
            self._cutter(),
            self._elevator(),
            self._proximity(),
            self._hooks(),
            self._rain(),
            self._light(),
            self._term(),
            self._crash()
        ])


if __name__ == '__main__':
    check = mower_self_check()
    check.run()
