from src.llm_interaction.spark_chatbot import SparkChat

def reporter(conversation_history):
    with open('func/generate_report/prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    # 初始化参数
    appid = "80a17aae"
    api_secret = "OTkwYjQzNDU5MWQ4NzdjNzY0YjdhNWE1"
    api_key = "bb6c27f70f73b00afe59e185f8f4c1a4"
    domain = "4.0Ultra"
    Spark_url = "wss://spark-api.xf-yun.com/v4.0/chat"

    # 创建实例
    spark_chat = SparkChat(appid, api_key, api_secret, Spark_url, domain)

    conversation_history.append({
        "role": "user",
        "content": prompt
    })

    # 获取回答
    response = spark_chat.spark_main(conversation_history)

    return response
