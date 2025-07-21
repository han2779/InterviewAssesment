from flask import request, Blueprint, jsonify
import Tools
import logging
from func.first_question.first import first_ques

first_bp = Blueprint('first_bp', __name__)

# 给我json格式的问题和用户回答
@first_bp.route('/first_ques', methods=['POST'])
def question():
    try:
        requestData = request.json
        response = first_ques(requestData)
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 1,
            "requestTime": curTime,
            "response": response
        }
        logging.info(f"[{curTime}]first question successed.")
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


