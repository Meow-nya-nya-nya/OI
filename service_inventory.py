"""
物品栏管理服务模块
管理玩家物品和物品效果
"""
from typing import Dict, Any, List, Optional
import json
import os


class Item:
    """物品类"""
    
    def __init__(self, item_id: str, name: str, description: str, item_type: str, effects: Dict[str, Any]):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type  # consumable, weapon, etc.
        self.effects = effects  # {"hp": 30, "attack": 1}
    
    def use(self, target_stats: Dict[str, Any]) -> Dict[str, Any]:
        """使用物品，返回效果结果"""
        result = {
            "success": True,
            "message": f"使用了{self.name}",
            "effects": {}
        }
        
        for effect_type, value in self.effects.items():
            if effect_type == "hp":
                old_hp = target_stats.get("hp", 100)
                max_hp = target_stats.get("max_hp", 100)
                new_hp = min(max_hp, old_hp + value)
                target_stats["hp"] = new_hp
                result["effects"]["hp"] = new_hp - old_hp
                
            elif effect_type == "attack":
                target_stats["attack"] = target_stats.get("attack", 10) + value
                result["effects"]["attack"] = value
                
            elif effect_type == "damage":
                old_hp = target_stats.get("hp", 100)
                new_hp = max(0, old_hp - abs(value))
                target_stats["hp"] = new_hp
                result["effects"]["damage"] = old_hp - new_hp
        
        return result


class InventoryService:
    """物品栏服务类"""
    
    def __init__(self):
        self.items_data = self._load_items_data()
        self.player_inventory = {}  # {item_id: count}
    
    def _load_items_data(self) -> Dict[str, Item]:
        """加载物品数据"""
        items_data = {
            "apple": Item(
                item_id="apple",
                name="苹果",
                description="新鲜的红苹果，看起来很美味",
                item_type="consumable",
                effects={"hp": 30, "attack": 1}
            ),
            "healing_potion": Item(
                item_id="healing_potion", 
                name="治疗药水",
                description="散发着草药香味的治疗药水",
                item_type="consumable",
                effects={"hp": 50}
            ),
            "damage_potion": Item(
                item_id="damage_potion",
                name="伤害药水",
                description="危险的毒药，使用需谨慎",
                item_type="consumable",
                effects={"damage": 30}
            ),
            "damage_potion": Item(
                item_id="herb",
                name="止血草",
                description="少量恢复血量，增加一些攻击力",
                item_type="consumable",
                effects={"hp": 10, "attack": 5}  # 对敌人30伤害，对自己50伤害
            ),
            "damage_potion": Item(
                item_id="damage_potion",
                name="伤害药水",
                description="危险的毒药，使用需谨慎",
                item_type="consumable",
                effects={"damage": 30}
            ),
            "damage_potion": Item(
                item_id="mana_potion",
                name="小蓝药",
                description="恢复少量血量",
                item_type="consumable",
                effects={"hp": 25}
            ),
            "damage_potion": Item(
                item_id="bread",
                name="硬面包",
                description="很干的面包",
                item_type="consumable",
                effects={"hp": 10}
            )
        }
        return items_data
    
    def add_item(self, item_id: str, count: int = 1) -> bool:
        """添加物品到背包"""
        if item_id in self.items_data:
            self.player_inventory[item_id] = self.player_inventory.get(item_id, 0) + count
            return True
        return False
    
    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """从背包移除物品"""
        if item_id in self.player_inventory and self.player_inventory[item_id] >= count:
            self.player_inventory[item_id] -= count
            if self.player_inventory[item_id] == 0:
                del self.player_inventory[item_id]
            return True
        return False
    
    def has_item(self, item_id: str, count: int = 1) -> bool:
        """检查是否有指定物品"""
        return self.player_inventory.get(item_id, 0) >= count
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """获取物品对象"""
        return self.items_data.get(item_id)
    
    def use_item(self, item_id: str, target_stats: Dict[str, Any], is_self: bool = True) -> Dict[str, Any]:
        """使用物品"""
        if not self.has_item(item_id):
            return {"success": False, "message": f"没有{self.items_data.get(item_id, {}).name}"}
        
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "message": "物品不存在"}
        
        # 特殊处理伤害药水
        if item_id == "damage_potion":
            if is_self:
                # 对自己使用伤害更大
                modified_effects = {"damage": 50}
                temp_item = Item(item.item_id, item.name, item.description, item.item_type, modified_effects)
                result = temp_item.use(target_stats)
            else:
                result = item.use(target_stats)
        else:
            result = item.use(target_stats)
        
        if result["success"]:
            self.remove_item(item_id)
        
        return result
    
    def get_inventory_display(self) -> str:
        """获取背包显示"""
        if not self.player_inventory:
            return "🎒 背包空空如也"
        
        inventory_lines = ["🎒 你的背包:"]
        for item_id, count in self.player_inventory.items():
            item = self.get_item(item_id)
            if item:
                inventory_lines.append(f"  • {item.name} x{count} - {item.description}")
        
        return "\n".join(inventory_lines)
    
    def get_usable_items(self) -> List[str]:
        """获取可使用的物品列表"""
        return list(self.player_inventory.keys())