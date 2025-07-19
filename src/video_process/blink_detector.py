# 这是检测眨眼频率的类。   想要拓展其它信息收集者即可在此目录中添加，方便扩展
import mediapipe as mp
import numpy as np
import cv2

class BlinkDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 状态变量
        self.blink_detected = False
        self.blink_count = 0
        self.ear_threshold = 0.25
        self.ear_history = []
        self.consecutive_frames = 0
        self.reset()

    def reset(self):
        """重置状态"""
        self.blink_detected = False
        self.blink_count = 0
        self.ear_history = []
        self.consecutive_frames = 0

    def analyze(self, frame):
        """检测眨眼"""
        result = {'blink': False, 'ear': 0.0}
        self.blink_detected = False

        # 转换图像格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 处理图像
        mesh_result = self.face_mesh.process(rgb_frame)

        if mesh_result.multi_face_landmarks:
            face_landmarks = mesh_result.multi_face_landmarks[0]

            # 获取眼睛关键点
            left_eye = self._get_eye_points(face_landmarks, 'left')
            right_eye = self._get_eye_points(face_landmarks, 'right')

            # 计算眼睛纵横比 (EAR)
            left_ear = self._calculate_ear(left_eye)
            right_ear = self._calculate_ear(right_eye)
            ear = (left_ear + right_ear) / 2.0
            result['ear'] = ear

            # 更新历史记录
            self.ear_history.append(ear)
            if len(self.ear_history) > 5:
                self.ear_history.pop(0)

            # 检测眨眼（EAR低于阈值）
            if ear < self.ear_threshold:
                self.consecutive_frames += 1
            else:
                # 如果之前是闭眼状态，且闭眼时间足够长
                if self.consecutive_frames >= 2:
                    self.blink_count += 1
                    self.blink_detected = True
                    result['blink'] = True
                self.consecutive_frames = 0

        return result

    def _get_eye_points(self, landmarks, eye='left'):
        """获取眼睛关键点"""
        if eye == 'left':
            indices = [33, 160, 158, 133, 153, 144]
        else:  # right eye
            indices = [362, 385, 387, 263, 373, 380]

        return [landmarks.landmark[i] for i in indices]

    def _calculate_ear(self, eye_points):
        """计算眼睛纵横比 (Eye Aspect Ratio)"""
        # 垂直距离
        A = np.linalg.norm(np.array([eye_points[1].x, eye_points[1].y]) -
                           np.array([eye_points[5].x, eye_points[5].y]))
        B = np.linalg.norm(np.array([eye_points[2].x, eye_points[2].y]) -
                           np.array([eye_points[4].x, eye_points[4].y]))

        # 水平距离
        C = np.linalg.norm(np.array([eye_points[0].x, eye_points[0].y]) -
                           np.array([eye_points[3].x, eye_points[3].y]))

        # 计算纵横比
        ear = (A + B) / (2.0 * C)
        return ear