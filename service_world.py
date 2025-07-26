"""
世界管理服务模块
管理游戏世界、位置和移动逻辑
"""
from typing import Dict, Any, List, Tuple, Optional


class Location:
    """位置类"""
    
    def __init__(self, name: str, description: str, exits: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.exits = exits or {}
        self.characters = []  # 该位置的角色列表
    
    def add_character(self, character_id: str):
        """添加角色到该位置"""
        if character_id not in self.characters:
            self.characters.append(character_id)
    
    def remove_character(self, character_id: str):
        """从该位置移除角色"""
        if character_id in self.characters:
            self.characters.remove(character_id)
    
    def get_exits_description(self) -> str:
        """获取出口描述"""
        if not self.exits:
            return "这里没有明显的出路。"
        
        exit_list = []
        direction_names = {
            "north": "北方", "south": "南方",
            "east": "东方", "west": "西方",
            "up": "上方", "down": "下方"
        }
        
        for direction in self.exits.keys():
            chinese_dir = direction_names.get(direction, direction)
            exit_list.append(chinese_dir)
        
        return f"可以前往: {', '.join(exit_list)}"


class WorldService:
    """世界管理服务类"""
    
    def __init__(self):
        self.locations = {}
        self.current_location = "village_center"
        self._initialize_world()
    
    def _initialize_world(self):
        """初始化游戏世界"""
        # 村庄中心
        self.locations["village_center"] = Location(
            name="村庄中心",
            description="这里是一个宁静的小村庄的中心。古老的石井坐落在广场中央，周围是几座朴素的房屋。微风轻拂，带来远山的清香。",
            exits={
                "north": "forest_entrance",
                "east": "village_shop",
                "west": "village_house",
                "south": "river_bank"
            }
        )
        
        # 森林入口
        self.locations["forest_entrance"] = Location(
            name="森林入口",
            description="茂密的森林在你面前展开，高大的树木遮天蔽日。阳光透过树叶洒下斑驳的光影，空气中弥漫着泥土和青草的香味。",
            exits={
                "south": "village_center",
                "north": "deep_forest"
            }
        )
        
        # 深林
        self.locations["deep_forest"] = Location(
            name="深林",
            description="你深入森林，周围变得更加幽暗神秘。古老的树木仿佛在窃窃私语，远处传来不明的声响。这里充满了未知的危险和机遇。",
            exits={
                "south": "forest_entrance"
            }
        )
        
        # 村庄商店
        self.locations["village_shop"] = Location(
            name="村庄商店",
            description="这是一间温馨的小商店，货架上摆满了各种日用品和冒险用具。店主是一位和蔼的老人，总是乐于助人。",
            exits={
                "west": "village_center"
            }
        )
        
        # 村民房屋
        self.locations["village_house"] = Location(
            name="村民房屋",
            description="这是一座典型的村庄房屋，木制的墙壁和茅草屋顶。房屋虽然简朴，但收拾得很整洁，透露出主人的勤劳。",
            exits={
                "east": "village_center"
            }
        )
        
        # 河岸
        self.locations["river_bank"] = Location(
            name="河岸",
            description="清澈的小河缓缓流淌，河水倒映着天空的蓝色。河岸边长满了芦苇和野花，偶尔有小鱼跃出水面，激起阵阵涟漪。",
            exits={
                "north": "village_center"
            }
        )
    
    def get_current_location(self) -> Location:
        """获取当前位置"""
        return self.locations.get(self.current_location)
    
    def get_location_description(self) -> str:
        """获取当前位置的完整描述"""
        location = self.get_current_location()
        if not location:
            return "你似乎迷失在了未知的地方..."
        
        description = f"📍 {location.name}\n\n{location.description}\n\n{location.get_exits_description()}"
        
        # 添加角色信息
        if location.characters:
            description += f"\n\n👥 这里有: {', '.join(location.characters)}"
        
        return description
    
    def move_to(self, direction: str) -> Tuple[bool, str]:
        """移动到指定方向"""
        current_loc = self.get_current_location()
        if not current_loc:
            return False, "当前位置未知，无法移动。"
        
        # 方向映射
        direction_map = {
            "北": "north", "南": "south", "东": "east", "西": "west",
            "上": "up", "下": "down", "北方": "north", "南方": "south",
            "东方": "east", "西方": "west", "上方": "up", "下方": "down"
        }
        
        # 标准化方向
        normalized_direction = direction_map.get(direction, direction)
        
        if normalized_direction not in current_loc.exits:
            return False, f"无法向{direction}移动，那里没有路。"
        
        target_location = current_loc.exits[normalized_direction]
        if target_location not in self.locations:
            return False, f"目标位置 {target_location} 不存在。"
        
        self.current_location = target_location
        return True, f"你向{direction}移动了。"
    
    def get_available_directions(self) -> List[str]:
        """获取可用的移动方向"""
        current_loc = self.get_current_location()
        if not current_loc:
            return []
        return list(current_loc.exits.keys())
    
    def add_character_to_location(self, character_id: str, location_id: str = None):
        """将角色添加到指定位置"""
        if location_id is None:
            location_id = self.current_location
        
        if location_id in self.locations:
            self.locations[location_id].add_character(character_id)
    
    def remove_character_from_location(self, character_id: str, location_id: str = None):
        """从指定位置移除角色"""
        if location_id is None:
            location_id = self.current_location
        
        if location_id in self.locations:
            self.locations[location_id].remove_character(character_id)
    
    def get_characters_in_current_location(self) -> List[str]:
        """获取当前位置的所有角色"""
        current_loc = self.get_current_location()
        if not current_loc:
            return []
        return current_loc.characters.copy()
    
    def reset_to_start(self):
        """重置到起始位置"""
        self.current_location = "village_center"

