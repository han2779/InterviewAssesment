from flask import request, Blueprint, jsonify
from func.generate_suggestion.suggestion_generator import suggestion
import Tools
import logging
import json
suggestion_bp = Blueprint('suggestion_bp', __name__)
# 给我json格式描述性语句
@suggestion_bp.route('/suggestion', methods=['POST'])
def suggest():
    try:
        # print("111")
        requestData = request.json
        print(requestData)
        content = requestData['problem']
        response = suggestion(content)  # 此时是字符串
        print(response)
        curTime = Tools.GetTime()
        retObj = {
            "requestTime": curTime,
            "response": response,
            "statusCode": 1
        }
        retObj = process_response(retObj)   # 字典转换为字典，但是response转换成了字典，总之 response必须是字典
        logging.info(f"[{curTime}]suggestion generation successed.")
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


def process_response(retObj):
    """
    处理包含多个aspect的response字段，返回处理后的字典

    参数:
        retObj: 原始响应字典，包含requestTime、response、statusCode字段

    返回:
        处理后的字典，其中response字段已转换为字典或字典列表
    """
    if not isinstance(retObj, dict) or 'response' not in retObj:
        return retObj  # 无效输入直接返回

    # 获取需要处理的response内容
    response_content = retObj['response']

    # 移除可能存在的```json开头和```结尾标记
    if isinstance(response_content, str):
        # 处理开头标记
        if response_content.startswith('```json'):
            response_content = response_content[7:]  # 移除```json
        # 处理结尾标记
        if response_content.endswith('```'):
            response_content = response_content[:-3]  # 移除```
        # 清除首尾空白字符
        response_content = response_content.strip()

    # 解析多个JSON对象
    try:
        # 尝试按花括号分割多个JSON对象
        objects = []
        open_braces = 0
        start_idx = 0
        content_len = len(response_content)

        for i in range(content_len):
            char = response_content[i]
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1

            # 当括号平衡且不是在起始位置时，尝试解析
            if open_braces == 0 and i > start_idx:
                json_str = response_content[start_idx:i + 1].strip()
                if json_str:  # 确保不是空字符串
                    try:
                        # 处理可能的转义字符
                        json_str = json_str.replace('\\"', '"')
                        obj = json.loads(json_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass  # 解析单个对象失败则跳过
                start_idx = i + 1

        # 根据解析结果设置response
        if len(objects) > 0:
            retObj['response'] = objects if len(objects) > 1 else objects[0]
        else:
            # 如果没有解析到多个对象，尝试整体解析
            try:
                retObj['response'] = json.loads(response_content.replace('\\"', '"'))
            except json.JSONDecodeError:
                # 保留原始内容但提示错误
                print("警告: 无法解析response内容为JSON")

    except Exception as e:
        print(f"处理response时出错: {str(e)}")

    return retObj