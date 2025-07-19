import cv2
import mediapipe as mp
from src.video_process import utils


class EmotionDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def detect(self, frame):
        """检测帧中的情绪"""
        results = {
            'dominant_emotion': 'neutral',
            'confidence': 0.0,
            'smile_score': 0.0,
            'emotions': {}
        }

        # 转换图像格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 处理图像
        mesh_result = self.face_mesh.process(rgb_frame)

        if mesh_result.multi_face_landmarks:
            face_landmarks = mesh_result.multi_face_landmarks[0]

            # 计算情绪
            emotion_data = utils.calculate_emotion_from_landmarks(face_landmarks.landmark)
            results['dominant_emotion'] = emotion_data['dominant_emotion']  # 主要情绪
            results['confidence'] = emotion_data['confidence']
            results['smile_score'] = emotion_data['smile_score']
            results['emotions'] = emotion_data['emotions']

        return results