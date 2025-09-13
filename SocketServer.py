import os
import json
import ssl
import base64
import hashlib
import hmac
from urllib.parse import urlparse, urlencode
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from dotenv import load_dotenv

load_dotenv()

XF_APPID = os.environ.get("XF_APPID")
XF_API_KEY = os.environ.get("XF_API_KEY")
XF_API_SECRET = os.environ.get("XF_API_SECRET")

# 默认使用 4.0Ultra
DEFAULT_DOMAIN = "4.0Ultra"
# 对应 4.0Ultra 的服务地址
DEFAULT_SPARK_URL = "wss://spark-api.xf-yun.com/v4.0/chat"

class WsParam:
    def __init__(self, appid: str, api_key: str, api_secret: str, spark_url: str):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        parsed = urlparse(spark_url)
        self.host = parsed.netloc
        self.path = parsed.path
        self.Spark_url = spark_url

    def create_url(self) -> str:
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = f"host: {self.host}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET {self.path} HTTP/1.1"

        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode("utf-8")
        authorization_origin = (
            f'api_key="{self.APIKey}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            "utf-8"
        )

        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.Spark_url + "?" + urlencode(v)
        return url

def gen_params(appid: str, domain: str, messages: list[dict]):
    """
    生成与星火协议一致的请求体。
    messages 形如:
    [
      {"role":"user","content":"你好"},
      {"role":"assistant","content":"你好，有什么能帮您？"},
      ...
    ]
    """
    return {
        "header": {"app_id": appid, "uid": "web-demo"},
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.8,
                "max_tokens": 2048,
                "top_k": 5,
                "auditing": "default",
            }
        },
        "payload": {"message": {"text": messages}},
    }

def getlength(messages: list[dict]) -> int:
    length = 0
    for item in messages:
        length += len(item.get("content", ""))
    return length

def checklen(messages: list[dict], max_len: int = 3) -> list[dict]:
    # 超过最大长度就从最早的消息开始裁剪
    while len(messages) > max_len:
        if messages:
            messages.pop(1)
        else:
            break
    return messages

async def spark_stream(appid: str, api_key: str, api_secret: str, spark_url: str, domain: str, messages: list[dict]):
    """
    异步连接星火 WebSocket，发送 messages，持续接收流式响应。
    以 dict 形式逐段 yield:
      {"type":"chunk","content": "..."}  # 流式片段
      {"type":"end"}                     # 结束
      {"type":"error","message":"..."}   # 错误
    """
    ws_param = WsParam(appid, api_key, api_secret, spark_url)
    ws_url = ws_param.create_url()

    # 使用默认 SSL 配置进行证书校验（生产环境建议保留校验）
    ssl_ctx = ssl.create_default_context()

    try:
        async with websockets.connect(ws_url, ssl=ssl_ctx, ping_interval=None) as spark_ws:
            # 发起请求
            payload = gen_params(appid=appid, domain=domain, messages=messages)
            await spark_ws.send(json.dumps(payload, ensure_ascii=False))

            while True:
                try:
                    msg = await spark_ws.recv()
                except (ConnectionClosedOK, ConnectionClosedError):
                    break

                data = json.loads(msg)      # json转字典
                code = data.get("header", {}).get("code", -1)
                if code != 0:
                    yield {"type": "error", "message": f"请求错误: {code}, {data}"}
                    break

                payload_choices = data.get("payload", {}).get("choices", {})
                status = payload_choices.get("status")
                texts = payload_choices.get("text", [])
                if texts:
                    content = texts[0].get("content", "")
                    if content:
                        yield {"type": "chunk", "content": content}

                if status == 2:
                    yield {"type": "end"}
                    break
    except Exception as e:
        yield {"type": "error", "message": f"连接星火失败: {e}"}




app = FastAPI()

# 允许前端用 file:// 或其它端口访问（开发环境方便调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/chat")
async def chat_ws(
    websocket: WebSocket,
    domain: str = Query(DEFAULT_DOMAIN),
    spark_url: str = Query(DEFAULT_SPARK_URL),
):
    """
    浏览器连接此 WebSocket，即可发消息并收到流式响应。
    - 接收：前端发送 JSON {"content":"用户说的话"} 或 纯文本字符串
    - 发送：服务端将逐段返回：
        {"type":"chunk","content":"..."} // 流式内容
        {"type":"end"}                   // 一轮结束
        {"type":"error","message":"..."} // 错误
        {"type":"system","message":"..."}// 系统状态提示
    """
    await websocket.accept()
    # 每个连接独立的对话上下文
    history: list[dict] = []

    # 基础校验
    if not (XF_APPID and XF_API_KEY and XF_API_SECRET):
        await websocket.send_json({"type": "error", "message": "后端未配置 XF_APPID/KEY/SECRET"})
        await websocket.close()
        return

    await websocket.send_json({"type": "system", "message": f"已连接。domain={domain}"})
    print(f"已连接。domain={domain}")

    try:
        while True:
            try:
                recv_text = await websocket.receive_text()  # 监听前端消息
            except WebSocketDisconnect:
                break

            # 解析前端消息
            content = None
            # is_init_system = False
            try:
                obj = json.loads(recv_text)
                content = obj.get("content")
                if obj.get("action") == "reset":
                    history = history[0:1] # 只保留系统提示词
                    await websocket.send_json({"type": "system", "message": "对话已重置"})
                    print("对话已重置")
                    continue

                if obj.get("action") == "init_system" and content:
                    system_text = obj["content"]
                    history.append({"role": "system", "content": system_text})
                    print("已设置系统提示词")
                    continue

            except json.JSONDecodeError:
                # 如果不是 JSON，就按纯文本处理
                content = recv_text

            if not content:
                await websocket.send_json({"type": "error", "message": "消息内容为空"})
                continue

            # 将用户消息放入上下文并裁剪
            history.append({"role": "user", "content": content})
            history = checklen(history)

            # 调用星火，流式转发给前端
            assistant_reply = []
            async for event in spark_stream(
                appid=XF_APPID,
                api_key=XF_API_KEY,
                api_secret=XF_API_SECRET,
                spark_url=spark_url,
                domain=domain,
                messages=history,
            ):
                if event.get("type") == "chunk":
                    assistant_reply.append(event["content"])
                    await websocket.send_json(event)
                elif event.get("type") == "end":
                    await websocket.send_json({"type": "end"})
                    break
                elif event.get("type") == "error":
                    await websocket.send_json(event)
                    break

            # 将 AI 回复追加到上下文，继续支持多轮
            if assistant_reply:
                history.append({"role": "assistant", "content": "".join(assistant_reply)})
                history = checklen(history)

    except Exception as e:
            await websocket.send_json({"type": "error", "message": f"后端异常: {e}"})
    finally:
            await websocket.close()


if __name__ == "__main__":
    # 启动: python SocketServer.py
    uvicorn.run("SocketServer:app", host="0.0.0.0", port=8000, reload=False)