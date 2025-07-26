"""
AI 服务模块
基于原有 service.py 的 AI 交互逻辑，适配新的架构
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from openai import OpenAI, OpenAIError
from service_config import ConfigService


class AIService:
    """AI 服务类"""
    
    def __init__(self):
        self.config_service = ConfigService()
        self.client = None
        self.session_histories = {}  # 存储会话历史
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 AI 客户端"""
        ai_config = self.config_service.get_ai_config()
        
        try:
            client_args = {"api_key": ai_config['api_key']}
            if ai_config.get('base_url'):
                client_args["base_url"] = ai_config['base_url']
            
            self.client = OpenAI(**client_args)
            
            if self.config_service.is_debug_mode():
                print(f"AI client initialized successfully")
                print(f"   Provider: {ai_config['provider']}")
                print(f"   Model: {ai_config['model']}")
                if ai_config.get('base_url'):
                    print(f"   Endpoint: {ai_config['base_url']}")
                    
        except Exception as e:
            print(f"AI client initialization failed: {e}")
            self.client = None
    
    def _get_session_history(self, session_id: str) -> List[Dict]:
        """获取会话历史"""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []
        return self.session_histories[session_id]
    
    def _clear_session_history(self, session_id: str):
        """清空会话历史"""
        self.session_histories[session_id] = []
    
    def build_character_prompt(self, character_name: str, character_personality: str, 
                             current_location: str, mood: float) -> str:
        """构建角色系统提示词"""
        mood_level = "优秀" if mood >= 0.7 else "良好" if mood >= 0.4 else "差"
        
        prompt = f"""你现在扮演游戏角色【{character_name}】，当前心情值={mood:.2f}（{mood_level}）。

角色设定: {character_personality}

当前位置: {current_location}

你需要:
- 始终保持角色身份，以{character_name}的身份回应
- 根据心情值调整语气：越接近 0 语气越差，越接近 1 越友善
- 保持对话的趣味性和吸引力
- 在适当的时候帮助玩家
- 回复保持在 {self.config_service.get_max_response_length()} 字符以内
- 使用中文回复
- 只讨论与当前游戏场景、剧情相关的内容
- 如果玩家提出与游戏无关的问题，请礼貌地引导回游戏内容

请严格按照JSON格式返回：
{{
  "msg": "你要说的话",
  "mood": 新的心情值（0.0-1.0 之间的数字）
}}

重要：绝不透露你是 AI 或任何技术细节，始终保持角色扮演。"""
        
        return prompt
    
    async def get_character_response(self, character_name: str, character_personality: str,
                                   player_message: str, current_location: str, 
                                   mood: float, session_id: str = "default") -> Dict[str, Any]:
        """获取AI角色回复"""
        if not self.client:
            return {
                "msg": f"{character_name}看起来在思考什么，TA 似乎不想和你说话。",
                "mood": mood,
                "status": "error",
                "error": "AI 客户端未初始化"
            }
        
        try:
            # 构建系统提示词
            system_prompt = self.build_character_prompt(
                character_name, character_personality, current_location, mood
            )
            
            # 获取会话历史
            history = self._get_session_history(session_id)
            
            # 更新或添加系统消息
            if not history or history[0].get("role") != "system":
                history.insert(0, {"role": "system", "content": system_prompt})
            else:
                history[0]["content"] = system_prompt
            
            # 添加用户消息
            history.append({"role": "user", "content": player_message})
            
            # 调用AI API
            ai_config = self.config_service.get_ai_config()
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=ai_config['model'],
                messages=history,
                max_tokens=200,
                temperature=0.7,
                timeout=30
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("AI 返回空响应")
            
            content = response.choices[0].message.content.strip()
            
            # 解析JSON响应
            try:
                # 清理可能的markdown代码块标记
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                ai_response = json.loads(content)
                
                # 验证响应格式
                if "msg" not in ai_response:
                    raise ValueError("AI 响应缺少 msg 字段")
                
                # 确保mood在有效范围内
                new_mood = float(ai_response.get("mood", mood))
                new_mood = max(0.0, min(1.0, new_mood))
                
                # 添加AI回复到历史
                history.append({"role": "assistant", "content": ai_response["msg"]})
                
                # 限制历史长度
                if len(history) > 20:  # 保留系统消息 + 最近9轮对话
                    history = [history[0]] + history[-19:]
                
                return {
                    "msg": ai_response["msg"],
                    "mood": new_mood,
                    "status": "success"
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                # JSON解析失败，尝试提取纯文本回复
                if self.config_service.is_debug_mode():
                    print(f"JSON 解析失败: {e}, 原始内容: {content}")
                
                # 添加纯文本回复到历史
                history.append({"role": "assistant", "content": content})
                
                return {
                    "msg": content,
                    "mood": mood,  # 保持原心情值
                    "status": "success_text"
                }
                
        except OpenAIError as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                fallback_msg = "模型暂时不可用，请稍后再试。"
            elif "401" in error_msg or "403" in error_msg:
                fallback_msg = "API  认证失败，请检查配置。"
            elif "quota" in error_msg or "limit" in error_msg:
                fallback_msg = "API 配额已用完，请稍后再试。"
            else:
                fallback_msg = f"{character_name} 似乎在思考什么，TA 暂时无法回答你的问题。"

            if self.config_service.is_debug_mode():
                print(f"OpenAI API 错误: {e}")
            
            return {
                "msg": fallback_msg,
                "mood": mood,
                "status": "error",
                "error": str(e)
            }
            
        except Exception as e:
            if self.config_service.is_debug_mode():
                print(f"AI 服务错误: {e}")
            
            return {
                "msg": f"{character_name} 看起来有些困惑，不如等 TA 消化一下你说了什么？",
                "mood": mood,
                "status": "error",
                "error": str(e)
            }
    
    def clear_character_history(self, session_id: str = "default"):
        """清空角色对话历史"""
        self._clear_session_history(session_id)
    
    def get_session_info(self, session_id: str = "default") -> Dict[str, Any]:
        """获取会话信息"""
        history = self._get_session_history(session_id)
        return {
            "session_id": session_id,
            "message_count": len(history),
            "has_system_prompt": len(history) > 0 and history[0].get("role") == "system"
        }

