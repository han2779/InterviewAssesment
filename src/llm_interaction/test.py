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
        print(" ")

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
        self._checklen()
        return self.text_list

    def _getlength(self):
        return sum(len(content["content"]) for content in self.text_list)

    def _checklen(self):
        while self._getlength() > 8000 and len(self.text_list) > 0:
            self.text_list.pop(0)

    def spark_main(self, text_list):
        self.answer = ""
        self.text_list = text_list
        self._checklen()

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