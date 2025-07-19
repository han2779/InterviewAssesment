from real_time_ASR import RealTimeASR
import time
# 你的讯飞认证信息
APP_ID = "80a17aae"
API_KEY = "0380d7bebb6207286d1fc7bd1427062e"

# 创建客户端实例
asr_client = RealTimeASR(APP_ID, API_KEY)


# 示例使用
if __name__ == "__main__":
    asr_client.start()

    # 让转写运行30秒
    time.sleep(5)


    asr_client.stop()