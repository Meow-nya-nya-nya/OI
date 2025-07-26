"""
配置服务模块
管理游戏配置信息
"""
import os
from typing import Dict, Any

# 尝试导入配置文件
try:
    import config
except ImportError:
    config = None


class ConfigService:
    """配置服务类"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            'game_title': 'AI Chat Game',
            'game_version': '2.0.0-webcli',
            'max_response_length': 500,
            'debug_mode': False,
            'ai_provider': 'kimi',
            'api_key': '',
            'model': 'kimi-k2-0711-preview',
            'api_base_url': 'https://api.moonshot.cn/v1',
            'default_mood': 0.5,
            'session_timeout': 3600,  # 1 小时
            'server_host': '0.0.0.0',
            'server_port': 8080,
        }
        
        # 从 config.py 加载配置
        if config:
            for attr_name in dir(config):
                if not attr_name.startswith('_'):
                    attr_value = getattr(config, attr_name)
                    # 转换配置名称格式
                    config_key = attr_name.lower()
                    default_config[config_key] = attr_value
        
        # 从环境变量覆盖配置
        env_mappings = {
            'GAME_TITLE': 'game_title',
            'DEBUG_MODE': 'debug_mode',
            'AI_PROVIDER': 'ai_provider',
            'API_KEY': 'api_key',
            'MODEL': 'model',
            'API_BASE_URL': 'api_base_url',
            'SERVER_HOST': 'server_host',
            'SERVER_PORT': 'server_port',
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                # 处理布尔值
                if config_key == 'debug_mode':
                    default_config[config_key] = env_value.lower() in ('true', '1', 'yes')
                # 处理整数值
                elif config_key == 'server_port':
                    try:
                        default_config[config_key] = int(env_value)
                    except ValueError:
                        pass
                else:
                    default_config[config_key] = env_value
        
        return default_config
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def get_game_title(self) -> str:
        """获取游戏标题"""
        return self.get('game_title')
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取 AI 配置"""
        return {
            'provider': self.get('ai_provider'),
            'api_key': self.get('api_key'),
            'model': self.get('model'),
            'base_url': self.get('api_base_url'),
        }
    
    def is_debug_mode(self) -> bool:
        """是否为调试模式"""
        return self.get('debug_mode', False)
    
    def get_max_response_length(self) -> int:
        """获取最大回复长度"""
        return self.get('max_response_length', 500)
    
    def get_default_mood(self) -> float:
        """获取默认心情值"""
        return self.get('default_mood', 0.5)

