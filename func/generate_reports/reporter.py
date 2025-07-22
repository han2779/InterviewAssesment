from src.llm_interaction.spark_chatbot import SparkChat
import json  # 必须导入json模块

def reporter(infor):
    # 初始化参数
    with open('func/generate_reports/prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
        # 创建实例
        spark_chat = SparkChat()
        print(infor)
        # 构造对话历史 - 使用json.dumps转换字典为字符串
        text_list = [
            {"role": "system",
             "content": prompt},
            {"role": "user", "content": json.dumps(infor, ensure_ascii=False, indent=2)}
        ]
        print(text_list)
        response = spark_chat.spark_main(text_list)
        return response
