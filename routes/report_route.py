from flask import request, Blueprint, jsonify
from func.generate_reports.reporter import reporter
import Tools
import logging
import json
report_bp = Blueprint('report_bp', __name__)

# 给我json格式的历史记录
@report_bp.route('/report', methods=['POST'])
def report():
    try:
        requestData = request.json
        print(requestData)
        conversation_history = requestData
        response = reporter(conversation_history)
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 1,
            "requestTime": curTime,
            "response": response
        }
        print(retObj)
        retObj = process_response(retObj)
        logging.info(f"[{curTime}]Report successed.")
        print(retObj)
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


import json
import re


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

    response_content = retObj['response']

    # 预处理：移除Markdown代码块标记并去除空白
    if isinstance(response_content, str):
        # 移除```json和```标记
        response_content = re.sub(r'^```json\s*', '', response_content)
        response_content = re.sub(r'\s*```$', '', response_content)
        response_content = response_content.strip()

    # 解析策略：
    # 1. 尝试整体解析
    # 2. 尝试按分隔符分割解析
    # 3. 使用更智能的JSON边界检测
    try:
        # 策略1：整体解析
        parsed = json.loads(response_content)
        retObj['response'] = parsed
        return retObj
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        # 策略2：尝试识别多个JSON对象
        # 智能识别JSON对象边界
        json_objects = []
        current_obj = ""
        brace_count = 0
        in_quote = False
        escape_char = False

        for char in response_content:
            # 处理引号转义
            if char == '\\':
                escape_char = not escape_char
            elif char == '"' and not escape_char:
                in_quote = not in_quote
                escape_char = False
            else:
                escape_char = False

            # 计算大括号数量（只在引号外计算）
            if not in_quote:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1

            current_obj += char

            # 当检测到一个完整的JSON对象时
            if brace_count == 0 and current_obj.strip().startswith('{'):
                try:
                    json_obj = json.loads(current_obj.strip())
                    json_objects.append(json_obj)
                    current_obj = ""
                except json.JSONDecodeError:
                    # 如果无法解析，继续寻找下一个可能的JSON对象
                    pass

        # 如果找到了JSON对象，更新响应
        if json_objects:
            retObj['response'] = json_objects if len(json_objects) > 1 else json_objects[0]
            return retObj

    except Exception as e:
        print(f"处理response时出错: {str(e)}")

    # 所有解析策略失败，尝试提取最可能的JSON部分
    try:
        # 提取最外层大括号内的内容
        match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if match:
            json_str = match.group(0)
            parsed = json.loads(json_str)
            retObj['response'] = parsed
            return retObj
    except (json.JSONDecodeError, TypeError):
        pass

    # 所有解析策略失败，保留原始内容并记录警告
    print("警告: 无法解析response内容为JSON，保留原始内容")
    return retObj


# import re
# def process_response(retObj):
#     """
#     处理包含多个aspect的response字段，返回处理后的字典
#
#     参数:
#         retObj: 原始响应字典，包含requestTime、response、statusCode字段
#
#     返回:
#         处理后的字典，其中response字段已转换为字典或字典列表
#     """
#     if not isinstance(retObj, dict) or 'response' not in retObj:
#         return retObj  # 无效输入直接返回
#
#     response_content = retObj['response']
#
#     # 预处理：移除Markdown代码块标记并去除空白
#     if isinstance(response_content, str):
#         # 移除```json和```标记
#         response_content = re.sub(r'^```json\s*', '', response_content)
#         response_content = re.sub(r'\s*```$', '', response_content)
#         response_content = response_content.strip()
#
#     # 解析策略：
#     # 1. 尝试整体解析
#     # 2. 尝试按分隔符分割解析
#     # 3. 使用更智能的JSON边界检测
#     try:
#         # 策略1：整体解析
#         parsed = json.loads(response_content)
#         retObj['response'] = parsed
#         return retObj
#     except (json.JSONDecodeError, TypeError):
#         pass
#
#     try:
#         # 策略2：尝试识别多个JSON对象
#         # 智能识别JSON对象边界
#         json_objects = []
#         current_obj = ""
#         brace_count = 0
#         in_quote = False
#         escape_char = False
#
#         for char in response_content:
#             # 处理引号转义
#             if char == '\\':
#                 escape_char = not escape_char
#             elif char == '"' and not escape_char:
#                 in_quote = not in_quote
#                 escape_char = False
#             else:
#                 escape_char = False
#
#             # 计算大括号数量（只在引号外计算）
#             if not in_quote:
#                 if char == '{':
#                     brace_count += 1
#                 elif char == '}':
#                     brace_count -= 1
#
#             current_obj += char
#
#             # 当检测到一个完整的JSON对象时
#             if brace_count == 0 and current_obj.strip().startswith('{'):
#                 try:
#                     json_obj = json.loads(current_obj.strip())
#                     json_objects.append(json_obj)
#                     current_obj = ""
#                 except json.JSONDecodeError:
#                     # 如果无法解析，继续寻找下一个可能的JSON对象
#                     pass
#
#         # 如果找到了JSON对象，更新响应
#         if json_objects:
#             retObj['response'] = json_objects if len(json_objects) > 1 else json_objects[0]
#             return retObj
#
#     except Exception as e:
#         print(f"处理response时出错: {str(e)}")
#
#     # 所有解析策略失败，尝试提取最可能的JSON部分
#     try:
#         # 提取最外层大括号内的内容
#         match = re.search(r'\{.*\}', response_content, re.DOTALL)
#         if match:
#             json_str = match.group(0)
#             parsed = json.loads(json_str)
#             retObj['response'] = parsed
#             return retObj
#     except (json.JSONDecodeError, TypeError):
#         pass
#
#     # 所有解析策略失败，保留原始内容并记录警告
#     print("警告: 无法解析response内容为JSON，保留原始内容")
#     return retObj
