# encoding: UTF-8
import json
import requests

class SparkChat:
    def __init__(self):
        # 请替换为你的 API Key，获取地址：https://console.xfyun.cn/services/bmx1
        self.api_key = "Bearer jEufuoytHtjaCPiPhSwI:QTJzAkVfJgAupdmtBiTG"
        self.url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

    def get_answer(self, message):
        headers = {
            'Authorization': self.api_key,
            'content-type': "application/json"
        }
        body = {
            "model": "4.0Ultra",
            "user": "user_id",
            "messages": message,
            "stream": True,
            "tools": [
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_mode": "deep"
                    }
                }
            ]
        }

        full_response = ""
        isFirstContent = True

        response = requests.post(url=self.url, json=body, headers=headers, stream=True)
        for chunks in response.iter_lines():
            if chunks and '[DONE]' not in str(chunks):
                data_org = chunks[6:]  # 去除事件前缀
                try:
                    chunk = json.loads(data_org)
                    text = chunk['choices'][0]['delta']
                    if 'content' in text and text['content']:
                        content = text["content"]
                        if isFirstContent:
                            isFirstContent = False
                        full_response += content
                except json.JSONDecodeError:
                    continue  # 忽略无法解析的片段
        return full_response

    def get_text(self, text, role, content):
        text.append({"role": role, "content": content})
        return text

    def get_length(self, text):
        return sum(len(content["content"]) for content in text)

    def check_len(self, text):
        while self.get_length(text) > 11000:
            del text[0]
        return text

    def spark_main(self, chat_history):
        # 深拷贝聊天历史，避免修改原始数据
        chat_history = [dict(d) for d in chat_history]
        user_input = next((item['content'] for item in chat_history if item['role'] == 'user'), '')
        # 清除历史中的 user 和 assistant 内容，仅保留 system
        filtered_history = [item for item in chat_history if item['role'] == 'system']

        # 添加用户输入并检查长度
        self.get_text(filtered_history, "user", user_input)
        self.check_len(filtered_history)

        # 获取模型回复
        response = self.get_answer(filtered_history)
        # 添加回复到历史
        self.get_text(filtered_history, "assistant", response)

        return response