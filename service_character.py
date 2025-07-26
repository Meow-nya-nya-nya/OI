from typing import Dict, Any, List, Optional
import json
import os
from config import ConfigService

class Mob:
    def __init__(self, name: str, health: int, attack_base: int, physical: int, magical: int, attack_speed: int, defense: int):
        # physical magical 一般在 100 上下，乘以 attack_base 得到攻击力
        self.name = "Mob"
        self.health = health
        self.attack_base = attack_base
        self.physical = physical
        self.magical = magical
        self.attack_speed = attack_speed
        self.defense = defense
    
    def take_damage(self, mob: 'Mob'):
        texts = []
        # 先按照 attack_speed 决定先后手
        is_attacker = self.attack_speed >= mob.attack_speed
        current, enemy = (self, mob) if is_attacker else (mob, self)
        while current.health > 0 and enemy.health > 0:
            attack_type = current.decide_attack_type()
            match self.attack_type:
                case 'physical':
                    damage = max(0, current.physical * enemy.attack_base - enemy.defense)
                    texts.append(f"{enemy} 对 {current} 造成了 {damage} 点物理伤害")
                case 'magical':
                    damage = max(0, current.magical * enemy.attack_base - enemy.defense)
                    texts.append(f"{enemy} 对 {current} 造成了 {damage} 点魔法伤害")
            mob.health -= damage
            if current.health <= 0:
                texts.append(f"{current} 被击败了！")
                break
            current, enemy = enemy, current  # 交换攻击者和防御者
        return texts
    
    def decide_attack_type(self) -> str:
        """决定攻击类型"""
        # 简单示例：50% 概率物理攻击，50% 概率魔法攻击
        return 'physical' if self.attack_base % 2 == 0 else 'magical'
    
    def __repr__(self):
        return self.name
    
class Character:
    """角色类"""
    
    def __init__(self, character_id: str, name: str, personality: str, 
                 location: str, mood: float = None):
        self.character_id = character_id
        self.name = name
        self.personality = personality
        self.location = location
        self.mood = mood or ConfigService().get_default_mood()
        self.conversation_history = []
    
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
            
            # 加载角色数据
            characters_data = role_data.get("characters", {})
            for character_id, character_info in characters_data.items():
                self.characters[character_id] = Character(
                    character_id=character_info["character_id"],
                    name=character_info["name"],
                    personality=character_info["personality"],
                    location=character_info["location"],
                    mood=character_info.get("mood", 0.5)
                )
                
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

