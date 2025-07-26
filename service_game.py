import asyncio
from typing import Dict, Any, List, Tuple
from config import ConfigService
from service_world import WorldService
from service_character import CharacterService, BattleSystem
from service_ai import AIService
from service_inventory import InventoryService


class GameService:
    def _get_item_display_name(self, item_id: str) -> str:
        """根据物品ID返回物品的中文显示名"""
        item_names = {
            "apple": "苹果",
            "healing_potion": "治疗药水",
            "damage_potion": "伤害药水"
        }
        return item_names.get(item_id, item_id)
    
    def _get_character_available_items(self, character_id: str) -> list:
        """获取角色可赠送的物品列表（可根据角色自定义扩展）"""
        # 示例实现：根据角色ID返回可赠送物品
        match character_id:
            case "elder":
                # 长老可以给苹果
                return ["apple"]
            case "witch":
                return ["healing_potion", "damage_potion"]
            case _:
                return []
    """游戏主服务类"""
    
    def __init__(self):
        self.config_service = ConfigService()
        self.world_service = WorldService()
        self.character_service = CharacterService()
        self.ai_service = AIService()
        self.inventory_service = InventoryService()
        self.battle_system = BattleSystem()
        self.battle_system.set_character_service(self.character_service)
        
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
        
        # 重置物品栏
        self.inventory_service = InventoryService()
        
        # 创建玩家Mob对象
        player_mob = self.character_service.create_player_mob()
        
        game_state = {
            'current_location': self.world_service.current_location,
            'player_name': '冒险者',
            'history': [],
            'game_started': True,
            'player_mob': player_mob,
            'in_battle': False,
            'battle_target': None
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
                
                # 战斗指令 - 简化版本
                case '战' | 'fight' | '挑战':
                    return self._handle_fight_command(args, game_state)
                case '逃' | 'flee' | '逃跑':
                    return self._handle_flee_command(game_state)
                
                # 物品指令 - 简化版本
                case '包' | 'bag' | 'inventory':
                    return self._handle_inventory_command()
                case '用' | 'use':
                    return self._handle_use_item_command(args, game_state)
                
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
  
战斗指令:
  战 <角色>            - 挑战角色战斗
  逃                   - 战斗中逃跑
  
物品指令:
  包                   - 查看背包
  用 <物品>            - 使用物品
  
系统指令:
  帮助 / h             - 显示此帮助
  清空                 - 清空屏幕
  状态                 - 显示游戏状态

💡 使用示例:
  看                   - 观察周围
  北                   - 向北移动  
  人                   - 看看有谁
  说 长老 你好         - 和长老打招呼
  战 村民              - 挑战村民
  包                   - 查看背包
  用 苹果              - 使用苹果

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
            # 获取角色可赠送的物品
            available_items = self._get_character_available_items(character_id)
            
            # 使用asyncio.run来运行异步函数
            ai_response = asyncio.run(self.ai_service.get_character_response(
                character_name=character.name,
                character_personality=character.personality,
                player_message=message,
                current_location=self.world_service.get_current_location().name,
                mood=character.mood,
                session_id=f"char_{character_id}",
                available_items=available_items
            ))
            
            response_text = ai_response.get("msg", "...")
            new_mood = ai_response.get("mood", character.mood)
            give_item = ai_response.get("give_item")
            
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
            
            # 处理AI决定的物品赠送
            item_result = ""
            if give_item and give_item in available_items:
                self.inventory_service.add_item(give_item, 1)
                item_name = self._get_item_display_name(give_item)
                item_result = f"\n🎁 {character.name}给了你{item_name}！"
            
            return f"🗣️ 你对{character.name}说: \"{message}\"\n\n{mood_emoji} {character.name}: \"{response_text}\"{status_info}{item_result}"
            
        except Exception as e:
            if self.config_service.is_debug_mode():
                return f"⚠️ AI服务错误: {str(e)}\n使用备用回复..."
            
            # 使用备用回复
            response = self._get_mock_ai_response(character, message)
            character.add_conversation(message, response)
            
            # 备用模式下的简单物品检查
            item_result = self._check_item_request(character_id, message)
            
            return f"🗣️ 你对{character.name}说: \"{message}\"\n\n😊 {character.name}: \"{response}\"{item_result}"
    
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
    
    def _handle_fight_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理战斗命令"""
        if not args:
            return "⚔️ 要挑战谁？\n格式: 战 <角色>\n例如: 战 村民"
        
        character_id = args[0]
        
        # 检查角色是否存在
        character = self.character_service.get_character(character_id)
        if not character:
            return f"❓ 没找到 '{character_id}'\n💡 输入 '人' 查看这里有谁"
        
        # 检查角色是否在当前位置
        current_location = self.world_service.current_location
        if character.location != current_location:
            return f"🚫 {character.name} 不在这里"
        
        # 检查角色是否可以战斗
        if not self.character_service.can_character_fight(character_id):
            refuse_message = self.character_service.get_refuse_fight_message(character_id)
            return f"🚫 {character.name}: \"{refuse_message}\""
        
        # 开始战斗
        return self._start_battle(character_id, game_state)
    
    def _handle_flee_command(self, game_state: Dict[str, Any]) -> str:
        """处理逃跑命令"""
        if not self.battle_system.battle_active:
            return "❓ 现在没有在战斗中"
        
        self.battle_system.stop_battle()
        
        # 获取当前战斗的敌人信息
        if 'current_battle_enemy' in game_state:
            enemy_id = game_state['current_battle_enemy']
            flee_message = self.character_service.get_fight_message(enemy_id, 'player_flee')
            character = self.character_service.get_character(enemy_id)
            
            # 清理战斗状态
            if 'current_battle_enemy' in game_state:
                del game_state['current_battle_enemy']
            
            return f"🏃 你逃离了战斗！\n\n😏 {character.name}: \"{flee_message}\""
        
        return "🏃 你逃离了战斗！"
    
    def _start_battle(self, enemy_id: str, game_state: Dict[str, Any]) -> str:
        """开始战斗"""
        character = self.character_service.get_character(enemy_id)
        if not character or not character.mob:
            return "❌ 战斗初始化失败"
        
        # 创建玩家Mob
        player_mob = self.character_service.create_player_mob()
        enemy_mob = character.mob
        
        # 记录当前战斗的敌人
        game_state['current_battle_enemy'] = enemy_id
        
        # 开始战斗并收集所有战斗信息
        battle_log = []
        battle_generator = self.battle_system.start_battle(player_mob, enemy_mob, character.name)
        
        result = "draw"
        try:
            while True:
                battle_text = next(battle_generator)
                battle_log.append(battle_text)
                # 如果战斗被中断，跳出循环
                if not self.battle_system.battle_active:
                    result = "player_flee"
                    break
        except StopIteration as e:
            # 生成器结束，获取返回值作为结果
            result = e.value if e.value else "draw"
        
        # 添加战斗结果消息
        if result == "player_win":
            win_message = self.character_service.get_fight_message(enemy_id, 'lose')
            battle_log.append(f"🎉 你获得了胜利！")
            battle_log.append(f"😔 {character.name}: \"{win_message}\"")
        elif result == "player_lose":
            lose_message = self.character_service.get_fight_message(enemy_id, 'win')
            battle_log.append(f"💀 你被击败了！")
            battle_log.append(f"😎 {character.name}: \"{lose_message}\"")
        elif result == "draw":
            battle_log.append(f"🤝 战斗以平局结束！")
        
        # 清理战斗状态
        if 'current_battle_enemy' in game_state:
            del game_state['current_battle_enemy']
        
        return "\n".join(battle_log)

    def _handle_fight_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理战斗命令"""
        if game_state.get('in_battle', False):
            return "🚫 你已经在战斗中了！"
        
        if len(args) < 1:
            return "💬 要挑战谁？\n格式: 战 <角色>\n例如: 战 村民"
        
        character_id = args[0]
        
        # 检查角色是否存在
        character = self.character_service.get_character(character_id)
        if not character:
            return f"❓ 没找到 '{character_id}'\n💡 输入 '人' 查看这里有谁"
        
        # 检查角色是否在当前位置
        current_location = self.world_service.current_location
        if character.location != current_location:
            return f"🚫 {character.name} 不在这里"
        
        # 检查角色是否可以战斗
        if not self.character_service.can_character_fight(character_id):
            refuse_msg = self.character_service.get_refuse_fight_message(character_id)
            return f"🚫 {character.name}: \"{refuse_msg}\""
        
        # 开始战斗
        game_state['in_battle'] = True
        game_state['battle_target'] = character_id
        
        player_mob = game_state['player_mob']
        enemy_mob = character.mob
        
        # 生成AI宣战对话
        try:
            battle_start_prompt = f"玩家向{character.name}发起了挑战，请生成一句简短的宣战回应，体现角色的性格和当前心情"
            ai_response = asyncio.run(self.ai_service.get_character_response(
                character_name=character.name,
                character_personality=character.personality,
                player_message=battle_start_prompt,
                current_location=self.world_service.get_current_location().name,
                mood=character.mood,
                session_id=f"battle_start_{character_id}",
                max_length=100
            ))
            
            battle_start_msg = ai_response.get("msg", f"{character.name}接受了你的挑战！")
            
        except Exception:
            battle_start_msg = f"{character.name}接受了你的挑战！"
        
        # 开始战斗流程
        battle_log = []
        battle_log.append(f"⚔️ 你向{character.name}发起了挑战！")
        battle_log.append(f"💬 {character.name}: \"{battle_start_msg}\"")
        battle_log.append("---")
        
        # 使用生成器进行战斗
        battle_generator = self.battle_system.start_battle(player_mob, enemy_mob, character.name)
        
        try:
            for battle_message in battle_generator:
                battle_log.append(battle_message)
                # 如果战斗结束，获取结果
                if battle_message.startswith("💀") or "被击败" in battle_message:
                    break
        except StopIteration as e:
            battle_result = e.value
        else:
            battle_result = "draw"
        
        # 处理战斗结果
        game_state['in_battle'] = False
        game_state['battle_target'] = None
        
        # 生成AI战斗结果对话
        try:
            if battle_result == "player_win":
                result_prompt = f"玩家在战斗中击败了{character.name}，请生成一句战败后的话，体现角色性格"
                result_key = "lose"
            elif battle_result == "player_lose":
                result_prompt = f"玩家在战斗中被{character.name}击败，请生成一句胜利后的话，体现角色性格"
                result_key = "win"
            else:
                result_prompt = f"玩家从与{character.name}的战斗中逃跑，请生成一句对逃跑的评价"
                result_key = "player_flee"
            
            ai_response = asyncio.run(self.ai_service.get_character_response(
                character_name=character.name,
                character_personality=character.personality,
                player_message=result_prompt,
                current_location=self.world_service.get_current_location().name,
                mood=character.mood,
                session_id=f"battle_end_{character_id}",
                max_length=100
            ))
            
            result_msg = ai_response.get("msg", self.character_service.get_fight_message(character_id, result_key))
            
        except Exception:
            result_msg = self.character_service.get_fight_message(character_id, result_key)
        
        battle_log.append("---")
        battle_log.append(f"💬 {character.name}: \"{result_msg}\"")
        
        # 根据战斗结果更新角色心情
        if battle_result == "player_win":
            character.update_mood(max(0.0, character.mood - 0.2))
        elif battle_result == "player_lose":
            character.update_mood(min(1.0, character.mood + 0.1))
        
        return "\n".join(battle_log)
    
    def _handle_flee_command(self, game_state: Dict[str, Any]) -> str:
        """处理逃跑命令"""
        if not game_state.get('in_battle', False):
            return "🚫 你不在战斗中"
        
        # 停止战斗
        self.battle_system.stop_battle()
        game_state['in_battle'] = False
        
        character_id = game_state.get('battle_target')
        if character_id:
            character = self.character_service.get_character(character_id)
            if character:
                # 生成AI逃跑对话
                try:
                    flee_prompt = f"玩家从战斗中逃跑了，请生成{character.name}对此的简短评价"
                    ai_response = asyncio.run(self.ai_service.get_character_response(
                        character_name=character.name,
                        character_personality=character.personality,
                        player_message=flee_prompt,
                        current_location=self.world_service.get_current_location().name,
                        mood=character.mood,
                        session_id=f"flee_{character_id}",
                        max_length=80
                    ))
                    
                    flee_msg = ai_response.get("msg", self.character_service.get_fight_message(character_id, "player_flee"))
                    
                except Exception:
                    flee_msg = self.character_service.get_fight_message(character_id, "player_flee")
                
                game_state['battle_target'] = None
                return f"🏃 你逃离了战斗！\n💬 {character.name}: \"{flee_msg}\""
        
        return "🏃 你逃离了战斗！"
    
    def _handle_inventory_command(self) -> str:
        """处理背包命令"""
        return self.inventory_service.get_inventory_display()
    
    def _handle_use_item_command(self, args: List[str], game_state: Dict[str, Any]) -> str:
        """处理使用物品命令"""
        if len(args) < 1:
            usable_items = self.inventory_service.get_usable_items()
            if not usable_items:
                return "🎒 背包里没有可用的物品"
            
            items_display = []
            for item_id in usable_items:
                item = self.inventory_service.get_item(item_id)
                if item:
                    count = self.inventory_service.player_inventory.get(item_id, 0)
                    items_display.append(f"  • {item.name} x{count}")
            
            return f"💡 可使用的物品:\n" + "\n".join(items_display) + "\n\n格式: 用 <物品名>"
        
        item_name = args[0]
        
        # 物品名称映射
        item_mapping = {
            "苹果": "apple",
            "治疗药水": "healing_potion", 
            "伤害药水": "damage_potion"
        }
        
        item_id = item_mapping.get(item_name, item_name)
        
        if not self.inventory_service.has_item(item_id):
            return f"🚫 你没有{item_name}"
        
        # 获取玩家状态
        player_mob = game_state.get('player_mob')
        if not player_mob:
            return "❌ 玩家状态异常"
        
        # 转换为字典格式以便物品系统使用
        player_stats = {
            "hp": player_mob.health,
            "max_hp": player_mob.max_health,
            "attack": player_mob.attack_base
        }
        
        # 使用物品
        result = self.inventory_service.use_item(item_id, player_stats, is_self=True)
        
        if result["success"]:
            # 更新玩家状态
            player_mob.health = player_stats["hp"]
            player_mob.attack_base = player_stats.get("attack", player_mob.attack_base)
            
            # 生成使用效果描述
            effects_desc = []
            for effect_type, value in result.get("effects", {}).items():
                if effect_type == "hp" and value > 0:
                    effects_desc.append(f"恢复了{value}点生命值")
                elif effect_type == "hp" and value < 0:
                    effects_desc.append(f"失去了{abs(value)}点生命值")
                elif effect_type == "damage":
                    effects_desc.append(f"受到了{value}点伤害")
                elif effect_type == "attack" and value > 0:
                    effects_desc.append(f"攻击力增加了{value}点")
            
            effect_text = "，".join(effects_desc) if effects_desc else ""
            
            return f"✅ 使用了{item_name}！{effect_text}\n❤️ 当前生命值: {player_mob.health}/{player_mob.max_health}"
        else:
            return f"❌ {result.get('message', '使用失败')}"
    
    def _check_item_request(self, character_id: str, message: str) -> str:
        """检查对话中的物品请求"""
        message_lower = message.lower()
        
        if character_id == "elder":
            # 长老可以给苹果
            food_keywords = ["饿", "食物", "吃", "苹果", "hungry", "food", "eat", "apple"]
            if any(keyword in message_lower for keyword in food_keywords):
                character = self.character_service.get_character("elder")
                if character and character.mood >= 0.4:  # 心情不错才给
                    self.inventory_service.add_item("apple", 1)
                    return "\n🎁 长老给了你一个苹果！"
                else:
                    return "\n😔 长老摇摇头：\"抱歉，我现在没有多余的食物。\""
        
        elif character_id == "witch":
            # 女巫可以给药水
            potion_keywords = ["药水", "治疗", "伤害", "毒药", "potion", "heal", "damage", "poison"]
            if any(keyword in message_lower for keyword in potion_keywords):
                character = self.character_service.get_character("witch")
                if character and character.mood >= 0.5:  # 心情好才给
                    # 根据请求类型给不同药水
                    if "治疗" in message_lower or "heal" in message_lower:
                        self.inventory_service.add_item("healing_potion", 1)
                        return "\n🎁 女巫给了你一瓶治疗药水！"
                    elif "伤害" in message_lower or "毒" in message_lower or "damage" in message_lower:
                        self.inventory_service.add_item("damage_potion", 1)
                        return "\n🎁 女巫给了你一瓶伤害药水！"
                    else:
                        # 随机给一种
                        import random
                        potion_type = random.choice(["healing_potion", "damage_potion"])
                        self.inventory_service.add_item(potion_type, 1)
                        potion_name = "治疗药水" if potion_type == "healing_potion" else "伤害药水"
                        return f"\n🎁 女巫给了你一瓶{potion_name}！"
                else:
                    return "\n😈 女巫冷笑：\"我确实有药水，但为什么要给你呢？\""
        
        return ""