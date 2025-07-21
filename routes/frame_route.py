from flask import request, Blueprint, jsonify
import Tools
import logging
import numpy as np
import cv2
from func.frame_process.process import analyze_expression

frame_bp = Blueprint('frame_bp', __name__)

# 给我json格式的问题和用户回答
@frame_bp.route('/frame_pro', methods=['POST'])
def frame_pro():
    if 'frame' not in request.files:
        return jsonify({"error": "No frame provided"}), 400

        # 读取上传的图像文件
    file = request.files['frame']
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    curTime = Tools.GetTime()
    if image is None:
        return jsonify({"error": "Invalid image"}), 400

    # 分析表情
    response = analyze_expression(image)
    retObj = {
        "statusCode": 1,
        "requestTime": curTime,
        "response": response
    }
    logging.info(f"[{curTime}]first question successed.")
    return jsonify(response)