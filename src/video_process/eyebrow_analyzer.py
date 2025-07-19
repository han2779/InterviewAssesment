import mediapipe as mp
import numpy as np
import cv2

class EyebrowAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 统计变量
        self.intensity_history = []
        self.average_intensity = 0.0
        self.reset()

    def reset(self):
        """重置统计"""
        self.intensity_history = []
        self.average_intensity = 0.0

    def analyze(self, frame):
        """分析眉毛活动"""
        result = {'intensity': 0.0, 'movement': 'neutral'}

        # 转换图像格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 处理图像
        mesh_result = self.face_mesh.process(rgb_frame)

        if mesh_result.multi_face_landmarks:
            face_landmarks = mesh_result.multi_face_landmarks[0]

            # 获取眉毛关键点
            left_eyebrow = self._get_eyebrow_points(face_landmarks, 'left')
            right_eyebrow = self._get_eyebrow_points(face_landmarks, 'right')

            # 计算眉毛高度
            left_height = self._calculate_eyebrow_height(left_eyebrow)
            right_height = self._calculate_eyebrow_height(right_eyebrow)

            # 计算活动强度
            intensity = (left_height + right_height) / 2
            result['intensity'] = intensity

            # 更新历史记录
            self.intensity_history.append(intensity)
            if len(self.intensity_history) > 10:
                self.intensity_history.pop(0)

            # 计算平均强度
            self.average_intensity = sum(self.intensity_history) / len(self.intensity_history)

            # 判断活动类型
            if intensity > 0.05:
                result['movement'] = 'raised'
            elif intensity < -0.05:
                result['movement'] = 'lowered'

        return result

    def _get_eyebrow_points(self, landmarks, eyebrow='left'):
        """获取眉毛关键点"""
        if eyebrow == 'left':
            indices = [70, 63, 105, 66, 107]
        else:  # right eyebrow
            indices = [300, 293, 334, 296, 336]

        return [landmarks.landmark[i] for i in indices]

    def _calculate_eyebrow_height(self, eyebrow_points):
        """计算眉毛高度"""
        # 计算眉毛中心点
        center_x = sum([p.x for p in eyebrow_points]) / len(eyebrow_points)
        center_y = sum([p.y for p in eyebrow_points]) / len(eyebrow_points)

        # 计算参考点（额头位置）
        forehead_y = eyebrow_points[0].y - 0.05  # 稍微向上偏移

        # 计算高度差
        height = forehead_y - center_y

        return height