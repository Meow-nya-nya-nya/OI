import asyncio
from typing import Dict, Any, List, Tuple
from config import ConfigService
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
        return f"""🎮 欢迎来到 {self.config_service.get_game_title()}!

🧙‍♂️ 你是一位刚到达神秘世界的年轻冒险者
🌟 在这里探索世界，与AI角色对话吧！

💡 新手提示:
  • 输入 '帮助' 查看指令
  • 输入 '看' 观察周围
  • 输入 '人' 查看角色
  • 输入 '清空' 清理屏幕

---"""
    
    def process_command(self, command: str, game_state: Dict[str, Any]) -> str:
        """处理玩家命令"""
        command = command.strip().lower()

        if not command:
            return "请输入一个命令。"

        parts = command.split()
        action = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        try:
            match action:
                # 系统指令 - 简化版本
                case '清空' | '清' | 'clear':
                    return self._handle_clear_command(game_state)
                case '帮助' | '帮' | 'h' | 'help':
                    return self._get_help_message()
                case '状态' | 'status':
                    return self._handle_status_command(game_state)
                
                # 探索指令 - 简化版本  
                case '看' | 'l' | 'look':
                    return self._handle_look_command()
                case '人' | 'c' | 'chars' | '角色':
                    return self._handle_characters_command()
                
                # 移动指令 - 简化版本
                case '北' | 'n' | 'north':
                    return self._handle_direction_command('north', game_state)
                case '南' | 's' | 'south':
                    return self._handle_direction_command('south', game_state)
                case '东' | 'e' | 'east':
                    return self._handle_direction_command('east', game_state)
                case '西' | 'w' | 'west':
                    return self._handle_direction_command('west', game_state)
                case '上' | 'u' | 'up':
                    return self._handle_direction_command('up', game_state)
                case '下' | 'd' | 'down':
                    return self._handle_direction_command('down', game_state)
                
                # 对话指令 - 简化版本
                case '说' | 'talk' | 'say':
                    return self._handle_talk_command(args, game_state)
                
                # 兼容旧指令
                case 'go' | 'move' | '走' | '去':
                    return self._handle_move_command(args, game_state)
                case 'where' | '位置':
                    return self._handle_where_command()
                
                case _:
                    return f"❓ 不认识的指令: {action}\n💡 输入 '帮助' 查看可用指令"
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
        return """🎮 简化指令帮助

基础指令:
  看 / l               - 查看当前位置
  北/南/东/西          - 移动方向 (或 n/s/e/w)
  人 / c               - 查看当前位置的角色
  
对话指令:
  说 <角色> <话>       - 与角色对话
  
系统指令:
  帮助 / h             - 显示此帮助
  清空                 - 清空屏幕
  状态                 - 显示游戏状态

💡 使用示例:
  看                   - 观察周围
  北                   - 向北移动  
  人                   - 看看有谁
  说 长老 你好         - 和长老打招呼

提示: 大部分指令都有简化版本，试试单个字符！"""
    
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
            return "🚫 这里没有其他人"
        
        char_list = []
        for char_id, character in characters.items():
            mood_emoji = self._get_mood_emoji(character.mood)
            char_list.append(f"  {mood_emoji} {character.name} ({char_id})")
        
        return "👥 这里的人:\n" + "\n".join(char_list) + "\n\n💬 使用 '说 <角色> <话>' 与他们对话"
    
    def _handle_move_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理移动命令"""
        if not args:
            directions = self.world_service.get_available_directions()
            direction_names = {
                "north": "北", "south": "南",
                "east": "东", "west": "西",
                "up": "上", "down": "下"
            }
            available = [direction_names.get(d, d) for d in directions]
            return f"🧭 要去哪里？可选: {' | '.join(available)}"
        
        direction = args[0]
        success, message = self.world_service.move_to(direction)
        
        if success:
            # 更新游戏状态
            game_state['current_location'] = self.world_service.current_location
            # 返回移动信息和新位置描述
            location_desc = self.world_service.get_location_description()
            return f"🚶 {message}\n\n{location_desc}"
        else:
            return f"❌ {message}"
    
    def _handle_direction_command(self, direction: str, game_state: Dict[str, Any]) -> str:
        """处理直接方向命令"""
        return self._handle_move_command([direction], game_state)
    
    def _handle_talk_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理对话命令"""
        if len(args) < 1:
            return "💬 和谁说话？\n格式: 说 <角色> <话>\n例如: 说 长老 你好"
        
        character_id = args[0]
        message = " ".join(args[1:]) if len(args) > 1 else "你好"
        
        # 检查角色是否存在
        character = self.character_service.get_character(character_id)
        if not character:
            return f"❓ 没找到 '{character_id}'\n💡 输入 '人' 查看这里有谁"
        
        # 检查角色是否在当前位置
        current_location = self.world_service.current_location
        if character.location != current_location:
            return f"🚫 {character.name} 不在这里"
        
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
            
            # 获取心情表情
            mood_emoji = self._get_mood_emoji(new_mood)
            
            # 添加状态信息（调试模式下）
            status_info = ""
            if self.config_service.is_debug_mode():
                status = ai_response.get("status", "unknown")
                status_info = f"\n[调试: {status}, 心情: {character.mood:.2f}]"
            
            return f"🗣️ 你对{character.name}说: \"{message}\"\n\n{mood_emoji} {character.name}: \"{response_text}\"{status_info}"
            
        except Exception as e:
            if self.config_service.is_debug_mode():
                return f"⚠️ AI服务错误: {str(e)}\n使用备用回复..."
            
            # 使用备用回复
            response = self._get_mock_ai_response(character, message)
            character.add_conversation(message, response)
            return f"🗣️ 你对{character.name}说: \"{message}\"\n\n😊 {character.name}: \"{response}\""
    
    def _get_mood_emoji(self, mood: float) -> str:
        """根据心情值获取表情符号"""
        if mood >= 0.8:
            return "😊"  # 非常友好
        elif mood >= 0.6:
            return "🙂"  # 友好
        elif mood >= 0.4:
            return "😐"  # 普通
        elif mood >= 0.2:
            return "😒"  # 冷淡
        else:
            return "😠"  # 敌对
    
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
        
        return f"""📊 游戏状态:
📍 当前位置: {location.name}
👥 这里的人: {char_count}人
🎮 游戏版本: {self.config_service.get('game_version')}
📝 历史记录: {len(game_state.get('history', []))}条"""

