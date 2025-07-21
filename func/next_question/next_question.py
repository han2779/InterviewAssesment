from src.llm_interaction.spark_chatbot import SparkChat
import json  # 必须导入json模块

def next_ques(infor):   # infor是历史记录
    # 初始化参数
    with open('func/next_question/prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    appid = "80a17aae"
    api_secret = "OTkwYjQzNDU5MWQ4NzdjNzY0YjdhNWE1"
    api_key = "bb6c27f70f73b00afe59e185f8f4c1a4"
    domain = "4.0Ultra"
    Spark_url = "wss://spark-api.xf-yun.com/v4.0/chat"

    # 创建实例
    spark_chat = SparkChat(appid, api_key, api_secret, Spark_url, domain)

    # 构造对话历史 - 使用json.dumps转换字典为字符串
    text_list = [
        {"role": "system",
         "content": prompt},
        {"role": "user", "content":json.dumps(infor, ensure_ascii=False, indent=2)}
    ]

    response = spark_chat.spark_main(text_list)
    return response

