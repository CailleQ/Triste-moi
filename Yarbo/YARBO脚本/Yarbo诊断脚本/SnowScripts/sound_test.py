import subprocess
import threading
import time

play_mp3_done = threading.Event()
microphone_done = threading.Event()
play_output_done = threading.Event()


def sound():
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
    print(new_list)
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
        if len(config) < k:
            print(new_list[k])
        else:
            if v != config[k]:
                print(v)

    if new_list == config:
        result['success'] += '声卡配置正常'
    else:
        result['fail'] += '声卡配置异常请检查！！！'
    return result


def play_sound():
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


def mp3_thread(result):
    play_mp3_thread = threading.Thread(target=play_sound)
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


def play_output():
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


def out_put_thread(result):
    mp3_thread = threading.Thread(target=play_output)
    mp3_thread.start()
    mp3_thread.join()
    while True:
        res = input("\r是否听到录音播放，0.否，1.是")
        if res == '0':
            result['fail'] += "mp3播放失败;"
            break
        elif res == '1':
            result['success'] += "mp3播放成功;"
            break
        else:
            print(">输入有误请请重新输入")


def microphone():
    print(">麦克风测试即将开始录音...")
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


def microphone_thread():
    mp3_thread = threading.Thread(target=microphone)
    mp3_thread.start()
    mp3_thread.join()


def run_sound():
    result = {"success": '', "fail": ''}
    mp3_thread(result)
    microphone_thread()
    out_put_thread(result)
    return result


if __name__ == '__main__':
    # print(run_sound())
    print(sound())
