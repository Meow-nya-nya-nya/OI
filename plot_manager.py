"""
剧情管理器模块
管理游戏剧情文件的加载和缓存
"""
import json
import os
from typing import Dict, Any, Optional, List


class PlotManager:
    """剧情管理器类"""
    
    def __init__(self, plots_dir: str = "plots"):
        self.plots_dir = plots_dir
        self.plot_cache = {}
        self._ensure_plots_dir()
    
    def _ensure_plots_dir(self):
        """确保剧情目录存在"""
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
    
    def load_plot(self, scene: str, level: int = 1) -> Optional[Dict[str, Any]]:
        """加载指定场景的剧情"""
        cache_key = f"{scene}_level{level}"
        
        # 检查缓存
        if cache_key in self.plot_cache:
            return self.plot_cache[cache_key]
        
        # 尝试加载文件
        plot_file = os.path.join(self.plots_dir, f"plot_{scene}.json")
        
        if not os.path.exists(plot_file):
            return None
        
        try:
            with open(plot_file, "r", encoding="utf-8") as f:
                plot_data = json.load(f)
            
            # 查找匹配的场景和等级
            for plot_item in plot_data:
                if (plot_item.get("scene") == scene and 
                    plot_item.get("level", 1) == level):
                    self.plot_cache[cache_key] = plot_item
                    return plot_item
            
            return None
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载剧情文件失败 {plot_file}: {e}")
            return None
    
    def get_plot_text(self, scene: str, level: int = 1) -> str:
        """获取剧情文本"""
        plot = self.load_plot(scene, level)
        if plot:
            return plot.get("plot", "")
        return ""
    
    def get_default_message(self, scene: str, level: int = 1) -> str:
        """获取默认消息"""
        plot = self.load_plot(scene, level)
        if plot:
            return plot.get("msg", "...")
        return "..."
    
    def get_available_scenes(self) -> List[str]:
        """获取所有可用的场景"""
        scenes = []
        
        if not os.path.exists(self.plots_dir):
            return scenes
        
        for filename in os.listdir(self.plots_dir):
            if filename.startswith("plot_") and filename.endswith(".json"):
                scene_name = filename[5:-5]  # 移除 "plot_" 前缀和 ".json" 后缀
                scenes.append(scene_name)
        
        return scenes
    
    def reload_plot(self, scene: str, level: int = 1):
        """重新加载指定剧情（清除缓存）"""
        cache_key = f"{scene}_level{level}"
        if cache_key in self.plot_cache:
            del self.plot_cache[cache_key]
        return self.load_plot(scene, level)
    
    def clear_cache(self):
        """清空所有剧情缓存"""
        self.plot_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cached_plots": len(self.plot_cache),
            "cache_keys": list(self.plot_cache.keys()),
            "plots_dir": self.plots_dir,
            "available_scenes": self.get_available_scenes()
        }

