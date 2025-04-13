'''
脚本名称: DC_HALOW_OTA脚本
脚本作者: AI Assistant
脚本时间: 2025-03-22
脚本版本: 0.1
脚本说明: 实现对DC设备中HALOW固件的OTA升级
'''
import os
import sys
import json
import asyncio
import signal
import logging
from datetime import datetime
from bleak import BleakScanner, BleakClient, BleakError
import time
import math
from tqdm import tqdm

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 配置日志
def setup_logging():
    """配置日志系统"""
    # 确保logs目录存在
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 生成日志文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'halow_ota_{timestamp}.log')
    
    # 配置日志格式
    log_format = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日志系统
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('HALOW_OTA')

# 全局变量
logger = setup_logging()

# 定义蓝牙连接相关参数
SERVICE_UUID = "1d14d6ee-fd63-4fa1-bfa4-8f47b42119f0"
CHARACTERISTIC_UUID_SUBSCRIBE = "f7782343-566d-6646-1233-2a132c0100dc"  # 接收常规回复
CHARACTERISTIC_UUID_SEND_LOG = "f7c8c341-9827-2786-3236-5a132d0100dc"   # 发送常规控制指令
CHARACTERISTIC_UUID_OTA_CMD = "f7bf3564-fb6d-4e53-88a4-5e37e0326063"    # 发送OTA指令

# 根据文档中提供的格式重新构建UUID
# 文档中提供的OTA固件传输characteristic为:
# 0x98,0x42,0x27,0xf3,0x34,0xfc,0x40,0x45,0xa5,0xd0,0x2c,0x58,0x1f,0x81,0xa1,0x53
CHARACTERISTIC_UUID_OTA_DATA = "984227f3-34fc-4045-a5d0-2c581f81a153"  # 正确的固件传输特征UUID

# 备选OTA数据特征UUID列表，按尝试顺序排列
ALTERNATE_OTA_DATA_UUIDS = [
    "984227f3-34fc-4045-a5d0-2c581f81a153",  # 设备实际返回的UUID格式
    "98422743-34fc-4045-a5d0-2c581f81a153",  # 之前尝试的UUID格式
    "9842f327-fc34-4540-a5d0-2c581f81a153",  # 之前尝试的UUID格式
    "9842-27f3-34fc-4045-a5d0-2c581f81a153",  # 另一种可能的格式
    "98-42-27-f3-34-fc-40-45-a5-d0-2c-58-1f-81-a1-53"  # 分隔的格式
]

# 控制连接的标志
running = True

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    global running
    logger.info("检测到Ctrl+C，准备断开连接...")
    running = False

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

