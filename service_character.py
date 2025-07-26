"""
角色管理服务模块
管理游戏中的 NPC 角色
"""
from typing import Dict, Any, List, Optional
from service_config import ConfigService


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
    
    def add_conversation(self, user_message: str, ai_response: str):
        """添加对话记录"""
        self.conversation_history.append({
            'user': user_message,
            'ai': ai_response
        })
        
        # 限制历史记录长度，避免内存过度使用
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_conversation_context(self) -> str:
        """获取对话上下文"""
        if not self.conversation_history:
            return ""
        
        context_lines = []
        for conv in self.conversation_history[-3:]:  # 只取最近 3 轮对话
            context_lines.append(f"玩家: {conv['user']}")
            context_lines.append(f"{self.name}: {conv['ai']}")
        
        return "\n".join(context_lines)
    
    def get_description(self) -> str:
        """获取角色描述"""
        mood_desc = self._get_mood_description()
        return f"{self.name} ({mood_desc})"
    
    def _get_mood_description(self) -> str:
        """获取心情描述"""
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
        self._initialize_characters()
    
    def _initialize_characters(self):
        """初始化游戏角色"""
        # 村庄长老
        self.characters["elder"] = Character(
            character_id="elder",
            name="村庄长老",
            personality="智慧而和蔼的老人，对村庄的历史了如指掌。他总是乐于为年轻的冒险者提供建议和指导。说话温和但富有哲理。",
            location="village_center",
            mood=0.7
        )
        
        # 商店老板
        self.characters["shopkeeper"] = Character(
            character_id="shopkeeper",
            name="商店老板",
            personality="精明但诚实的商人，对各种商品和价格了如指掌。他喜欢与顾客聊天，总是能提供有用的信息。说话直接但友善。",
            location="village_shop",
            mood=0.6
        )
        
        # 神秘旅者
        self.characters["traveler"] = Character(
            character_id="traveler",
            name="神秘旅者",
            personality="来自远方的神秘旅者，见多识广，知道许多外界的秘密。他的话语中总是带着一丝神秘感，让人捉摸不透。",
            location="forest_entrance",
            mood=0.5
        )
        
        # 村民
        self.characters["villager"] = Character(
            character_id="villager",
            name="村民",
            personality="朴实的村民，对村庄生活非常熟悉。他们勤劳善良，但对外来者有些谨慎。说话朴实无华。",
            location="village_house",
            mood=0.5
        )
        
        # 河边渔夫
        self.characters["fisherman"] = Character(
            character_id="fisherman",
            name="河边渔夫",
            personality="安静的渔夫，喜欢独自在河边钓鱼。他对河流和周围的自然环境非常了解，说话简洁但富有智慧。",
            location="river_bank",
            mood=0.6
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

