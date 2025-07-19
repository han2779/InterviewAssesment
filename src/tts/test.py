from tts_client import TTSClient

# 配置您的API凭证
APP_ID = "80a17aae"
API_KEY = "bb6c27f70f73b00afe59e185f8f4c1a4"
API_SECRET = "OTkwYjQzNDU5MWQ4NzdjNzY0YjdhNWE1"

# 创建TTS客户端实例
tts_client = TTSClient(APP_ID, API_KEY, API_SECRET)

# 执行语音合成
tts_client.synthesize("你好，欢迎使用语音合成服务")