import mediapipe as mp
import numpy as np
import cv2

class EyeContactAnalyzer:       # 分析打开摄像头到关闭摄像头这段时间内的眼触比例
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 统计变量
        self.eye_contact_frames = 0
        self.total_frames = 0
        self.eye_contact_ratio = 0.0
        self.reset()

    def reset(self):
        """重置统计"""
        self.eye_contact_frames = 0
        self.total_frames = 0
        self.eye_contact_ratio = 0.0

    def analyze(self, frame):
        """分析眼神接触"""
        result = {'contact': False, 'confidence': 0.0}
        self.total_frames += 1

        # 转换图像格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 处理图像
        mesh_result = self.face_mesh.process(rgb_frame)

        if mesh_result.multi_face_landmarks:
            face_landmarks = mesh_result.multi_face_landmarks[0]

            # 获取眼睛关键点
            left_eye = self._get_eye_points(face_landmarks, 'left')
            right_eye = self._get_eye_points(face_landmarks, 'right')

            # 计算眼睛方向
            left_direction = self._calculate_eye_direction(left_eye)
            right_direction = self._calculate_eye_direction(right_eye)

            # 判断是否直视摄像头
            if left_direction[0] > 0.6 and right_direction[0] > 0.6:
                result['contact'] = True
                result['confidence'] = (left_direction[0] + right_direction[0]) / 2
                self.eye_contact_frames += 1

            # 更新比例
            self.eye_contact_ratio = self.eye_contact_frames / self.total_frames

        return result

    def _get_eye_points(self, landmarks, eye='left'):
        """获取眼睛关键点"""
        if eye == 'left':
            indices = [33, 133, 160, 159, 158, 157, 173]
        else:  # right eye
            indices = [362, 263, 387, 386, 385, 384, 398]

        return [landmarks.landmark[i] for i in indices]

    def _calculate_eye_direction(self, eye_points):
        """计算眼睛方向"""
        # 计算眼睛中心点
        center_x = sum([p.x for p in eye_points]) / len(eye_points)
        center_y = sum([p.y for p in eye_points]) / len(eye_points)

        # 计算瞳孔位置（简化版）
        iris_x = eye_points[0].x
        iris_y = eye_points[0].y

        # 计算偏移量
        offset_x = iris_x - center_x
        offset_y = iris_y - center_y

        # 计算直视摄像头的置信度
        direct_confidence = max(0, 1 - abs(offset_x) * 3)

        return (direct_confidence, offset_x, offset_y)