def ensure_results_directory():
    """确保results目录存在"""
    results_dir = os.path.join(PROJECT_ROOT, 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        logger.info(f'创建results目录: {results_dir}')
    else:
        logger.info(f'results目录已存在: {results_dir}')

def save_ota_result(success=True, data=None):
    """
    保存OTA升级结果到json文件
    
    Args:
        success (bool): 升级是否成功
        data (dict): 成功时的升级信息
    """
    ensure_results_directory()
    
    # 准备结果数据
    result = {
        "halow_ota": {
            "code": 0 if success else 1,
            "data": data if success and data else {}
        }
    }
    
    logger.info(f"保存OTA升级结果: {result}")
    
    try:
        # 保存结果到json文件
        result_file = os.path.join(PROJECT_ROOT, 'results', 'halow_ota.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        logger.info(f'HALOW OTA升级结果已保存至: {result_file}')
    except Exception as e:
        logger.error(f'保存结果文件失败: {str(e)}')

def get_base_name():
    """从base.json文件中读取设备名称"""
    try:
        # 尝试从用户主目录读取
        home_path = os.path.expanduser("~")
        base_json_path = os.path.join(home_path, '.ros', 'base.json')
        
        if os.path.exists(base_json_path):
            with open(base_json_path, 'r') as f:
                data = json.load(f)
                base_name = data.get("BaseName")
                if base_name:
                    logger.info(f"从base.json获取到设备名称: {base_name}")
                    return base_name
                else:
                    logger.warning("base.json中不包含BaseName字段")
                    return None
        else:
            logger.warning(f"base.json文件不存在: {base_json_path}")
            return None
    except Exception as e:
        logger.error(f"读取BaseName出错: {str(e)}")
        return None

def verify_firmware_file(firmware_path):
    """
    验证固件文件是否存在并获取其大小
    
    Args:
        firmware_path (str): 固件文件路径
    
    Returns:
        tuple: (是否有效, 文件大小)
    """
    if not os.path.exists(firmware_path):
        logger.error(f"固件文件不存在: {firmware_path}")
        return False, 0
    
    file_size = os.path.getsize(firmware_path)
    logger.info(f"固件文件大小: {file_size} 字节")
    
    return True, file_size

# 修改扫描逻辑，捕获更多设备类型
async def scan_devices(base_name, scan_time=10.0):
    """
    扫描并返回指定名称的设备
    """
    target_address = None
    found_devices = []
    
    # 打印扫描提示
    print(f"正在扫描蓝牙设备，请等待 {scan_time} 秒...")
    logger.info(f"扫描时间设置为: {scan_time}秒")
    
    start_time = time.time()
    devices = await BleakScanner.discover(timeout=scan_time)
    scan_duration = time.time() - start_time
    
    logger.info(f"扫描完成，耗时 {scan_duration:.2f} 秒")
    
    if not devices:
        logger.error("未找到任何蓝牙设备")
        print("错误: 未找到任何蓝牙设备，请确保蓝牙已开启")
        return None, []
    
    for device in devices:
        device_name = device.name if device.name else "Unknown"
        logger.info(f"发现设备: {device_name} ({device.address})")
        
        # 收集所有设备
        found_devices.append({
            "name": device_name,
            "address": device.address
        })
        
        # 检查设备名称是否匹配目标名称
        if device_name and base_name.lower() in device_name.lower():
            target_address = device.address
            logger.info(f"找到目标设备: {device_name} ({device.address})")
    
    # 如果没有找到精确匹配的设备，但发现了其他设备，提供选择
    if not target_address and found_devices:
        print("\n未找到精确匹配的目标设备，但发现了以下设备:")
        for i, device in enumerate(found_devices):
            print(f"{i+1}. {device['name']} ({device['address']})")
        
        print("\n请选择一个设备进行连接 (输入数字)，或按Enter键退出:")
        user_choice = input()
        
        if user_choice and user_choice.isdigit():
            choice_idx = int(user_choice) - 1
            if 0 <= choice_idx < len(found_devices):
                target_address = found_devices[choice_idx]['address']
                logger.info(f"用户选择了设备: {found_devices[choice_idx]['name']} ({target_address})")
                print(f"已选择设备: {found_devices[choice_idx]['name']} ({target_address})")
    
    if not target_address:
        logger.error("未找到任何DC设备")
        print("错误: 未找到任何DC设备，请确保设备已开启并处于可发现状态")
    
    return target_address, found_devices

# 修改扫描逻辑，优先匹配正确的UUID
async def run():
    """
    执行HALOW固件OTA升级任务
    """
    logger.info("开始执行DC_HALOW_OTA脚本")
    
    # 检查参数
    force_data_char = None
    
    # 解析命令行参数
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--force-characteristic" and i + 1 < len(sys.argv):
            force_data_char = sys.argv[i + 1]
            logger.info(f"强制使用特征: {force_data_char}")
            print(f"将强制使用特征: {force_data_char} 进行数据传输")
            i += 2
        else:
            i += 1
    
    # 如果没有指定特征，使用默认的
    if not force_data_char:
        force_data_char = CHARACTERISTIC_UUID_OTA_DATA
        logger.info(f"默认使用特征: {force_data_char}")
    
    # 检查固件文件
    firmware_path = os.path.join(PROJECT_ROOT, 'ota_bin', 'halow_ota.bin')
    valid, firmware_size = verify_firmware_file(firmware_path)
    
    if not valid:
        print(f"错误: 找不到HALOW固件文件: {firmware_path}")
        save_ota_result(False, {"error": "固件文件不存在"})
        return
    
    print(f"已找到HALOW固件文件: halow_ota.bin (大小: {firmware_size} 字节)")
    
    # 读取固件文件内容
    with open(firmware_path, 'rb') as f:
        firmware_data = f.read()
    
    # 从base.json获取设备名称
    ble_name = get_base_name()
    if not ble_name:
        logger.error("无法从base.json获取蓝牙名称，请先配置base.json文件")
        print("错误: 无法从base.json获取蓝牙名称")
        print("请确保用户主目录下的.ros/base.json文件包含有效的BaseName")
        save_ota_result(False, {"error": "无法获取蓝牙设备名称"})
        return
    
    logger.info(f"从base.json获取的蓝牙名称: {ble_name}")
    print(f"目标设备名称: {ble_name}")
    
    # 使用扫描设备函数
    scan_timeout = 10.0
    target_address, found_devices = await scan_devices(ble_name, scan_timeout)
    
    if not target_address:
        logger.error(f"未找到设备: {ble_name}")
        print(f"错误: 未找到设备: {ble_name}")
        save_ota_result(False, {"error": "未找到目标设备"})
        return
    
    # 创建通知回调函数
    notification_responses = []
    notification_event = asyncio.Event()
    
    def notification_handler(sender, data):
        try:
            data_str = data.decode('utf-8').strip().replace('\x00', '')
            logger.info(f"收到数据: {data_str}")
            print(f"收到: {data_str}")
            notification_responses.append(data_str)
            notification_event.set()
        except UnicodeDecodeError:
            # 如果不是文本数据，记录十六进制值
            hex_data = ' '.join([f'0x{b:02x}' for b in data])
            logger.info(f"收到非文本数据: {hex_data}")
            print(f"收到二进制数据: {hex_data}")
            notification_responses.append(hex_data)
            notification_event.set()
    
    # 连接设备并执行OTA过程
    print(f"正在连接到设备...")
    client = None
    
    try:
        # 创建客户端
        client = BleakClient(target_address, timeout=15.0)
        
        # 尝试连接，最多3次
        connected = False
        for attempt in range(3):
            try:
                if not client.is_connected:
                    await client.connect()
                
                if client.is_connected:
                    connected = True
                    logger.info("成功连接到设备")
                    break
            except BleakError as e:
                logger.warning(f"连接尝试 {attempt+1} 失败: {str(e)}")
                if attempt < 2:
                    print(f"连接尝试失败，等待3秒后重试...")
                    await asyncio.sleep(3)
        
        # 检查连接状态
        if not connected:
            logger.error("连接失败，已达到最大尝试次数")
            print("错误: 无法连接到设备")
            save_ota_result(False, {"error": "连接设备失败"})
            return
            
        # 已成功连接到设备
        logger.info(f"已成功连接到设备")
        print(f"已成功连接到设备")
        
        # MTU协商
        # 注意: 不再固定使用500，尝试协商设备支持的最佳MTU
        try:
            # MTU设置在某些平台/设备上可能不支持，但我们尝试进行协商
            logger.info(f"尝试进行MTU协商...")
            
            # 在某些平台上可能支持MTU协商
            if hasattr(client, 'exchange_mtu') and callable(client.exchange_mtu):
                try:
                    desired_mtu = 240  # 请求240字节的MTU
                    negotiated_mtu = await client.exchange_mtu(desired_mtu)
                    logger.info(f"协商的MTU: {negotiated_mtu}")
                    print(f"协商的MTU大小: {negotiated_mtu}")
                except Exception as e:
                    logger.warning(f"MTU协商不受支持: {e}")
                    print(f"注意: MTU协商不受支持，使用默认设置")
                    negotiated_mtu = 23  # 默认值
            else:
                logger.info("当前平台不支持显式MTU协商")
                print(f"注意: 当前平台不支持显式MTU协商")
                negotiated_mtu = 23  # 默认值
        except Exception as e:
            logger.warning(f"MTU协商失败: {e}")
            print(f"注意: MTU协商未成功，使用默认设置")
            negotiated_mtu = 23  # 默认值
            
        try:
            # 发现设备上的服务和特征
            logger.info("正在发现设备上的服务和特征...")
            print("正在检查设备支持的特性...")
            
            ota_data_char = None
            available_services = {}
            available_chars = {}
            
            # 收集所有可用服务和特征
            for service in client.services:
                service_uuid = service.uuid.lower()
                logger.info(f"发现服务: {service_uuid}")
                available_services[service_uuid] = service
                
                for char in service.characteristics:
                    char_uuid = char.uuid.lower()
                    available_chars[char_uuid] = char
                    logger.info(f"  特征: {char_uuid}, 属性: {char.properties}")
                    
                    # 检查是否是我们的OTA数据特征
                    if char_uuid == CHARACTERISTIC_UUID_OTA_DATA.lower():
                        ota_data_char = char.uuid
                        logger.info(f"找到OTA数据特征: {ota_data_char}")
            
            # 如果有强制使用的特征，检查它是否存在
            if force_data_char:
                if force_data_char.lower() in available_chars:
                    ota_data_char = force_data_char
                    logger.info(f"强制使用指定的特征: {ota_data_char}")
                else:
                    logger.error(f"强制指定的特征 {force_data_char} 不存在")
                    print(f"错误: 找不到指定的特征 {force_data_char}")
                    save_ota_result(False, {"error": f"找不到指定的特征 {force_data_char}"})
                    return
            
            # 打印最终选择的特征信息
            char_obj = available_chars.get(ota_data_char.lower())
            if char_obj:
                print(f"\n已选择 {ota_data_char} 特征用于OTA数据传输")
                print(f"特征属性: {', '.join(char_obj.properties)}")
            else:
                logger.error(f"无法获取特征对象: {ota_data_char}")
                print(f"错误: 无法获取特征对象: {ota_data_char}")
                save_ota_result(False, {"error": f"无法获取特征对象: {ota_data_char}"})
                return
            
            # 确认OTA命令特征是否存在
            ota_cmd_char = None
            if CHARACTERISTIC_UUID_OTA_CMD.lower() in available_chars:
                ota_cmd_char = CHARACTERISTIC_UUID_OTA_CMD
                logger.info(f"找到OTA命令特征: {ota_cmd_char}")
            else:
                # 尝试查找任何可写特征作为OTA命令特征
                for char_uuid, char in available_chars.items():
                    props = char.properties
                    if "write" in props and char_uuid != ota_data_char.lower():
                        ota_cmd_char = char.uuid
                        logger.info(f"将使用可写特征作为OTA命令特征: {ota_cmd_char}")
                        break
                
                if not ota_cmd_char:
                    logger.info("未找到独立的OTA命令特征，将使用与OTA数据相同的特征")
                    ota_cmd_char = ota_data_char
                    print("将使用相同特征发送OTA命令和数据")
                    
            # 启用通知
            try:
                logger.info(f"启用通知: {CHARACTERISTIC_UUID_SUBSCRIBE}")
                await client.start_notify(CHARACTERISTIC_UUID_SUBSCRIBE, notification_handler)
            except Exception as e:
                logger.error(f"启用通知失败: {str(e)}")
                print(f"错误: 启用通知失败: {str(e)}")
                save_ota_result(False, {"error": f"启用通知失败: {str(e)}"})
                return
                
        except Exception as e:
            logger.error(f"发现设备上的服务和特征时出错: {e}")
            print(f"错误: 发现设备上的服务和特征时出错: {e}")
            save_ota_result(False, {"error": f"发现设备上的服务和特征时出错: {e}"})
            return
        
        print("\n===== 开始HALOW OTA升级流程 =====")
        
        # 1. 设置OTA目标为HALOW
        notification_responses.clear()
        notification_event.clear()
        logger.info("设置OTA目标为HALOW")
        print("1. 设置OTA目标为HALOW...")
        
        cmd = "DC+OTA_TARGET=HALOW_OTA"
        await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, cmd.encode())
        
        # 等待响应
        try:
            await asyncio.wait_for(notification_event.wait(), 5.0)
            notification_event.clear()
            
            if not any("find partition success" in resp for resp in notification_responses):
                logger.error("没有收到分区成功的响应")
                print("错误: 设备无法找到HALOW分区")
                save_ota_result(False, {"error": "设备无法找到HALOW分区"})
                return
            
            logger.info("成功找到HALOW分区")
            print("   找到HALOW分区成功")
        except asyncio.TimeoutError:
            logger.error("等待设置OTA目标响应超时")
            print("错误: 等待设备响应超时")
            save_ota_result(False, {"error": "设置OTA目标响应超时"})
            return
        
        # 2. 发送固件大小
        notification_responses.clear()
        notification_event.clear()
        logger.info(f"发送固件大小: {firmware_size}")
        print(f"2. 发送固件大小: {firmware_size} 字节...")
        
        cmd = f"DC+OTA_SIZE={firmware_size}"
        await client.write_gatt_char(CHARACTERISTIC_UUID_SEND_LOG, cmd.encode())
        
        # 等待响应
        try:
            await asyncio.wait_for(notification_event.wait(), 5.0)
            notification_event.clear()
            
            response_ok = False
            for resp in notification_responses:
                if f"DC+OTA_SIZE={firmware_size}" in resp:
                    response_ok = True
                    break
            
            if not response_ok:
                logger.error("设置固件大小失败")
                print("错误: 设置固件大小失败")
                save_ota_result(False, {"error": "设置固件大小失败"})
                return
            
            logger.info("设置固件大小成功")
            print("   设置固件大小成功")
        except asyncio.TimeoutError:
            logger.error("等待设置固件大小响应超时")
            print("错误: 等待设备响应超时")
            save_ota_result(False, {"error": "设置固件大小响应超时"})
            return
        
        # 3. 发送开始OTA命令
        logger.info("发送开始OTA命令")
        print("3. 发送开始OTA命令...")
        
        start_cmd = bytearray([0x00])
        await client.write_gatt_char(ota_cmd_char, start_cmd)
        
        # 等待设备就绪
        await asyncio.sleep(1)
        
        # 4. 开始传输固件数据
        print(f"开始传输固件数据，总大小: {firmware_size} 字节")
        
        # 获取特征对象
        char_obj = available_chars.get(ota_data_char.lower())
        if not char_obj:
            logger.error(f"无法获取特征对象: {ota_data_char}")
            print(f"错误: 无法获取特征对象: {ota_data_char}")
            save_ota_result(False, {"error": f"无法获取特征对象: {ota_data_char}"})
            return
        
        # 确定正确的写入方法
        use_write_without_response = "write-without-response" in char_obj.properties
        
        # 记录特征信息
        logger.info(f"使用特征 {ota_data_char} 传输数据")
        logger.info(f"特征属性: {', '.join(char_obj.properties)}")
        logger.info(f"将使用: {'write-without-response' if use_write_without_response else 'write'}")
        print(f"正在使用特征 {ota_data_char} 传输数据")
        print(f"特征属性: {', '.join(char_obj.properties)}")
        
        # 设置传输参数，降低包大小以避免错误
        chunk_size = 240  # 降低包大小到240字节
        logger.info(f"使用调整后的数据包大小: {chunk_size}字节")

        # 设置传输延迟为50ms
        delay_between_chunks = 0.05  # 50ms
        logger.info(f"使用固定传输延迟: {delay_between_chunks}秒")

        # 每10包额外延迟
        delay_interval = 10
        
        total_chunks = math.ceil(firmware_size / chunk_size)
        
        print(f"传输设置:")
        print(f"- 数据包大小: {chunk_size} 字节")
        print(f"- 总数据包数: {total_chunks}")
        print(f"- 传输间隔: {delay_between_chunks * 1000:.0f}ms")
        print(f"- 每{delay_interval}个包增加额外延迟")
        
        with tqdm(total=firmware_size, unit='B', unit_scale=True, desc="传输进度") as pbar:
            i = 0
            retry_count = 0
            max_retries = 3
            failed_chunk_size = 0
            
            while i < firmware_size:
                chunk = firmware_data[i:i+chunk_size]
                chunk_num = i // chunk_size + 1
                
                try:
                    # 根据特征支持的方法选择写入方式
                    if use_write_without_response:
                        await client.write_gatt_char(ota_data_char, chunk, response=False)
                    else:
                        await client.write_gatt_char(ota_data_char, chunk, response=True)
                        
                    pbar.update(len(chunk))
                    
                    # 每传输一定数量的块后，添加额外延迟
                    if chunk_num % delay_interval == 0:
                        await asyncio.sleep(delay_between_chunks * 3)  # 每隔一定数量的包，增加额外延迟
                    else:
                        await asyncio.sleep(delay_between_chunks)  # 标准延迟
                    
                    # 继续下一个数据块
                    i += len(chunk)
                    retry_count = 0  # 重置重试计数
                        
                except Exception as e:
                    logger.error(f"传输数据块时出错: {e}")
                    
                    # 检查是否是写入失败错误
                    if "Failed to initiate write" in str(e):
                        retry_count += 1
                        if retry_count <= max_retries:
                            logger.warning(f"尝试重试 ({retry_count}/{max_retries})...")
                            print(f"传输失败，正在重试 ({retry_count}/{max_retries})...")
                            await asyncio.sleep(1)  # 等待一会再重试
                            continue
                        
                        # 如果多次尝试失败，尝试减小包大小
                        if chunk_size > 20:
                            failed_chunk_size = chunk_size
                            # 减小包大小到原来的一半，但不小于20
                            chunk_size = max(chunk_size // 2, 20)
                            total_chunks = math.ceil((firmware_size - i) / chunk_size)
                            
                            logger.warning(f"包大小 {failed_chunk_size} 传输失败，减小到 {chunk_size}")
                            print(f"\n包大小 {failed_chunk_size} 字节传输失败，正在减小到 {chunk_size} 字节并继续...")
                            print(f"已传输: {i} 字节, 剩余: {firmware_size - i} 字节")
                            
                            retry_count = 0
                            continue
                    
                    # 如果不是写入问题或者包大小已经很小，则返回错误
                    print(f"传输失败: {e}")
                    save_ota_result(False, {"error": f"传输数据失败: {e}", "position": i})
                    return
        
        print("\n\n   固件数据传输完成")
        
        # 5. 发送结束OTA命令
        logger.info("发送结束OTA命令")
        print("5. 发送结束OTA命令...")
        
        end_cmd = bytearray([0x03])
        await client.write_gatt_char(ota_cmd_char, end_cmd)
        
        # 等待最终响应
        await asyncio.sleep(3)
        
        print("\nHALOW固件OTA升级已完成！")
        print("设备可能会在升级后重启")
        
        # 保存成功结果
        save_ota_result(True, {
            "ble_name": ble_name, 
            "firmware_size": firmware_size,
            "firmware_name": "halow_ota.bin",
            "upgrade_type": "HALOW_OTA",
            "ota_data_characteristic": ota_data_char,
            "ota_cmd_characteristic": ota_cmd_char
        })
        
    except Exception as e:
        logger.error(f"OTA过程中出现错误: {str(e)}")
        print(f"错误: OTA过程中出现错误: {str(e)}")
        save_ota_result(False, {"error": str(e)})
            
    except Exception as e:
        logger.critical(f"连接过程中发生未处理的异常: {str(e)}", exc_info=True)
        print(f"错误: 连接过程中发生异常: {str(e)}")
        save_ota_result(False, {"error": str(e)})
        
    finally:
        # 确保资源被释放
        if client and client.is_connected:
            logger.info("关闭连接...")
            try:
                await client.disconnect()
                logger.info("已断开连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {str(e)}")
                print(f"警告: 断开连接时出错: {str(e)}")

if __name__ == "__main__":
    try:
        # 打印使用说明
        print("\n===================== HALOW OTA 固件更新工具 =====================")
        print("用法: python dc_halow_ota.py [选项]")
        print("选项:")
        print("  --force-characteristic UUID : 强制使用指定的特征UUID进行数据传输")
        print("    (默认特征: 984227f3-34fc-4045-a5d0-2c581f81a153)")
        print("\n传输参数:")
        print("  - 默认数据包大小: 240字节 (自动调整)")
        print("  - 传输间隔: 50ms")
        print("  - 出错时自动减小包大小并重试")
        print("\n示例:")
        print("  python dc_halow_ota.py")
        print("  python dc_halow_ota.py --force-characteristic 984227f3-34fc-4045-a5d0-2c581f81a153")
        print("==================================================================\n")
        
        # 运行主程序
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("\n用户中止操作")
        save_ota_result(False, {"error": "用户中止操作"})
    except Exception as e:
        logger.exception("程序执行出错")
        print(f"\n错误: {str(e)}")
        save_ota_result(False, {"error": f"程序执行出错: {str(e)}"})
    finally:
        print("\nHALOW OTA 任务结束")
