import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# 初始化MediaPipe面部网格和虹膜检测
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# 定义关键点索引常量
LEFT_EYE = [33, 160, 158, 133, 153, 144]  # 左眼轮廓点
RIGHT_EYE = [362, 385, 387, 263, 373, 380]  # 右眼轮廓点
MOUTH_OUTER = [78, 308]  # 嘴角外侧点
MOUTH_INNER = [13, 14]  # 唇唇内侧点
LEFT_EYEBROW = [70, 63, 105, 66]  # 左眉毛点
RIGHT_EYEBROW = [300, 293, 334, 296]  # 右眉毛点
FOREHEAD = [10, 67, 109, 338]  # 额头参考点
IRIS_LEFT = 468  # 左虹膜中心
IRIS_RIGHT = 473  # 右虹膜中心


def analyze_expression(image):
    """分析单帧图像中的面部表情"""
    # 转换图像为RGB格式
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image)

    # 如果没有检测到面部
    if not results.multi_face_landmarks:
        return {
            "expression": "normal",
            "is_smiling": False,
            "is_blinking": False,
            "eyebrow_strength": 0.0,
            "is_eye_contact": False,
            "is_frowning": False
        }

    # 获取第一个面部的关键点
    landmarks = results.multi_face_landmarks[0].landmark
    h, w, _ = image.shape

    # 1. 是否微笑 (通过嘴唇宽度变化和高度变化判断)
    mouth_left_outer = landmarks[MOUTH_OUTER[0]].x * w
    mouth_right_outer = landmarks[MOUTH_OUTER[1]].x * w
    mouth_width = abs(mouth_left_outer - mouth_right_outer)

    upper_lip = landmarks[MOUTH_INNER[0]].y * h
    lower_lip = landmarks[MOUTH_INNER[1]].y * h
    mouth_height = abs(upper_lip - lower_lip)

    is_smiling = mouth_width > 0.15 * w and mouth_height < 0.03 * h

    # 3. 眉毛活动强度
    def eyebrow_strength(eyebrow_points, forehead_points):
        # 计算眉毛中点Y坐标
        eyebrow_y = sum(landmarks[i].y for i in eyebrow_points) / len(eyebrow_points)
        # 计算额头参考点Y坐标
        forehead_y = sum(landmarks[i].y for i in forehead_points) / len(forehead_points)
        # 计算相对位移 (值越大表示眉毛抬得越高)
        return max(0, forehead_y - eyebrow_y) * 10

    left_eyebrow_str = eyebrow_strength(LEFT_EYEBROW, FOREHEAD)
    right_eyebrow_str = eyebrow_strength(RIGHT_EYEBROW, FOREHEAD)
    eyebrow_strength_avg = (left_eyebrow_str + right_eyebrow_str) / 2.0

    # 4. 是否眼神接触 (虹膜位置)
    def is_eye_contact(iris_point, eye_points):
        eye_center_x = sum(landmarks[i].x for i in eye_points) / len(eye_points)
        iris_x = landmarks[iris_point].x
        # 虹膜在眼睛中心附近
        return abs(eye_center_x - iris_x) < 0.02

    left_eye_contact = is_eye_contact(IRIS_LEFT, LEFT_EYE)
    right_eye_contact = is_eye_contact(IRIS_RIGHT, RIGHT_EYE)
    is_eye_contact = left_eye_contact and right_eye_contact

    # 5. 是否皱眉 (眉毛内聚)
    eyebrow_left_x = landmarks[LEFT_EYEBROW[0]].x
    eyebrow_right_x = landmarks[RIGHT_EYEBROW[0]].x
    eyebrow_distance = abs(eyebrow_left_x - eyebrow_right_x)
    is_frowning = eyebrow_distance < 0.15  # 值越小表示皱眉越紧

    # 6. 当前表情 (简化版)
    expression = "normal"
    if is_smiling:
        expression = "smiling"
    elif is_frowning:
        expression = "frowning"
    elif eyebrow_strength_avg > 0.4:
        expression = "surprised"

    return {
        "expression": expression,
        "is_smiling": bool(is_smiling),
        "eyebrow_strength": float(round(eyebrow_strength_avg, 2)),
        "is_eye_contact": bool(is_eye_contact),
        "is_frowning": bool(is_frowning)
    }



