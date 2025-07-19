# import numpy as np

def calculate_emotion_from_landmarks(landmarks):
    """根据面部关键点计算情绪"""
    # 提取关键点
    left_eyebrow = [landmarks[i] for i in [70, 63, 105, 66, 107]]
    right_eyebrow = [landmarks[i] for i in [300, 293, 334, 296, 336]]
    mouth = [landmarks[i] for i in [61, 291, 0, 17, 314, 402, 270]]

    # 计算情绪特征
    eyebrow_height = (sum([p.y for p in left_eyebrow]) / 5 + sum([p.y for p in right_eyebrow]) / 5) / 2
    mouth_width = abs(mouth[0].x - mouth[1].x)
    mouth_height = abs(mouth[2].y - mouth[3].y)
    smile_score = mouth_width * mouth_height * 100  # 微笑分数

    # 根据特征判断情绪
    emotions = {
        'neutral': 0.5,
        'happy': max(0, smile_score - 0.3),
        'sad': max(0, 0.4 - eyebrow_height),
        'angry': max(0, eyebrow_height - 0.6),
        'surprised': max(0, (eyebrow_height - 0.5) * 2)
    }

    # 归一化
    total = sum(emotions.values())
    for emotion in emotions:
        emotions[emotion] /= total

    # 确定主要情绪
    dominant_emotion = max(emotions, key=emotions.get)
    confidence = emotions[dominant_emotion]

    return {
        'dominant_emotion': dominant_emotion,
        'confidence': confidence,
        'smile_score': smile_score,
        'emotions': emotions
    }