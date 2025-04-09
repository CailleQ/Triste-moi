import asyncio
import bleak
import signal
import sys
import json
from bleak import BleakClient
from datetime import datetime


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
    running = False

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

async def run():
    scan_flag = False
    FIX_OTA_ERR = False
    FIX_CONFIG_ERR = False
    base_name = get_base_name()
    # # 假设base_name为"DC_6666666666666666"来测试
    # base_name = "DC_6666666666666666"
    if not base_name:
        print("未找到 BaseName，脚本退出。")
        return

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
                        utf8_data = data.decode('utf-8').replace('\x00', '')
                        log_entry = f"{timestamp} - {utf8_data}\n"
                    except UnicodeDecodeError:
                        log_entry = f"{timestamp} - (无法解码)\n"
                    if current_instruction and instruction_callbacks.get(current_instruction):
                        callback = instruction_callbacks[current_instruction]#回调函数处理接收数据
                        callback(utf8_data)
                    
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

                # 发送读取查看是否卡在升级步骤命令
                current_instruction = GET_OTA_FLAG_CMD
                await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, GET_OTA_FLAG_CMD.encode('utf-8'))
                print(f"发送命令：{GET_OTA_FLAG_CMD}")
                await asyncio.sleep(1)  # 等待设备响应

                # 发送读取查看是否卡在配置步骤命令
                current_instruction = GET_CONFIG_FLAG_CMD
                await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, GET_CONFIG_FLAG_CMD.encode('utf-8'))
                print(f"发送命令：{GET_CONFIG_FLAG_CMD}")
                await asyncio.sleep(1)  # 等待设备响应

                # current_instruction = FIX_OTA_FLAG_CMD
                # await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, FIX_OTA_FLAG_CMD.encode('utf-8'))
                # print(f"发送命令：{FIX_OTA_FLAG_CMD}")
                # await asyncio.sleep(3)  # 等待设备响应
                # 发送修复CONFIG_FLAG指令
                current_instruction = FIX_CONFIG_FLAG_CMD
                await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, FIX_CONFIG_FLAG_CMD.encode('utf-8'))
                print(f"发送命令：{FIX_CONFIG_FLAG_CMD}")
                await asyncio.sleep(3)  # 等待设备响应
                
                current_instruction = KEEP_ALIVE_CMD
                print("60S 保活检查修复结果：")
                for i in range(60): 
                    await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, KEEP_ALIVE_CMD.encode('utf-8'))
                    # 打印60S倒计时
                    print(f"{i+1}S")
                    await asyncio.sleep(1)  # 等待设备响应
                # 修复成功后断开连接并结束脚本
                print("修复成功，断开连接")
                await client.disconnect()
                return
            
        else:
            print(f"未找到设备 {base_name}。")
        

    

    print("已断开与设备的连接。")

if __name__ == "__main__":
    asyncio.run(run())
