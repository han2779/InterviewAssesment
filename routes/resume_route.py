from flask import request, Blueprint, jsonify
from func.generate_resume.resume_parser import resume_paser
import Tools
import logging
# from utils.process_resume import process_response

resume_bp = Blueprint('resume_bp', __name__)

# 给我json格式的用户基本信息
@resume_bp.route('/resume', methods=['POST'])
def resume():
    try:
        requestData = request.json
        response = resume_paser(requestData)
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 1,
            "requestTime": curTime,
            "response": response
        }
        logging.info(f"[{curTime}]Resume generation successed.")
        return jsonify(retObj)

    except Exception as e:
        curTime = Tools.GetTime()
        retObj = {
            "statusCode": 0,
            "requestTime": curTime,
            "response": str(e)
        }
        return jsonify(retObj)


