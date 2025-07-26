"""
游戏配置文件
"""
import os

# 游戏基本信息
GAME_TITLE = "AI Chat Game - WebCLI"
GAME_VERSION = "2.0.0-webcli"

# AI配置
AI_PROVIDER = "kimi"
API_KEY = "sk-kJo5gCMv0QKQqHfbHCdqpY5DBpqzQCrfLpHmih96HlMhr10T"  # 请替换为您的API密钥
MODEL = "kimi-k2-0711-preview"
API_BASE_URL = "https://api.moonshot.cn/v1"

# 游戏设置
MAX_RESPONSE_LENGTH = 500
DEFAULT_MOOD = 0.5
DEBUG_MODE = False

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080

# 从环境变量覆盖配置
if os.getenv("API_KEY"):
    API_KEY = os.getenv("API_KEY")

if os.getenv("DEBUG_MODE"):
    DEBUG_MODE = os.getenv("DEBUG_MODE").lower() in ("true", "1", "yes")

if os.getenv("SERVER_PORT"):
    try:
        SERVER_PORT = int(os.getenv("SERVER_PORT"))
    except ValueError:
        pass

