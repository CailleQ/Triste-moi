# -*- coding:utf-8 -*-  
import os
import subprocess
import sys
import threading
import time

# 解决linux下导报无法识别的问题
sys.path.append("../")
from Lib.SelfCheck.baseSelfCheckLib import GetInfo
from Lib.SelfCheck.hubSelfCheckLib import hubSelfCheck
from Lib.DevLib.SerialDev import Serial_tool
from Lib.tool.logger import logger
from Lib.tool.docker_tool import check_docker, docker_close_power
from Lib.tool.common import print_with_color
from sound_test import sound
from Lib.SelfCheck.selfClass import *

play_mp3_done = threading.Event()
microphone_done = threading.Event()
play_output_done = threading.Event()


class Sound:

    def sound(self):
        config = 'amixer -c 0 contents'
        result = {"success": '', "fail": ''}
        obj = subprocess.Popen(config, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = obj.stdout.read()
        err = obj.stderr.read()
        res = res.decode('utf-8').split('numid')[1:]

        lst = []
        for i in res:
            temp = []
            for s in i.split('\n'):
                if 'name' in s:
                    temp.append(s)
                if ': values=' in s:
                    temp.append(s)
            lst.append(temp)
        new_list = []
        for i in lst:
            dict = {}
            dict['numid'] = i[0].split(',')[0][1:]
            dict['name'] = i[0].split('name=')[1][1:-1]
            dict['values'] = i[1].split('=')[1]
            new_list.append(dict)
        new_list.sort(key=lambda x: int(x['numid']))
        config = [{'numid': '1', 'name': 'Receive PATH3 Source Select', 'values': '3'},
                  {'numid': '2', 'name': 'Receive PATH2 Source Select', 'values': '2'},
                  {'numid': '3', 'name': 'Receive PATH1 Source Select', 'values': '1'},
                  {'numid': '4', 'name': 'Receive PATH0 Source Select', 'values': '0'},
                  {'numid': '5', 'name': 'Transmit SDO3 Source Select', 'values': '3'},
                  {'numid': '6', 'name': 'Transmit SDO2 Source Select', 'values': '2'},
                  {'numid': '7', 'name': 'Transmit SDO1 Source Select', 'values': '1'},
                  {'numid': '8', 'name': 'Transmit SDO0 Source Select', 'values': '0'},
                  {'numid': '9', 'name': 'I2STDM Digital Loopback Mode', 'values': '0'},
                  {'numid': '10', 'name': 'PCM Read Wait Time MS', 'values': '0'},
                  {'numid': '11', 'name': 'PCM Write Wait Time MS', 'values': '0'},
                  {'numid': '12', 'name': '3D Mode', 'values': '0'},
                  {'numid': '13', 'name': 'ALC Capture Target Volume', 'values': '12'},
                  {'numid': '14', 'name': 'ALC Capture Max PGA', 'values': '7'},
                  {'numid': '15', 'name': 'ALC Capture Min PGA', 'values': '0'},
                  {'numid': '16', 'name': 'ALC Capture Function', 'values': '3'},
                  {'numid': '17', 'name': 'ALC Capture ZC Switch', 'values': 'off'},
                  {'numid': '18', 'name': 'ALC Capture Hold Time', 'values': '0'},
                  {'numid': '19', 'name': 'ALC Capture Decay Time', 'values': '0'},
                  {'numid': '20', 'name': 'ALC Capture Attack Time', 'values': '5'},
                  {'numid': '21', 'name': 'ALC Capture NG Threshold', 'values': '10'},
                  {'numid': '22', 'name': 'ALC Capture NG Type', 'values': '1'},
                  {'numid': '23', 'name': 'ALC Capture NG Switch', 'values': 'on'},
                  {'numid': '24', 'name': 'ZC Timeout Switch', 'values': 'off'},
                  {'numid': '25', 'name': 'Capture Digital Volume', 'values': '192,192'},
                  {'numid': '26', 'name': 'Capture Mute', 'values': 'off'},
                  # {'numid': '27', 'name': 'Left Channel Capture Volume', 'values': '8'},
                  {'numid': '28', 'name': 'Right Channel Capture Volume', 'values': '0'},
                  {'numid': '29', 'name': 'Playback De-emphasis', 'values': '0'},
                  {'numid': '30', 'name': 'Capture Polarity', 'values': '0'},
                  {'numid': '31', 'name': 'PCM Volume', 'values': '192,192'},
                  {'numid': '32', 'name': 'Left Mixer Left Bypass Volume', 'values': '0'},
                  {'numid': '33', 'name': 'Right Mixer Right Bypass Volume', 'values': '0'},
                  # {'numid': '34', 'name': 'Output 1 Playback Volume', 'values': '22,22'},
                  {'numid': '35', 'name': 'Output 2 Playback Volume', 'values': '33,33'},
                  {'numid': '36', 'name': 'Headphone Switch', 'values': 'off'},
                  {'numid': '37', 'name': 'Speaker Switch', 'values': 'on'},
                  {'numid': '38', 'name': 'Main Mic Switch', 'values': 'on'},
                  {'numid': '39', 'name': 'Headset Mic Switch', 'values': 'on'},
                  {'numid': '40', 'name': 'Left PGA Mux', 'values': '2'},
                  {'numid': '41', 'name': 'Right PGA Mux', 'values': '0'},
                  {'numid': '42', 'name': 'Differential Mux', 'values': '0'},
                  {'numid': '43', 'name': 'Mono Mux', 'values': '0'},
                  # {'numid': '44', 'name': 'Left Line Mux', 'values': '3'},
                  {'numid': '45', 'name': 'Right Line Mux', 'values': '0'},
                  {'numid': '46', 'name': 'Left Mixer Left Playback Switch', 'values': 'on'},
                  {'numid': '47', 'name': 'Left Mixer Left Bypass Switch', 'values': 'off'},
                  {'numid': '48', 'name': 'Right Mixer Right Playback Switch', 'values': 'on'},
                  {'numid': '49', 'name': 'Right Mixer Right Bypass Switch', 'values': 'off'}]
        new_list = [i for i in new_list if
                    i['numid'] != '27' and i['numid'] != '34' and i['numid'] != '44' and i['numid'] != '34']
        for k, v in enumerate(new_list):
            if v != config[k]:
                print(v)

        if new_list == config:
            print("声卡配置正常")
            result['success'] += '声卡配置正常'
        else:
            print("声卡配置异常请检查")
            result['fail'] += '声卡配置异常请检查！！！'
        return result

    def play_sound(self):
        print(">即将播放音乐...", end='')
        cmd = 'sudo play -v 1 mp3/test.mp3'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()
        while True:
            try:
                play_mp3_done.set()
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > 5:
                    process.terminate()
                    process.wait()
                    print("\r>mp3播放完成")
                    play_mp3_done.clear()
                    break
                time.sleep(1)
            except:
                process.terminate()
                process.wait()
                play_mp3_done.clear()

    def mp3_thread(self, result):
        play_mp3_thread = threading.Thread(target=self.play_sound)
        play_mp3_thread.start()
        play_mp3_thread.join()
        while True:
            res = input("\r>是否听到mp3播放，0.否，1.是")
            if res == '0':
                result['fail'] += "mp3播放失败;"
                break
            elif res == '1':
                result['success'] += "mp3播放成功;"
                break
            else:
                print(">输入有误请请重新输入")

    def play_output(self):
        print(">即将开始播放录音...")
        cmd = 'sudo play output.wav'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()
        while True:
            try:
                play_output_done.set()
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > 5:
                    process.terminate()
                    process.wait()
                    print("\r>播放完成")
                    play_output_done.clear()
                    break
                time.sleep(1)
            except:
                process.terminate()
                process.wait()
                play_output_done.clear()

    def out_put_thread(self, result):
        mp3_thread = threading.Thread(target=self.play_output)
        mp3_thread.start()
        mp3_thread.join()
        while True:
            res = input("\r>是否听到录音播放，0.否，1.是")
            if res == '0':
                result['fail'] += "mp3播放失败;"
                break
            elif res == '1':
                result['success'] += "mp3播放成功;"
                break
            else:
                print("输入有误请请重新输入")

    def microphone(self):
        print(">麦克风测试录音...")
        cmd = 'arecord -D "plughw:CARD=ES8388,DEV=0" -f S16_LE -r 44100 -c 2 -d 10 output.wav'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()
        while True:
            try:
                microphone_done.set()
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > 5:
                    process.terminate()
                    process.wait()
                    print("\r>录音完成")
                    microphone_done.clear()
                    break
                time.sleep(1)
            except:
                process.terminate()
                process.wait()
                microphone_done.clear()

    def microphone_thread(self):
        mp3_thread = threading.Thread(target=self.microphone)
        mp3_thread.start()
        mp3_thread.join()

    def run_sound(self):
        result = {"success": '', "fail": ''}
        self.mp3_thread(result)
        self.microphone_thread()
        self.out_put_thread(result)
        return result


def get_data(*args):
    lst = {"success": [], "fail": []}
    for i in args:
        if i is not None:
            if isinstance(i.get("success"), list):
                lst.get("success").extend([v for v in i.get("success") if v is not None and v != ''])
            else:
                lst.get("success").append(i.get("success"))
            if isinstance(i.get("fail"), list):
                lst.get("fail").extend([v for v in i.get("fail") if v is not None and v != ''])
            else:
                lst.get("fail").append(i.get("fail"))
    print_with_color("==========成功结果==========", "green")
    for i in lst.get("success"):
        if i != '':
            print_with_color(i, "green")
    print_with_color("==========失败结果==========", "red")
    for i in lst.get("fail"):
        if i != '':
            print_with_color(i, "red")


def snow_self_check():
    check_docker()
    serial_tool = Serial_tool(baudrate=460800)
    dev = serial_tool.connectClientDev()
    if serial_tool.isConnectedDev(dev):
        print("主板串口已连接")
        logger.info(">>>>>>>>>>>主板串口已连接>>>>>>>>>>>")
    else:
        print("未找到主板串口")
        logger.info(">>>>>>>>>>>未找到主板串口<<<<<<<<<<<")
        sys.exit(0)
    docker_close_power(dev)
    print(">自检脚本版本：" + BaseInfo.scriptVer)
    logger.info(">自检脚本版本：" + BaseInfo.scriptVer)
    print(">将在5s后继续...")
    logger.info(">将在5s后继续...")
    print("--------------------------")

    time.sleep(5)
    sound_test = Sound()
    getinfo = GetInfo()
    get_robot_info = getinfo.getRobotInfo(dev)
    hub = hubSelfCheck(dev)
    lft_info = None
    spd_gyro = None
    chute = None
    cover = None
    bld = None
    head_led = None
    body_led = None
    rgb = None
    top_led = None
    serail = None
    rtk = None
    net = None
    sound_res = None
    mp3_res = None

    while True:
        try:
            print(">开始车身基础功能自检")
            logger.info(">>>>>>>>>>>开始车身基础功能自检<<<<<<<<<<<")
            time.sleep(1)
            print(">清除车身电机保护并失能车头碰撞模块中...")
            logger.info(">>>>>>>>>>>清除车身电机保护并失能车头碰撞模块中...<<<<<<<<<<<")
            getinfo.clearProtect(dev, BaseInfo.BODY)
            time.sleep(1)
            print(">复位车身模块中，请等待10s...")
            getinfo.resetRobotModule(dev, BaseInfo.BODY)
            time.sleep(1)

            if SelfCheckLftInfo.lftTestFlag == 1:
                print("\n>推杆自检测试中...")
                logger.info(">>>>>>>>>>>推杆自检测试中...<<<<<<<<<<<")
                time.sleep(1)
                lft_info = getinfo.lftSelfCheck(dev)
                time.sleep(1)

            if SelfCheckSpdInfo.spdTestFlag == 1:
                print("\n>行走电机&陀螺仪自检测试中...")
                logger.info(">>>>>>>>>>>>行走电机&陀螺仪自检测试中...<<<<<<<<<<<")
                time.sleep(1)
                spd_gyro = getinfo.spdGyroSelfCheck(dev)
                time.sleep(1)

            print("\n>车身基础功能自检完成")
            logger.info(">>>>>>>>>>>>车身基础功能自检完成<<<<<<<<<<<")
            print("----------------------------")
            # 无车头
            if SelfCheckHeadInfo.headType == 0:
                print(">未检测到车头,自检结束")
                logger.info(">未检测到车头，自检结束")
                break
            # 扫雪头
            elif SelfCheckHeadInfo.headType == 1:
                print(">开始车头基础功能自检")
                logger.info(">>>>>>>>>>>>开始车头基础功能自检<<<<<<<<<<<")
                time.sleep(1)
                print(">清除车头电机保护中...")
                logger.info(">清除车头电机保护中...")
                getinfo.clearProtect(dev, BaseInfo.HEAD)
                time.sleep(1)
                print(">复位车头模块中，请等待10s...")
                getinfo.resetRobotModule(dev, BaseInfo.HEAD)
                time.sleep(1)

                if SelfCheckChuteInfo.chuteTestFlag == 1:
                    print(">抛雪管自检测试中...")
                    logger.info(">抛雪管自检测试中...")
                    time.sleep(1)
                    chute = getinfo.chuteSelfCheck(dev)
                    time.sleep(1)

                if SelfCheckCoverInfo.coverTestFlag == 1:
                    print(">俯仰角自检测试中...")
                    logger.info(">俯仰角自检测试中...")
                    time.sleep(1)
                    cover = getinfo.coverSelfCheck(dev)
                    time.sleep(1)

                if SelfCheckBldcInfo.bldcTestFlag == 1:
                    print(">卷雪电机自检测试中...")
                    logger.info(">卷雪电机自检测试中...")
                    time.sleep(1)
                    bld = getinfo.bldcSelfCheck(dev)
                    time.sleep(1)

                print(">车头基础功能自检完成")
                logger.info(">车头基础功能自检完成")
                print("----------------------------")
                print(">车身自检结束")
                logger.info(">>>>>>>>>>>>>车身自检结束<<<<<<<<<<<")
            # 吹树叶头
            elif SelfCheckHeadInfo.headType == 2:
                break
            # 割草头
            elif SelfCheckHeadInfo.headType == 3:
                break

            # Hub检测
            print(">开始进行灯光效果展示，请连同电脑提示及实际视觉效果进行判断")
            logger.info(">开始进行灯光效果展示")

            print(">车头灯测试中...")
            logger.info(">车头灯测试中...")
            time.sleep(1)
            head_led = hub.headLedSelfCheck()
            time.sleep(1)
            #
            print(">车身补光灯测试中...")
            logger.info(">车身补光灯测试中...")
            time.sleep(1)
            body_led = hub.bodyLedSelfCheck()
            time.sleep(1)

            print(">RGB灯测试中...")
            logger.info(">RGB灯测试中...")
            time.sleep(1)
            rgb = hub.rgbSelfCheck()
            time.sleep(1)

            print(">车顶灯测试中...")
            logger.info(">车顶灯测试中...")
            time.sleep(1)
            top_led = hub.topLedSelfCheck()
            time.sleep(1)

            print(">灯板效果检测已结束，请自行判断灯板是否有异常")
            logger.info(">灯板效果检测已结束")
            print("---------------------------------")
            time.sleep(1)

            print(">开始进行rtk检测")
            logger.info(">开始进行rtk检测")
            print(">rtk数据扫描中...")
            time.sleep(1)
            rtk = hub.rtk_test()
            print(">rtk检测已结束")
            logger.info(">rtk检测已结束")
            print("---------------------------------")
            time.sleep(1)

            print(">开始进行网络连接检测")
            logger.info(">开始进行网络连接检测")
            print(">网络检测中...")
            time.sleep(1)
            net = hub.networkSelfCheck()
            print(">网络连接检测已结束")
            logger.info(">网络连接检测已结束")
            print("---------------------------------")
            print(">hub功能自检测试完成")
            logger.info(">hub功能自检测试完成")

            print(">声卡检测中...")
            logger.info(">声卡检测中...")
            sound_res = sound()
            print("---------------------------------")
            time.sleep(1)

            print(">喇叭检测中...")
            logger.info(">喇叭检测中...")
            mp3_res = sound_test.run_sound()
            print("---------------------------------")
            time.sleep(1)
            break
        except KeyboardInterrupt:
            break

    dev.close()
    print("\n>设备已断开")
    # 处理结果

    logger.info(">设备已断开")
    os.system("docker restart snowbot")
    print("\n>docker已重启")
    get_data(lft_info, spd_gyro, chute, cover, bld, head_led, body_led, rgb, top_led, serail, rtk, net,
             get_robot_info, sound_res, mp3_res)


if __name__ == '__main__':
    # sound_test = Sound()
    # sound_test.run_sound()
    try:
        snow_self_check()
    except serial.SerialException as e:
        print("串口被占用，请结束其他占用串口进程.")
    except Exception as e:
        print(e)
        print("发生未知异常")
