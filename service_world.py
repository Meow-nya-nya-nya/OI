"""
世界管理服务模块
管理游戏世界、位置和移动逻辑
"""
from typing import Dict, Any, List, Tuple, Optional
import json
import os


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
    
    def get_exits_description(self, direction_names: Dict[str, str] = None) -> str:
        """获取出口描述"""
        if not self.exits:
            return "这里没有明显的出路。"
        
        exit_list = []
        names_map = direction_names or {
            "north": "北方", "south": "南方",
            "east": "东方", "west": "西方",
            "up": "上方", "down": "下方"
        }
        
        for direction in self.exits.keys():
            chinese_dir = names_map.get(direction, direction)
            exit_list.append(chinese_dir)
        
        return f"可以前往: {', '.join(exit_list)}"


class WorldService:
    """世界管理服务类"""
    
    def __init__(self):
        self.locations = {}
        self.current_location = "village_center"
        self.direction_names = {}
        self._initialize_world()
    
    def _initialize_world(self):
        """从JSON文件初始化游戏世界"""
        scene_file = os.path.join("worlds", "scene.json")
        
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            # 加载方向名称映射
            self.direction_names = scene_data.get("direction_names", {})
            
            # 加载位置数据
            locations_data = scene_data.get("locations", {})
            for location_id, location_info in locations_data.items():
                self.locations[location_id] = Location(
                    name=location_info["name"],
                    description=location_info["description"],
                    exits=location_info.get("exits", {})
                )
            
            # 设置默认位置
            self.current_location = scene_data.get("default_location", "village_center")
            
        except FileNotFoundError:
            print(f"警告: 场景文件 {scene_file} 未找到，使用默认场景")
            self._create_default_world()
        except json.JSONDecodeError as e:
            print(f"警告: 场景文件格式错误: {e}，使用默认场景")
            self._create_default_world()
    
    def _create_default_world(self):
        """创建默认的游戏世界（备用方案）"""
        self.direction_names = {
            "north": "北方", "south": "南方",
            "east": "东方", "west": "西方",
            "up": "上方", "down": "下方"
        }
        
        self.locations["village_center"] = Location(
            name="村庄中心",
            description="这里是一个简单的村庄中心。",
            exits={}
        )
    
    def get_current_location(self) -> Location:
        """获取当前位置"""
        return self.locations.get(self.current_location)
    
    def get_location_description(self) -> str:
        """获取当前位置的完整描述"""
        location = self.get_current_location()
        if not location:
            return "你似乎迷失在了未知的地方..."
        
        description = f"📍 {location.name}\n\n{location.description}\n\n{location.get_exits_description(self.direction_names)}"
        
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

