# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging
import pyaudio


class RealTimeASR():
    def __init__(self, app_id, api_key):
        # 存储配置参数
        self.app_id = app_id
        self.api_key = api_key

        # 状态控制变量
        self.keep_sending = False
        self.ws = None
        self.final_transcript = ""  # 存储最终的转写结果
        self.is_connected = False  # 标记是否已建立连接
        self.is_recording = False  # 标记是否正在录音

        # 录音设备参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1280
        self.FRAMES = self.CHUNK // 2

        # 音频设备对象
        self.p = pyaudio.PyAudio()
        self.stream = None

        # 线程对象
        self.tsend = None
        self.trecv = None

    def connect(self):
        """建立WebSocket连接（只连接一次）"""
        if self.is_connected:
            return True

        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (self.app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest().encode('utf-8')

        apiKey = self.api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa).decode('utf-8')
        self.end_tag = "{\"end\": true}"

        try:
            self.ws = create_connection(base_url + f"?appid={self.app_id}&ts={ts}&signa={quote(signa)}")
            print("WebSocket连接已建立")
            self.is_connected = True
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def start_recording(self):
        """开始录音"""
        if not self.is_connected:
            print("请先建立连接")
            return False

        if self.is_recording:
            print("已在录音中")
            return True

        # 重置状态
        self.final_transcript = ""
        self.keep_sending = True
        self.is_recording = True

        # 打开音频流
        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.FRAMES
            )
            print("开始录音...")
        except Exception as e:
            print(f"录音设备打开失败: {e}")
            self.is_recording = False
            return False

        # 启动发送线程
        self.tsend = threading.Thread(target=self.send, daemon=True)
        self.tsend.start()

        # 启动接收线程（如果未启动）
        if not self.trecv or not self.trecv.is_alive():
            self.trecv = threading.Thread(target=self.recv, daemon=True)
            self.trecv.start()

        return True

    def send(self):
        """实时采集并发送音频数据"""
        try:
            while self.keep_sending:
                # 读取音频数据
                data = self.stream.read(self.FRAMES, exception_on_overflow=False)
                # 发送音频块
                self.ws.send(data)
                # 控制发送频率
                time.sleep(0.04)
        except Exception as e:
            print(f"发送异常: {e}")
        # finally:
        #     # 发送结束标记
        #     if self.ws:
        #         self.ws.send(self.end_tag.encode('utf-8'))
        #     # 关闭录音流
        #     if self.stream:
        #         self.stream.stop_stream()
        #         self.stream.close()
        #         self.stream = None

    def extract_text(self, data_str):
        """从转写结果中提取文本内容(w参数)"""
        try:
            # 解析JSON字符串
            data_dict = json.loads(data_str)

            # 提取"w"参数的值
            if "cn" in data_dict and "st" in data_dict["cn"]:
                rt_list = data_dict["cn"]["st"].get("rt", [])
                text = ""
                for rt in rt_list:
                    for ws in rt.get("ws", []):
                        for cw in ws.get("cw", []):
                            if "w" in cw:
                                text += cw["w"]
                return text
            return ""
        except Exception as e:
            print(f"解析结果出错: {e}")
            return ""

    def recv(self):
        """接收并解析转写结果"""
        try:
            while self.is_connected and (self.keep_sending):
                result = self.ws.recv()
                if not result:
                    break

                result_dict = json.loads(result)

                # 处理不同类型的消息
                if result_dict["action"] == "started":
                    print("连接成功，准备实时转写")
                elif result_dict["action"] == "result":
                    # 提取并存储转写文本
                    data_str = result_dict.get("data", "")
                    if data_str:
                        current_text = self.extract_text(data_str)
                        # 只保留最长的结果（通常是最终结果）
                        if len(current_text) > len(self.final_transcript):
                            self.final_transcript = current_text
                elif result_dict["action"] == "error":
                    print("发生错误（语音转写）:", result_dict)
                    break

        except websocket.WebSocketConnectionClosedException:
            print("连接已关闭")
            self.is_connected = False
        except Exception as e:
            print(f"接收异常: {e}")

    def stop_recording(self):
        """停止录音并返回结果"""
        if not self.is_recording:
            print("当前未在录音")
            return None

        # 停止发送
        self.keep_sending = False
        self.is_recording = False

        # 等待发送线程结束
        if self.tsend and self.tsend.is_alive():
            self.tsend.join(timeout=2)

        # 等待0.5秒确保接收最后的结果
        time.sleep(0.5)

        # 获取最终结果
        result = self.final_transcript

        # 打印本次转写结果
        print("\n========== 本次转写结果 ==========")
        print(result)
        print("=================================")

        return result

    def close(self):
        """关闭所有连接和资源"""
        # 停止录音（如果正在录音）
        if self.is_recording:
            self.keep_sending = False
            self.is_recording = False

        # 关闭WebSocket连接
        if self.ws:
            self.ws.close()
            self.ws = None

        # 关闭音频流
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # 终止PyAudio
        self.p.terminate()

        self.is_connected = False
        print("所有资源已释放")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 请替换为您自己的APPID和APIKEY
    app_id = "80a17aae"
    api_key = "0380d7bebb6207286d1fc7bd1427062e"

    client = RealTimeASR(app_id, api_key)

    # 先建立连接
    # print("按回车建立WebSocket连接...")
    # input()
    if client.connect():
        print("连接成功！")
    else:
        print("连接失败，程序退出")
        exit()

    # 主循环：使用回车键作为开关
    while True:
        print("\n按回车开始录音")
        input()
        client.start_recording()   # 这一函数会打开音频流

        print("再按回车结束录音并获取结果...")
        input()
        result = client.stop_recording()

        # 询问用户是否继续
        # choice = input("\n继续转写？(y/n): ").lower()
        # if choice != 'y':
        #     break

    print("出循环了")
    # 关闭所有资源
    client.close()
    print("程序已退出")