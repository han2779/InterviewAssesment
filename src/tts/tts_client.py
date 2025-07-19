# -*- coding:utf-8 -*-
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import threading
import pyaudio
from io import BytesIO


class TTSClient:
    class WsParam:
        """内部参数处理类"""

        def __init__(self, app_id, api_key, api_secret, text):
            self.app_id = app_id
            self.api_key = api_key
            self.api_secret = api_secret
            self.text = text

            self.common = {"app_id": self.app_id}
            self.business = {
                "aue": "raw",
                "auf": "audio/L16;rate=16000",
                "vcn": "x4_yezi",  # 中文青年女声
                "tte": "utf8"
            }
            self.data = {
                "status": 2,
                "text": base64.b64encode(self.text.encode('utf-8')).decode()
            }

        def create_url(self):
            """生成带鉴权的WebSocket地址"""
            host = "ws-api.xfyun.cn"
            now = datetime.now()
            rfc_time = format_date_time(mktime(now.timetuple()))

            # 构造签名
            signature_origin = f"host: {host}\ndate: {rfc_time}\nGET /v2/tts HTTP/1.1"
            signature = hmac.new(
                self.api_secret.encode(),
                signature_origin.encode(),
                digestmod=hashlib.sha256
            ).digest()
            signature_base64 = base64.b64encode(signature).decode()

            # 构造授权头
            authorization = base64.b64encode(
                f'api_key="{self.api_key}", algorithm="hmac-sha256", '
                f'headers="host date request-line", signature="{signature_base64}"'
                .encode()
            ).decode()

            # 构建最终URL
            params = {"authorization": authorization, "date": rfc_time, "host": host}
            return f"wss://tts-api.xfyun.cn/v2/tts?{urlencode(params)}"

    def __init__(self, app_id, api_key, api_secret):
        """
        初始化TTS客户端
        :param app_id: 应用ID
        :param api_key: API Key
        :param api_secret: API Secret
        """
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.audio_buffer = BytesIO()
        self.audio_lock = threading.Lock()
        self._pyaudio = pyaudio.PyAudio()

    @staticmethod
    def _on_message(ws, message):
        """WebSocket消息处理器（静态方法避免循环引用）"""
        try:
            data = json.loads(message)
            code = data.get("code")
            audio = base64.b64decode(data["data"]["audio"])
            status = data["data"]["status"]

            if code != 0:
                print(f"错误 {code}: {data.get('message')}")
                ws.close()
                return

            # 写入音频数据
            tts_client = getattr(ws, 'tts_client', None)
            if tts_client:
                with tts_client.audio_lock:
                    tts_client.audio_buffer.write(audio)

                if status == 2:
                    # print("合成完成")
                    ws.close()
                    threading.Thread(
                        target=tts_client._play_audio,
                        args=(tts_client.audio_buffer.getvalue(),)
                    ).start()
                    # 清空缓冲区
                    tts_client.audio_buffer.seek(0)
                    tts_client.audio_buffer.truncate()

        except Exception as e:
            print(f"消息处理错误: {e}")

    @staticmethod
    def _on_error(ws, error):
        """错误处理器"""
        print(f"连接错误: {error}")

    @staticmethod
    def _on_open(ws):
        """连接打开处理器"""

        def send_request():
            try:
                wsParam = getattr(ws, 'wsParam', None)
                if wsParam:
                    payload = {
                        "common": wsParam.common,
                        "business": wsParam.business,
                        "data": wsParam.data
                    }
                    ws.send(json.dumps(payload))
                    # print("TTS请求已发送")
            except Exception as e:
                print(f"请求发送错误: {e}")

        threading.Thread(target=send_request).start()

    def _play_audio(self, audio_data):
        """内部播放音频方法"""
        try:
            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                output=True
            )
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            print("播放完成")
        except Exception as e:
            print(f"播放错误: {e}")

    def synthesize(self, text):
        """
        执行语音合成
        :param text: 需要合成的文本
        """
        # 准备参数
        wsParam = self.WsParam(
            self.app_id,
            self.api_key,
            self.api_secret,
            text
        )

        # 创建WebSocket连接
        ws_url = wsParam.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_open=self._on_open
        )

        # 添加自定义属性用于回调
        ws.wsParam = wsParam
        ws.tts_client = self

        # 开始连接
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def __del__(self):
        """析构函数，清理资源"""
        self._pyaudio.terminate()