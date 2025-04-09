import asyncio
import bleak
import signal
import sys
import json
from bleak import BleakClient
from datetime import datetime
import threading
import queue

current_instruction = None
# Bluetooth信息
SERVICE_UUID = "1d14d6ee-fd63-4fa1-bfa4-8f47b42119f0"
CHARACTERISTIC_UUID_SUBSCRIBE = "f7782343-566d-6646-1233-2a132c0100dc"
CHARACTERISTIC_UUID_SEND_LOG = "f7c8c341-9827-2786-3236-5a132d0100dc"

# 命令字符串
SITE_SELECT_CMD = "DC+MODE=SITE_SELECT"
NORMAL_MODE_CMD = "DC+MODE=NORMAL"
RTK_CONFIG_CMD = "DC+MODE=RTK_CONFIG"
GET_DC_INFO_CMD = "DC+INFO?"
GET_NTRIP_MODE_CMD = "DC+NTRIP_MODE?"
GET_HALOW_VERSION_CMD = "HALOW_VERSION?"
FIX_OTA_FLAG_CMD = "DCsave,OTA_FLAG=YES;"
FIX_CONFIG_FLAG_CMD  = "DCsave,H_CONF_FLAG=YES;"
GET_OTA_FLAG_CMD = "DCread,OTA_FLAG;"
GET_CONFIG_FLAG_CMD = "DCread,H_CONF_FLAG;"

KEEP_ALIVE_CMD = "1"  # 每秒发送的保活命令

ble_name = ""
dc_mac = ""
halow_ssid = ""
halow_mac = ""
dc_firm_ver = ""
ntrip_mode_value = ""
halow_version_value = ""
avg_cn0 = None
gps_fix_err = False
gps_status = None


def handle_get_ota_flag_response(data):
    # 如果data不为空，则打印data
    if data:
        print(f"OTA_FLAG: {data}")
        if "NO" in data:
            FIX_OTA_ERR = True
            print(f"扫描到变砖风险，开始纠错: {data}")
            return data
def handle_get_config_flag_response(data):
    if data:
        print(f"CONFIG_FLAG: {data}")
        if "NO" in data:
            FIX_CONFIG_ERR = True
            print(f"扫描到变砖风险，开始纠错: {data}")
            return data
    
# 指令回调函数字典
instruction_callbacks = {
    GET_OTA_FLAG_CMD: handle_get_ota_flag_response,
    GET_CONFIG_FLAG_CMD: handle_get_config_flag_response,
}

# 控制循环的标志
running = True

def signal_handler(sig, frame):
    global running
    print("\n检测到 Ctrl-C. 停止脚本...")

# 注册 Ctrl-C 信号处理器
signal.signal(signal.SIGINT, signal_handler)

# 读取 JSON 文件中的 BaseName
def get_base_name():
    try:
        with open('/home/firefly/.ros/base.json', 'r') as f:
            data = json.load(f)
            return data.get("BaseName")
    except Exception as e:
        print(f"读取 BaseName 出错: {e}")
        return None

# 创建一个线程安全的队列，用于存储要发送的指令
instruction_queue = queue.Queue()

# 创建一个锁，用于线程安全地访问共享资源
lock = threading.Lock()

# 用户输入指令的线程函数
def input_thread_function():
    global running
    while running:
        user_input = input("请输入指令（或按Ctrl+C退出）：")
        if user_input:
            with lock:
                instruction_queue.put(user_input)

