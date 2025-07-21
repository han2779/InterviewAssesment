import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import time
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket


class SparkChat:
    def __init__(self, appid, api_key, api_secret, Spark_url, domain):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.Spark_url = Spark_url
        self.domain = domain
        self.answer = ""
        self.sid = ''
        self.text_list = []

    class Ws_Param:
        def __init__(self, APPID, APIKey, APISecret, Spark_url):
            self.APPID = APPID
            self.APIKey = APIKey
            self.APISecret = APISecret
            self.host = urlparse(Spark_url).netloc
            self.path = urlparse(Spark_url).path
            self.Spark_url = Spark_url

        def create_url(self):
            now = datetime.now()
            date = format_date_time(mktime(now.timetuple()))

            signature_origin = "host: " + self.host + "\n"
            signature_origin += "date: " + date + "\n"
            signature_origin += "GET " + self.path + " HTTP/1.1"

            signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                     digestmod=hashlib.sha256).digest()
            signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

            authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

            v = {
                "authorization": authorization,
                "date": date,
                "host": self.host
            }
            return self.Spark_url + '?' + urlencode(v)

    # Websocket回调函数
    def _on_error(self, ws, error):
        print("### error:", error)

    def _on_close(self, ws, one, two):
        pass

    def _on_open(self, ws):
        thread.start_new_thread(self._run, (ws,))

    def _run(self, ws, *args):
        data = json.dumps(self._gen_params())
        ws.send(data)

    def _on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            self.sid = data["header"]["sid"]
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            self.answer += content
            if status == 2:
                ws.close()

    def _gen_params(self):
        return {
            "header": {"app_id": self.appid, "uid": "1234"},
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": 0.8,
                    "max_tokens": 2048,
                    "top_k": 5,
                    "auditing": "default"
                }
            },
            "payload": {"message": {"text": self.text_list}}
        }

    def getText(self, role, content):
        self.text_list.append({"role": role, "content": content})
        self.checklen()
        return self.text_list

    def getlength(self):
        return sum(len(content["content"]) for content in self.text_list)

    def checklen(self):
        while self.getlength() > 8000 and len(self.text_list) > 0:
            self.text_list.pop(1)   # 保留系统消息

    def spark_main(self, text_list):
        self.answer = ""
        self.text_list = text_list
        self.checklen()

        wsParam = self.Ws_Param(self.appid, self.api_key, self.api_secret, self.Spark_url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()

        ws = websocket.WebSocketApp(wsUrl,
                                    on_message=lambda ws, msg: self._on_message(ws, msg),
                                    on_error=lambda ws, err: self._on_error(ws, err),
                                    on_close=lambda ws, *args: self._on_close(ws, *args),
                                    on_open=lambda ws: self._on_open(ws))
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return self.answer


# 在其他文件中使用
if __name__ == '__main__':
    # 初始化参数
    appid = "80a17aae"
    api_secret = "OTkwYjQzNDU5MWQ4NzdjNzY0YjdhNWE1"
    api_key = "bb6c27f70f73b00afe59e185f8f4c1a4"
    domain = "4.0Ultra"
    Spark_url = "wss://spark-api.xf-yun.com/v4.0/chat"

    # 创建实例
    spark_chat = SparkChat(appid, api_key, api_secret, Spark_url, domain)

    # 构造对话历史
    text_list = [
        {"role": "system", "content": "你现在扮演面试官"},
        {"role": "user", "content": "面试官您好，我已经准备好了。"}
    ]

    while True:
        # 获取回答
        response = spark_chat.spark_main(text_list)
        print("\n星火:", response)

        # 添加新对话并继续
        text_list = spark_chat.getText("assistant", response)
        user_input = input("\n" + "我:")
        text_list = spark_chat.getText("user", user_input)

