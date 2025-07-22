from src.llm_interaction.spark_chatbot import SparkChat
import json  # 必须导入json模块

def first_ques(infor):      # infor是不足之处的描述性语句
    # 初始化参数
    with open('func/first_question/prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()

    # 创建实例
    spark_chat = SparkChat()
    # 构造对话历史 - 使用json.dumps转换字典为字符串
    text_list = [
        {"role": "system",
         "content": prompt},
        {"role": "user", "content": json.dumps(infor, ensure_ascii=False, indent=2)}
    ]
    response = spark_chat.spark_main(text_list)
    return response

