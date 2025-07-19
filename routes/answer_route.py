from flask import request, Blueprint, jsonify
import Tools
import logging
from func.speech_evaluation.answer_evaluation import answer_evaluation

answer_bp = Blueprint('answer_bp', __name__)

# 给我json格式的问题和用户回答
@answer_bp.route('/answer_evaluation', methods=['POST'])
def answer_evalue():
    try:
        requestData = request.json
        response = answer_evaluation(requestData)
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 1,
            "requestTime": curTime,
            "response": response
        }
        logging.info(f"[{curTime}]answer evaluation successed.")
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


