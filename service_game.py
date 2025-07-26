"""
游戏主服务模块
整合各个服务模块，处理游戏逻辑
"""
import asyncio
from typing import Dict, Any, List, Tuple
from service_config import ConfigService
from service_world import WorldService
from service_character import CharacterService
from service_ai import AIService


class GameService:
    """游戏主服务类"""
    
    def __init__(self):
        self.config_service = ConfigService()
        self.world_service = WorldService()
        self.character_service = CharacterService()
        self.ai_service = AIService()
        
        # 初始化角色位置
        self._sync_character_locations()
    
    def _sync_character_locations(self):
        """同步角色位置到世界服务"""
        for char_id, character in self.character_service.get_all_characters().items():
            self.world_service.add_character_to_location(char_id, character.location)
    
    def create_new_game(self) -> Dict[str, Any]:
        """创建新游戏状态"""
        # 重置世界和角色状态
        self.world_service.reset_to_start()
        self.character_service.reset_all_moods()
        self._sync_character_locations()
        
        game_state = {
            'current_location': self.world_service.current_location,
            'player_name': '冒险者',
            'history': [],
            'game_started': True
        }
        
        # 添加欢迎信息
        welcome_msg = self._get_welcome_message()
        game_state['history'].append({
            'type': 'system',
            'content': welcome_msg
        })
        
        # 添加初始位置描述
        location_desc = self.world_service.get_location_description()
        game_state['history'].append({
            'type': 'system',
            'content': location_desc
        })
        
        return game_state
    
    def _get_welcome_message(self) -> str:
        """获取欢迎信息"""
        return f"""Welcome to {self.config_service.get_game_title()}!

You are a young adventurer who has just arrived in a mysterious realm.
Explore this world and chat with AI-driven characters!

Tip: Type 'help' to see available commands
Tip: Type 'clear' to clear the screen

---"""
    
    def process_command(self, command: str, game_state: Dict[str, Any]) -> str:
        """处理玩家命令"""
        command = command.strip().lower()
        
        if not command:
            return "请输入一个命令。"
        
        # 解析命令
        parts = command.split()
        action = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # 清空命令
            if action in ['clear', '清空', '清屏']:
                return self._handle_clear_command(game_state)
            
            # 帮助命令
            elif action in ['help', 'h', '帮助', '命令']:
                return self._get_help_message()
            
            # 查看命令
            elif action in ['look', 'l', '看', '查看', '观察']:
                return self._handle_look_command()
            
            # 位置命令
            elif action in ['where', '位置', '我在哪']:
                return self._handle_where_command()
            
            # 角色命令
            elif action in ['characters', 'chars', '角色', '人物', 'npc']:
                return self._handle_characters_command()
            
            # 移动命令
            elif action in ['go', 'move', '走', '去', '移动']:
                return self._handle_move_command(args, game_state)
            
            # 直接方向命令
            elif action in ['north', 'n', 'south', 's', 'east', 'e', 'west', 'w',
                           '北', '南', '东', '西', '上', '下', '左', '右']:
                return self._handle_direction_command(action, game_state)
            
            # 对话命令
            elif action in ['talk', 'say', '说', '聊', '对话', '交谈']:
                return self._handle_talk_command(args, game_state)
            
            # 状态命令
            elif action in ['status', 'stat', '状态']:
                return self._handle_status_command(game_state)
            
            else:
                return f"未知命令: {action}\n输入 'help' 查看可用命令。"
                
        except Exception as e:
            if self.config_service.is_debug_mode():
                return f"处理命令时出错: {str(e)}"
            else:
                return "出现了一些问题，请重试。"
    
    def _handle_clear_command(self, game_state: Dict[str, Any]) -> str:
        """处理清空命令"""
        game_state['history'] = []
        return "屏幕已清空。"
    
    def _get_help_message(self) -> str:
        """获取帮助信息"""
        return """Available Commands:

Exploration Commands:
  look / 看             - View current location
  where / 位置          - Show current location name
  go <direction> / 走 <方向>   - Move (north/south/east/west or 北/南/东/西)
  
Character Commands:
  characters / 角色     - List characters in current location
  talk <character> <message> / 说 <角色> <消息> - Chat with AI characters
  
System Commands:
  status / 状态         - Show game status
  help / 帮助           - Show this help information
  clear / 清空          - Clear screen

Examples:
  看                   - Look around
  北 or go north       - Move north
  说 elder 你好        - Greet the elder"""
    
    def _handle_look_command(self) -> str:
        """处理查看命令"""
        return self.world_service.get_location_description()
    
    def _handle_where_command(self) -> str:
        """处理位置命令"""
        location = self.world_service.get_current_location()
        return f"Current Location: {location.name}"
    
    def _handle_characters_command(self) -> str:
        """处理角色命令"""
        current_location = self.world_service.current_location
        characters = self.character_service.get_characters_in_location(current_location)
        
        if not characters:
            return "There are no other people here."
        
        char_list = []
        for char_id, character in characters.items():
            char_list.append(f"  • {character.name} (ID: {char_id}) - {character.get_description()}")
        
        return "Characters here:\n" + "\n".join(char_list) + "\n\nTip: Use 'talk <character_id> <message>' to chat with them"
    
    def _handle_move_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理移动命令"""
        if not args:
            directions = self.world_service.get_available_directions()
            direction_names = {
                "north": "北方", "south": "南方",
                "east": "东方", "west": "西方",
                "up": "上方", "down": "下方"
            }
            available = [direction_names.get(d, d) for d in directions]
            return f"去哪里？可用方向: {', '.join(available)}"
        
        direction = args[0]
        success, message = self.world_service.move_to(direction)
        
        if success:
            # 更新游戏状态
            game_state['current_location'] = self.world_service.current_location
            # 返回移动信息和新位置描述
            location_desc = self.world_service.get_location_description()
            return f"{message}\n\n{location_desc}"
        else:
            return message
    
    def _handle_direction_command(self, direction: str, game_state: Dict[str, Any]) -> str:
        """处理直接方向命令"""
        return self._handle_move_command([direction], game_state)
    
    def _handle_talk_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理对话命令"""
        if len(args) < 1:
            return "和谁说话？使用: talk <角色ID> <消息>\n或者: 说 <角色ID> <消息>"
        
        character_id = args[0]
        message = " ".join(args[1:]) if len(args) > 1 else "你好"
        
        # 检查角色是否存在
        character = self.character_service.get_character(character_id)
        if not character:
            return f"没有找到角色 '{character_id}'。\n输入 'characters' 查看当前位置的角色。"
        
        # 检查角色是否在当前位置
        current_location = self.world_service.current_location
        if character.location != current_location:
            return f"{character.name} 不在这里。"
        
        # 调用AI服务获取回复
        try:
            # 使用asyncio.run来运行异步函数
            ai_response = asyncio.run(self.ai_service.get_character_response(
                character_name=character.name,
                character_personality=character.personality,
                player_message=message,
                current_location=self.world_service.get_current_location().name,
                mood=character.mood,
                session_id=f"char_{character_id}"
            ))
            
            response_text = ai_response.get("msg", "...")
            new_mood = ai_response.get("mood", character.mood)
            
            # 更新角色心情
            character.update_mood(new_mood)
            
            # 记录对话
            character.add_conversation(message, response_text)
            
            # 添加状态信息（调试模式下）
            status_info = ""
            if self.config_service.is_debug_mode():
                status = ai_response.get("status", "unknown")
                status_info = f"\n[调试: {status}, 心情: {character.mood:.2f}]"
            
            return f"You said to {character.name}: \"{message}\"\n\n{character.name}: \"{response_text}\"{status_info}"
            
        except Exception as e:
            if self.config_service.is_debug_mode():
                return f"AI服务错误: {str(e)}\n使用备用回复..."
            
            # 使用备用回复
            response = self._get_mock_ai_response(character, message)
            character.add_conversation(message, response)
            return f"You said to {character.name}: \"{message}\"\n\n{character.name}: \"{response}\""
    
    def _get_mock_ai_response(self, character, message: str) -> str:
        """获取模拟AI回复（临时实现）"""
        responses = {
            "elder": f"年轻的冒险者，我听到你说'{message}'。村庄的智慧告诉我们，每一次交流都是学习的机会。",
            "shopkeeper": f"欢迎光临！关于'{message}'，我想我可能有些有用的东西给你。",
            "traveler": f"有趣...'{message}'让我想起了远方的一些传说...",
            "villager": f"哦，'{message}'啊，这让我想起了村里的一些事情。",
            "fisherman": f"嗯...'{message}'...就像河水一样，话语也有它的流向。"
        }
        
        return responses.get(character.character_id, f"关于'{message}'，我需要想想...")
    
    def _handle_status_command(self, game_state: Dict[str, Any]) -> str:
        """处理状态命令"""
        location = self.world_service.get_current_location()
        char_count = len(self.world_service.get_characters_in_current_location())
        
        return f"""Game Status:
Current Location: {location.name}
Characters in Location: {char_count}
Game Version: {self.config_service.get('game_version')}
History Count: {len(game_state.get('history', []))}"""

