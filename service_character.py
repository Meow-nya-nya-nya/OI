from typing import Dict, Any, List, Optional, Generator, Tuple
import json
import os
import time
import random
from config import ConfigService

class Mob:
    def __init__(self, name: str, health: int, attack_base: int, physical: int, magical: int, attack_speed: int, defense: int):
        # physical magical 一般在 100 上下，乘以 attack_base 得到攻击力
        self.name = name
        self.max_health = health
        self.health = health
        self.attack_base = attack_base
        self.physical = physical
        self.magical = magical
        self.attack_speed = attack_speed
        self.defense = defense
    
    def reset_health(self):
        """重置血量"""
        self.health = self.max_health
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.health > 0
    
    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际伤害值"""
        actual_damage = min(damage, self.health)
        self.health -= actual_damage
        return actual_damage
    
    def decide_attack_type(self) -> str:
        """决定攻击类型"""
        # 根据物理和魔法属性决定攻击类型
        if self.physical > self.magical:
            return 'physical'
        elif self.magical > self.physical:
            return 'magical'
        else:
            # 如果相等，随机选择
            import random
            return random.choice(['physical', 'magical'])
    
    def calculate_damage(self, target: 'Mob', attack_type: str) -> Tuple[int, bool, bool]:
        """计算对目标的伤害，返回(伤害值, 是否暴击, 是否防御成功)"""
        # 基础伤害计算
        if attack_type == 'physical':
            base_damage = (self.physical * self.attack_base) // 100
        else:  # magical
            base_damage = (self.magical * self.attack_base) // 100
        
        # 添加随机性 (±20%)
        damage_variance = random.uniform(0.8, 1.2)
        raw_damage = int(base_damage * damage_variance)
        
        # 暴击判定 (15%概率)
        is_critical = random.random() < 0.15
        if is_critical:
            raw_damage = int(raw_damage * 1.5)
        
        # 防御判定 (defense作为成功概率0-100)
        defense_success = random.randint(1, 100) <= target.defense
        
        if defense_success:
            # 防御成功，减少伤害
            # 最高抵消 min(attack_base * 0.4, raw_damage * 0.4)
            max_reduction = min(self.attack_base * 0.4, raw_damage * 0.4)
            damage_reduction = random.uniform(0.2, max_reduction)
            final_damage = max(1, int(raw_damage - damage_reduction))
        else:
            final_damage = raw_damage
        
        # 确保至少造成1点伤害
        final_damage = max(1, final_damage)
        
        return final_damage, is_critical, defense_success
    
    def get_health_percentage(self) -> float:
        """获取血量百分比"""
        return self.health / self.max_health if self.max_health > 0 else 0
    
    def __repr__(self):
        return self.name
    
class Character:
    """角色类"""
    
    def __init__(self, character_id: str, name: str, personality: str, 
                 location: str, mood: float = None, mob: Mob = None):
        self.character_id = character_id
        self.name = name
        self.personality = personality
        self.location = location
        self.mood = mood or ConfigService().get_default_mood()
        self.conversation_history = []
        self.mob = mob  # 战斗数值
        self.can_fight = mob is not None  # 是否可以战斗
    
    def add_conversation(self, user_message: str, ai_response: str, history_limit: int = 10):
        """添加对话记录"""
        self.conversation_history.append({
            'user': user_message,
            'ai': ai_response
        })
        
        # 限制历史记录长度，避免内存过度使用
        if len(self.conversation_history) > history_limit:
            self.conversation_history = self.conversation_history[-history_limit:]
    
    def get_conversation_context(self, context_limit: int = 3) -> str:
        """获取对话上下文"""
        if not self.conversation_history:
            return ""
        
        context_lines = []
        for conv in self.conversation_history[-context_limit:]:  # 只取最近几轮对话
            context_lines.append(f"玩家: {conv['user']}")
            context_lines.append(f"{self.name}: {conv['ai']}")
        
        return "\n".join(context_lines)
    
    def get_description(self, mood_descriptions: Dict[str, str] = None) -> str:
        """获取角色描述"""
        mood_desc = self._get_mood_description(mood_descriptions)
        return f"{self.name} ({mood_desc})"
    
    def _get_mood_description(self, mood_descriptions: Dict[str, str] = None) -> str:
        """获取心情描述"""
        if mood_descriptions:
            # 使用外部提供的心情描述映射
            mood_thresholds = [0.8, 0.6, 0.4, 0.2, 0.0]
            for threshold in mood_thresholds:
                if self.mood >= threshold:
                    return mood_descriptions.get(str(threshold), "普通")
            return mood_descriptions.get("0.0", "敌对")
        else:
            # 使用默认的心情描述
            if self.mood >= 0.8:
                return "非常友好"
            elif self.mood >= 0.6:
                return "友好"
            elif self.mood >= 0.4:
                return "普通"
            elif self.mood >= 0.2:
                return "冷淡"
            else:
                return "敌对"
    
    def update_mood(self, new_mood: float):
        """更新心情值"""
        self.mood = max(0.0, min(1.0, new_mood))  # 确保在 0-1 范围内


class CharacterService:
    """角色管理服务类"""
    
    def __init__(self):
        self.characters = {}
        self.mood_descriptions = {}
        self.conversation_history_limit = 10
        self.context_conversation_limit = 3
        self._initialize_characters()
        
        # 尝试导入AI服务用于战斗对话
        try:
            from service_ai import AIService
            self.ai_service = AIService()
            self.ai_available = True
        except ImportError:
            self.ai_service = None
            self.ai_available = False
    
    def _initialize_characters(self):
        """从JSON文件初始化游戏角色"""
        role_file = os.path.join("worlds", "role.json")
        
        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                role_data = json.load(f)
            
            # 加载配置参数
            self.mood_descriptions = role_data.get("mood_descriptions", {})
            self.conversation_history_limit = role_data.get("conversation_history_limit", 10)
            self.context_conversation_limit = role_data.get("context_conversation_limit", 3)
            self.player_stats = role_data.get("player_stats", {})
            
            # 加载角色数据
            characters_data = role_data.get("characters", {})
            for character_id, character_info in characters_data.items():
                # 创建Mob对象（如果角色可以战斗）
                mob = None
                if character_info.get("can_fight", False) and "mob_stats" in character_info:
                    stats = character_info["mob_stats"]
                    mob = Mob(
                        name=character_info["name"],
                        health=stats["health"],
                        attack_base=stats["attack_base"],
                        physical=stats["physical"],
                        magical=stats["magical"],
                        attack_speed=stats["attack_speed"],
                        defense=stats["defense"]
                    )
                
                character = Character(
                    character_id=character_info["character_id"],
                    name=character_info["name"],
                    personality=character_info["personality"],
                    location=character_info["location"],
                    mood=character_info.get("mood", 0.5),
                    mob=mob
                )
                
                # 添加战斗相关属性
                character.can_fight = character_info.get("can_fight", False)
                character.refuse_fight_message = character_info.get("refuse_fight_message", "")
                character.fight_messages = character_info.get("fight_messages", {})
                
                self.characters[character_id] = character
                
        except FileNotFoundError:
            print(f"警告: 角色文件 {role_file} 未找到，使用默认角色")
            self._create_default_characters()
        except json.JSONDecodeError as e:
            print(f"警告: 角色文件格式错误: {e}，使用默认角色")
            self._create_default_characters()
    
    def _create_default_characters(self):
        """创建默认角色（备用方案）"""
        self.mood_descriptions = {
            "0.8": "非常友好", "0.6": "友好", "0.4": "普通",
            "0.2": "冷淡", "0.0": "敌对"
        }
        self.conversation_history_limit = 10
        self.context_conversation_limit = 3
        
        self.characters["elder"] = Character(
            character_id="elder",
            name="村庄长老",
            personality="智慧而和蔼的老人。",
            location="village_center",
            mood=0.7
        )
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """获取指定角色"""
        return self.characters.get(character_id)
    
    def get_characters_in_location(self, location: str) -> Dict[str, Character]:
        """获取指定位置的所有角色"""
        return {
            char_id: char for char_id, char in self.characters.items()
            if char.location == location
        }
    
    def get_all_characters(self) -> Dict[str, Character]:
        """获取所有角色"""
        return self.characters.copy()
    
    def add_character(self, character: Character):
        """添加新角色"""
        self.characters[character.character_id] = character
    
    def remove_character(self, character_id: str):
        """移除角色"""
        if character_id in self.characters:
            del self.characters[character_id]
    
    def move_character(self, character_id: str, new_location: str):
        """移动角色到新位置"""
        if character_id in self.characters:
            self.characters[character_id].location = new_location
    
    def update_character_mood(self, character_id: str, new_mood: float):
        """更新角色心情"""
        if character_id in self.characters:
            self.characters[character_id].update_mood(new_mood)
    
    def get_character_list_for_location(self, location: str) -> List[str]:
        """获取指定位置的角色 ID 列表"""
        return [
            char_id for char_id, char in self.characters.items()
            if char.location == location
        ]
    
    def reset_all_moods(self):
        """重置所有角色的心情值"""
        default_mood = ConfigService().get_default_mood()
        for character in self.characters.values():
            character.mood = default_mood
            character.conversation_history = []
    
    def add_character_conversation(self, character_id: str, user_message: str, ai_response: str):
        """为指定角色添加对话记录"""
        if character_id in self.characters:
            self.characters[character_id].add_conversation(
                user_message, ai_response, self.conversation_history_limit
            )
    
    def get_character_context(self, character_id: str) -> str:
        """获取指定角色的对话上下文"""
        if character_id in self.characters:
            return self.characters[character_id].get_conversation_context(
                self.context_conversation_limit
            )
        return ""
    
    def get_mood_description(self, mood: float) -> str:
        """根据心情值获取描述"""
        # 找到最接近的心情描述
        mood_thresholds = [0.8, 0.6, 0.4, 0.2, 0.0]
        for threshold in mood_thresholds:
            if mood >= threshold:
                return self.mood_descriptions.get(str(threshold), "普通")
        return self.mood_descriptions.get("0.0", "敌对")
    
    def get_character_description(self, character_id: str) -> str:
        """获取角色描述（包含正确的心情描述）"""
        if character_id in self.characters:
            return self.characters[character_id].get_description(self.mood_descriptions)
        return "未知角色"
    
    def _generate_battle_dialogue(self, attacker_name: str, defender_name: str, 
                                attack_type: str, is_critical: bool, defense_success: bool, damage: int) -> str:
        """生成战斗对话"""
        if not self.ai_available:
            return self._get_fallback_battle_dialogue(attacker_name, defender_name, attack_type, is_critical, defense_success)
        
        try:
            # 构建战斗情况描述
            situation = f"{attacker_name}对{defender_name}进行了{'物理' if attack_type == 'physical' else '魔法'}攻击"
            if is_critical:
                situation += "，造成了暴击"
            if defense_success:
                situation += f"，但{defender_name}成功防御了部分伤害"
            situation += f"，最终造成{damage}点伤害"
            
            # 使用AI生成简短的战斗对话
            import asyncio
            ai_response = asyncio.run(self.ai_service.get_character_response(
                character_name=attacker_name,
                character_personality="战斗中的角色，会说一些简短的战斗台词",
                player_message=situation,
                current_location="战斗中",
                mood=0.5,
                session_id=f"battle_{attacker_name}",
                max_length=50  # 限制长度
            ))
            
            dialogue = ai_response.get("msg", "").strip()
            # 确保对话不会太长
            if len(dialogue) > 100:
                dialogue = dialogue[:97] + "..."
            
            return f"{attacker_name}: \"{dialogue}\""
            
        except Exception:
            # AI生成失败，使用备用对话
            return self._get_fallback_battle_dialogue(attacker_name, defender_name, attack_type, is_critical, defense_success)
    
    def _get_fallback_battle_dialogue(self, attacker_name: str, defender_name: str, 
                                    attack_type: str, is_critical: bool, defense_success: bool) -> str:
        """获取备用战斗对话"""
        dialogues = []
        
        if is_critical:
            dialogues.extend([
                f"{attacker_name}: \"这就是我的真正实力！\"",
                f"{attacker_name}: \"完美的一击！\"",
                f"{attacker_name}: \"看我的绝招！\""
            ])
        elif defense_success:
            dialogues.extend([
                f"{defender_name}: \"我不会轻易倒下的！\"",
                f"{defender_name}: \"还不够！\"",
                f"{attacker_name}: \"竟然被挡住了...\"",
            ])
        else:
            if attack_type == "physical":
                dialogues.extend([
                    f"{attacker_name}: \"尝尝我的拳头！\"",
                    f"{attacker_name}: \"接招吧！\"",
                    f"{defender_name}: \"好痛...\"",
                ])
            else:
                dialogues.extend([
                    f"{attacker_name}: \"魔法的力量！\"",
                    f"{attacker_name}: \"感受魔法的威力！\"",
                    f"{defender_name}: \"这股魔力...\"",
                ])
        
        return random.choice(dialogues) if dialogues else ""
    
    def create_player_mob(self) -> Mob:
        """创建玩家的Mob对象"""
        stats = self.player_stats
        return Mob(
            name="冒险者",
            health=stats.get("health", 100),
            attack_base=stats.get("attack_base", 100),
            physical=stats.get("physical", 80),
            magical=stats.get("magical", 50),
            attack_speed=stats.get("attack_speed", 65),
            defense=stats.get("defense", 18)
        )
    
    def can_character_fight(self, character_id: str) -> bool:
        """检查角色是否可以战斗"""
        character = self.get_character(character_id)
        return character and character.can_fight
    
    def get_refuse_fight_message(self, character_id: str) -> str:
        """获取角色拒绝战斗的消息"""
        character = self.get_character(character_id)
        if character and hasattr(character, 'refuse_fight_message'):
            return character.refuse_fight_message
        return "这个角色不想与你战斗。"
    
    def get_fight_message(self, character_id: str, result: str) -> str:
        """获取战斗结果消息"""
        character = self.get_character(character_id)
        if character and hasattr(character, 'fight_messages'):
            return character.fight_messages.get(result, "...")
        return "..."


class BattleSystem:
    """战斗系统类"""
    
    def __init__(self):
        self.battle_active = False
        self.current_battle = None
        # 初始化角色服务以使用AI对话生成
        self.character_service = None
    
    def set_character_service(self, character_service):
        """设置角色服务引用"""
        self.character_service = character_service
    
    def start_battle(self, player_mob: Mob, enemy_mob: Mob, enemy_name: str) -> Generator[str, None, str]:
        """开始战斗，返回战斗过程的生成器"""
        self.battle_active = True
        
        # 重置双方血量
        player_mob.reset_health()
        enemy_mob.reset_health()
        
        yield f"⚔️ 战斗开始！{player_mob.name} VS {enemy_mob.name}"
        yield f"💪 {player_mob.name}: HP {player_mob.health}/{player_mob.max_health}"
        yield f"💪 {enemy_mob.name}: HP {enemy_mob.health}/{enemy_mob.max_health}"
        yield "---"
        
        # 决定先手
        if player_mob.attack_speed >= enemy_mob.attack_speed:
            yield f"⚡ {player_mob.name} 速度更快，先手攻击！"
            first_attacker, first_defender = player_mob, enemy_mob
            first_is_player = True
        else:
            yield f"⚡ {enemy_mob.name} 速度更快，先手攻击！"
            first_attacker, first_defender = enemy_mob, player_mob
            first_is_player = False
        
        yield "---"
        
        round_count = 1
        while player_mob.is_alive() and enemy_mob.is_alive() and self.battle_active:
            yield f"🔄 第 {round_count} 回合"
            
            # 第一个攻击者
            if self.battle_active:
                attack_type = first_attacker.decide_attack_type()
                damage, is_critical, defense_success = first_attacker.calculate_damage(first_defender, attack_type)
                actual_damage = first_defender.take_damage(damage)
                
                # 生成战斗描述
                attack_emoji = "👊" if attack_type == "physical" else "✨"
                attack_desc = "物理攻击" if attack_type == "physical" else "魔法攻击"
                
                yield f"{attack_emoji} {first_attacker.name} 使用{attack_desc}！"
                
                # 添加战斗细节
                if is_critical:
                    yield f"💥 暴击！造成额外伤害！"
                if defense_success:
                    yield f"🛡️ {first_defender.name} 成功防御，减少了部分伤害！"
                
                yield f"💥 对 {first_defender.name} 造成 {actual_damage} 点伤害！"
                yield f"❤️ {first_defender.name}: HP {first_defender.health}/{first_defender.max_health}"
                
                # 尝试生成AI战斗对话
                if self.character_service:
                    battle_dialogue = self.character_service._generate_battle_dialogue(first_attacker.name, first_defender.name, 
                                                                   attack_type, is_critical, defense_success, actual_damage)
                    if battle_dialogue:
                        yield f"💬 {battle_dialogue}"
                
                if not first_defender.is_alive():
                    if first_is_player:
                        yield f"💀 {enemy_mob.name} 被击败了！"
                        return "player_win"
                    else:
                        yield f"💀 {player_mob.name} 被击败了！"
                        return "player_lose"
            
            # 第二个攻击者
            if self.battle_active and player_mob.is_alive() and enemy_mob.is_alive():
                second_attacker = enemy_mob if first_is_player else player_mob
                second_defender = player_mob if first_is_player else enemy_mob
                
                attack_type = second_attacker.decide_attack_type()
                damage, is_critical, defense_success = second_attacker.calculate_damage(second_defender, attack_type)
                actual_damage = second_defender.take_damage(damage)
                
                # 生成战斗描述
                attack_emoji = "👊" if attack_type == "physical" else "✨"
                attack_desc = "物理攻击" if attack_type == "physical" else "魔法攻击"
                
                yield f"{attack_emoji} {second_attacker.name} 使用{attack_desc}！"
                
                # 添加战斗细节
                if is_critical:
                    yield f"💥 暴击！造成额外伤害！"
                if defense_success:
                    yield f"🛡️ {second_defender.name} 成功防御，减少了部分伤害！"
                
                yield f"💥 对 {second_defender.name} 造成 {actual_damage} 点伤害！"
                yield f"❤️ {second_defender.name}: HP {second_defender.health}/{second_defender.max_health}"
                
                # 尝试生成AI战斗对话
                if self.character_service:
                    battle_dialogue = self.character_service._generate_battle_dialogue(second_attacker.name, second_defender.name, 
                                                                   attack_type, is_critical, defense_success, actual_damage)
                    if battle_dialogue:
                        yield f"💬 {battle_dialogue}"
                
                if not second_defender.is_alive():
                    if first_is_player:
                        yield f"💀 {player_mob.name} 被击败了！"
                        return "player_lose"
                    else:
                        yield f"💀 {enemy_mob.name} 被击败了！"
                        return "player_win"
            
            yield "---"
            round_count += 1
            
            # 添加一些随机性，避免无限循环
            if round_count > 20:
                yield "⏰ 战斗时间过长，以平局结束！"
                return "draw"
        
        # 如果战斗被中断
        if not self.battle_active:
            return "player_flee"
        
        return "draw"
    
    def stop_battle(self):
        """停止当前战斗"""
        self.battle_active = False