async def run():
    scan_flag = False
    FIX_OTA_ERR = False
    FIX_CONFIG_ERR = False
    # 初始化定义base_name为空
    base_name = None
    # 输入蓝牙扫描时间
    while True:
        try:
            scan_time = int(input("请输入蓝牙扫描时间（单位：秒）："))
            break
        except ValueError:
            print("输入无效，请输入一个整数。")
    # 扫描蓝牙设备并打印所有的设备
    while scan_time:
        # 尝试扫描指定的蓝牙设备
        device = None
        print("正在扫描设备...")
        devices = await bleak.BleakScanner.discover()
        print("已发现关于DC的设备：")
        for d in devices:
            # 只打印蓝牙名称包含"DC"的设备
            if "DC" in d.name:
                print(f"- {d.name} ({d.address})")
        # 固定扫描10S就退出
        await asyncio.sleep(scan_time)
        print("扫描结束")
        break

    # 交互询问是否使用bsae.json里的作为蓝牙名称
    while True:
        user_input = input("是否使用base.json里的蓝牙名称？(y/n): ")
        if user_input.lower() == 'y':
            base_name = get_base_name()
            if base_name:
                print(f"使用base.json里的蓝牙名称: {base_name}")
                break
        elif user_input.lower() == 'n':
            base_name = input("请输入蓝牙名称: ")
            if base_name:
                print(f"使用输入的蓝牙名称: {base_name}")
                break
        else:
            print("无效输入，请重新输入。")
    if base_name is None:
        print(f"蓝牙名称: {base_name}")
        print("未找到 BaseName，脚本退出。")
        return
    
    # 创建并启动用户输入线程
    input_thread = threading.Thread(target=input_thread_function)
    input_thread.daemon = True  # 设置为守护线程，主程序退出时自动终止
    input_thread.start()

    print(f"目标设备：{base_name}")
    while running:
        # 尝试扫描指定的蓝牙设备
        device = None
        print("正在扫描设备...")
        devices = await bleak.BleakScanner.discover()
        print("已发现设备：")
        for d in devices:
            print(f"- {d.name} ({d.address})")
            if d.name == base_name:
                device = d
                break

        if not device:
            print(f"设备 '{base_name}' 未找到。")
            scan_flag = False
        # 开始连接并进行修复
        if not scan_flag:
            async with BleakClient(device, timeout=30.0) as client:
                # 等待一段时间以确保设备准备好
                await asyncio.sleep(5)
                print(f"已连接到 {base_name}")

                # 确保服务已解析
                client_services = client.services
                # 检查特征是否支持通知
                print("检查特征是否支持通知...")
                for char in client.services.get_service(SERVICE_UUID).characteristics:
                    if char.uuid == CHARACTERISTIC_UUID_SUBSCRIBE:
                        print(f"特征 {char.uuid} 的属性: {char.properties}")
                        if "notify" not in char.properties:
                            print(f"特征 {CHARACTERISTIC_UUID_SUBSCRIBE} 不支持通知。")
                            return
                # 定义接收数据的回调函数
                def handle_notification(sender, data):
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        utf8_data = data.decode('utf-8').replace('\x00', ' ')
                        log_entry = f"{timestamp} - {utf8_data}\n"
                    except UnicodeDecodeError:
                        log_entry = f"{timestamp} - (无法解码)\n"
                    print(log_entry)
                    
                    with open("yarbo_data.log", "a") as log_file:
                        log_file.write(log_entry)

                # 订阅特征
                print(f"尝试订阅特征 {CHARACTERISTIC_UUID_SUBSCRIBE}...")
                try:
                    await client.start_notify(CHARACTERISTIC_UUID_SUBSCRIBE, handle_notification)
                    print("已订阅通知。")
                except bleak.BleakError as e:
                    print(f"订阅特征 {CHARACTERISTIC_UUID_SUBSCRIBE} 失败，继续执行。错误信息: {e}")
                    return
                # 发送指令
                while running:
                    # 处理用户输入的指令队列
                    with lock:
                        while not instruction_queue.empty():
                            instruction = instruction_queue.get()
                            try:
                                # 发送指令到蓝牙设备
                                await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, instruction.encode())
                                print(f"已发送指令: {instruction}")
                            except Exception as e:
                                print(f"发送指令失败: {e}")
                                break
                    # 每秒发送保活命令
                    await asyncio.sleep(1)
                    try:
                        await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, KEEP_ALIVE_CMD.encode())
                    except Exception as e:
                        print(f"发送保活命令失败: {e}")
                        break
        else:
            print(f"未找到设备 {base_name}。")
        

    print("已断开与设备的连接。")

if __name__ == "__main__":
    asyncio.run(run())
