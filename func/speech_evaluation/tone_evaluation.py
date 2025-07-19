import numpy as np
from pyaudioAnalysis import audioSegmentation as aS
from pyaudioAnalysis import audioBasicIO
from pyaudioAnalysis import ShortTermFeatures
from scipy import stats
from flask import Blueprint, request, jsonify
import os
import uuid
import logging

# 创建蓝图
intonation_bp = Blueprint('intonation_bp', __name__)


def analyze_intonation(audio_path):
    """
    分析音频语调变化
    :param audio_path: WAV音频文件路径
    :return: 包含各时间段语调特征的列表
    """
    try:
        # 读取音频文件
        [fs, x] = audioBasicIO.read_audio_file(audio_path)
        x = audioBasicIO.stereo_to_mono(x)

        # 语音活动检测 (VAD)
        segments = aS.silence_removal(
            x, fs, 0.020, 0.020,
            smooth_window=1.0,
            weight=0.3,
            plot=False
        )

        # 短时特征提取参数
        window = 0.05
        step = 0.02
        intonation_features = []

        for seg in segments:
            start = int(seg[0] * fs)
            end = int(seg[1] * fs)
            segment_x = x[start:end]

            if len(segment_x) < 1024:
                continue

            # 提取音高特征
            f, f_names = ShortTermFeatures.feature_extraction(
                segment_x, fs, window * fs, step * fs
            )

            pitch_idx = f_names.index('pitch')
            pitch = f[pitch_idx, :]
            time = np.arange(0, len(pitch)) * step + (window / 2)

            # 过滤无效音高值
            valid_mask = pitch > 0
            valid_pitch = pitch[valid_mask]
            valid_time = time[valid_mask]

            if len(valid_pitch) == 0:
                continue

            # 计算语调统计特征
            slope, _, _, _, _ = stats.linregress(
                valid_time, valid_pitch
            )

            # 构建时间段特征
            segment_features = {
                "start_time": round(seg[0], 2),
                "end_time": round(seg[1], 2),
                "duration": round(seg[1] - seg[0], 2),
                "mean_pitch": round(float(np.mean(valid_pitch)), 2),
                "pitch_std": round(float(np.std(valid_pitch)), 2),
                "pitch_min": round(float(np.min(valid_pitch)), 2),
                "pitch_max": round(float(np.max(valid_pitch)), 2),
                "trend_slope": round(float(slope * 1000), 2),  # Hz/秒
                "trend_direction": "rising" if slope > 0.0005 else "falling" if slope < -0.0005 else "stable"
            }
            intonation_features.append(segment_features)

        return intonation_features

    except Exception as e:
        logging.error(f"Audio analysis failed: {str(e)}")
        return None