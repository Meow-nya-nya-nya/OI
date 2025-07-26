import os
import yaml
from typing import Any, Dict

def load_config() -> Dict[str, Any]:
    """从YAML文件加载配置"""
    config_file = "config.yaml"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 从环境变量覆盖配置
        if os.getenv("API_KEY"):
            config['ai']['api_key'] = os.getenv("API_KEY")
        
        if os.getenv("DEBUG_MODE"):
            config['game_settings']['debug_mode'] = os.getenv("DEBUG_MODE").lower() in ("true", "1", "yes")
        
        if os.getenv("SERVER_PORT"):
            try:
                config['server']['port'] = int(os.getenv("SERVER_PORT"))
            except ValueError:
                pass
        
        return config
        
    except FileNotFoundError:
        print(f"警告: 配置文件 {config_file} 未找到，使用默认配置")
        return _get_default_config()
    except yaml.YAMLError as e:
        print(f"警告: 配置文件格式错误: {e}，使用默认配置")
        return _get_default_config()

def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        'game': {
            'version': "2.0.0-webcli"
        },
        'ai': {
            'provider': "kimi",
            'api_key': "sk-kJo5gCMv0QKQqHfbHCdqpY5DBpqzQCrfLpHmih96HlMhr10T",
            'model': "kimi-k2-0711-preview",
            'api_base_url': "https://api.moonshot.cn/v1"
        },
        'game_settings': {
            'max_response_length': 500,
            'default_mood': 0.5,
            'debug_mode': False
        },
        'server': {
            'host': "0.0.0.0",
            'port': 8080,
            'session_timeout': 3600
        }
    }

# 加载配置
_config = load_config()

# 为了向后兼容，保留原有的常量
GAME_TITLE = "AI Chat Game - WebCLI"  # 写死在代码中
GAME_VERSION = _config['game']['version']
AI_PROVIDER = _config['ai']['provider']
API_KEY = _config['ai']['api_key']
MODEL = _config['ai']['model']
API_BASE_URL = _config['ai']['api_base_url']
MAX_RESPONSE_LENGTH = _config['game_settings']['max_response_length']
DEFAULT_MOOD = _config['game_settings']['default_mood']
DEBUG_MODE = _config['game_settings']['debug_mode']
SERVER_HOST = _config['server']['host']
SERVER_PORT = _config['server']['port']

def get_config() -> Dict[str, Any]:
    """获取完整配置字典"""
    return _config


class ConfigService:
    """配置服务类"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
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
        
        # 从全局配置加载
        yaml_config = get_config()
        # 将嵌套的YAML配置转换为扁平结构
        default_config.update({
            'game_version': yaml_config.get('game', {}).get('version', default_config['game_version']),
            'ai_provider': yaml_config.get('ai', {}).get('provider', default_config['ai_provider']),
            'api_key': yaml_config.get('ai', {}).get('api_key', default_config['api_key']),
            'model': yaml_config.get('ai', {}).get('model', default_config['model']),
            'api_base_url': yaml_config.get('ai', {}).get('api_base_url', default_config['api_base_url']),
            'max_response_length': yaml_config.get('game_settings', {}).get('max_response_length', default_config['max_response_length']),
            'default_mood': yaml_config.get('game_settings', {}).get('default_mood', default_config['default_mood']),
            'debug_mode': yaml_config.get('game_settings', {}).get('debug_mode', default_config['debug_mode']),
            'server_host': yaml_config.get('server', {}).get('host', default_config['server_host']),
            'server_port': yaml_config.get('server', {}).get('port', default_config['server_port']),
            'session_timeout': yaml_config.get('server', {}).get('session_timeout', default_config['session_timeout']),
        })
        
        # 从环境变量覆盖配置
        env_mappings = {
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
        """获取游戏标题（已废弃，标题现在写死在webcli中）"""
        return "AI Chat Game - WebCLI"
    
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

