import cv2
import time
from src.video_process.eye_contact import EyeContactAnalyzer
from src.video_process.emotion_analyzer import EmotionDetector
from src.video_process.eyebrow_analyzer import EyebrowAnalyzer
from src.video_process.blink_detector import BlinkDetector


class FacialExpressionAnalyzer:
    def __init__(self):
        # 初始化分析模块
        self.emotion_detector = EmotionDetector()
        self.eye_contact = EyeContactAnalyzer()
        self.eyebrow_analyzer = EyebrowAnalyzer()
        self.blink_detector = BlinkDetector()

        # 初始化统计变量
        self.reset_stats()

        # 分析状态控制
        self.is_analyzing = False
        self.start_time = None
        self.end_time = None

    def reset_stats(self):
        """重置所有统计数据"""
        self.frame_count = 0
        self.smile_count = 0
        self.results = {
            'emotion_distribution': {'neutral': 0, 'happy': 0, 'sad': 0, 'angry': 0, 'surprised': 0},
            # 'smile_frequency': 0,
            # 'eye_contact_ratio': 0,
            # 'eyebrow_intensity': 0,
            # 'blink_frequency': 0
        }

        # 重置子模块统计
        self.eye_contact.reset()
        self.eyebrow_analyzer.reset()
        self.blink_detector.reset()

    def start_analysis(self):
        """开始表情分析"""
        self.reset_stats()
        self.is_analyzing = True
        self.start_time = time.time()
        self.end_time = None
        print("表情分析已开始")

    def end_analysis(self):
        """结束表情分析"""
        if self.is_analyzing:
            self.is_analyzing = False
            self.end_time = time.time()
            print("表情分析已结束")
        else:
            print("分析尚未开始")

    def process_frame(self, frame):
        """处理单帧图像并更新统计数据（仅在分析状态下有效）"""
        if not self.is_analyzing:
            return frame

        self.frame_count += 1

        # 检测情绪
        emotion_result = self.emotion_detector.detect(frame)
        self.results['emotion_distribution'][emotion_result['dominant_emotion']] += 1

        # 检测微笑
        if emotion_result['smile_score'] > 0.7:
            self.smile_count += 1

        # 分析眼神接触
        eye_result = self.eye_contact.analyze(frame)

        # 分析眉毛活动
        eyebrow_result = self.eyebrow_analyzer.analyze(frame)

        # 检测眨眼
        blink_result = self.blink_detector.analyze(frame)

        # 返回带注释的帧用于可视化
        annotated_frame = self._annotate_frame(frame, emotion_result, eye_result, eyebrow_result)
        return annotated_frame

    def get_summary(self):
        """获取分析摘要（必须在结束分析后调用）"""
        if self.is_analyzing:
            print("警告：分析仍在进行中，请先调用 end_analysis()")
            return None

        if self.start_time is None or self.end_time is None:
            print("错误：未开始分析或未结束分析")
            return None

        # 计算分析时长
        elapsed_time = self.end_time - self.start_time

        # 计算情绪分布百分比
        total_frames = max(1, self.frame_count)
        for emotion in self.results['emotion_distribution']:
            self.results['emotion_distribution'][emotion] = round(
                self.results['emotion_distribution'][emotion] / total_frames, 2
            )

        # 计算其他指标
        minutes = max(1, elapsed_time / 60)
        self.results['微笑频率'] = round(self.smile_count / minutes, 1)
        self.results['眼神接触率'] = round(self.eye_contact.eye_contact_ratio, 2)
        self.results['眉毛活动强度'] = round(self.eyebrow_analyzer.average_intensity, 1)
        self.results['眨眼频率'] = round(self.blink_detector.blink_count / minutes, 1)

        # 添加时间信息
        self.results['经历时间'] = round(elapsed_time, 1)
        # self.results['start_time'] = self.start_time
        # self.results['end_time'] = self.end_time
        # self.results['frame_count'] = self.frame_count

        return self.results

    def _annotate_frame(self, frame, emotion, eye, eyebrow):
        """在帧上添加分析结果注释"""
        # 添加分析状态
        status = "ANALYZING" if self.is_analyzing else "IDLE"
        cv2.putText(frame, f"Status: {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加情绪标签
        cv2.putText(frame, f"Emotion: {emotion['dominant_emotion']} ({emotion['confidence']:.2f})",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加微笑检测
        cv2.putText(frame, f"Smile: {'Yes' if emotion['smile_score'] > 0.7 else 'No'}",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加眼神接触
        cv2.putText(frame, f"Eye Contact: {'Yes' if eye['contact'] else 'No'}",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加眉毛活动
        cv2.putText(frame, f"Eyebrow: {eyebrow['intensity']:.2f}",
                    (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加眨眼检测
        cv2.putText(frame, f"Blink: {'Yes' if self.blink_detector.blink_detected else 'No'}",
                    (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame
