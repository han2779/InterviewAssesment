from flask import request, Blueprint, jsonify
from func.generate_reports.reporter import reporter
import Tools
import logging

report_bp = Blueprint('report_bp', __name__)

# 给我json格式的历史记录
@report_bp.route('/report', methods=['POST'])
def report():
    try:
        requestData = request.json
        conversation_history = requestData
        response = reporter(conversation_history)
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 1,
            "requestTime": curTime,
            "response": response
        }
        logging.info(f"[{curTime}]Report successed.")
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


