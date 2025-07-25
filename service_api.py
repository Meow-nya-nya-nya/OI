# service_api.py
import logging_config  # 必须放最前
logging_config.setup_logging()
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from service import process_dialog

app = FastAPI(title="DOSGame-NPC-Dialog-Service")

# --------------- 请求体 ---------------
class DialogRequest(BaseModel):
    level: int
    npc: str
    option: str
    scene: str
    clear: bool = False   # 前端控制是否清空历史

# --------------- 内存会话存储 ---------------
# key 为前端会话 id（这里先用固定值 "global"，上线可换成 uuid）
session_store: Dict[str, List[Dict]] = {}

# --------------- 接口 ---------------
@app.post("/dialog")
def dialog_endpoint(req: DialogRequest):
    sid = "global"   # TODO: 上线时改成前端传来的唯一会话 id

    # 如果 clear=True 或会话不存在，则重建历史（仅含 system）
    if req.clear or sid not in session_store:
        from service import load_plot
        plots = load_plot(req.level)
        system_prompt = plots[req.scene]["plot"]
        session_store[sid] = [{"role": "system", "content": system_prompt}]

    current_mood = 0.5  # 可替换为从数据库读取
    result = process_dialog(
        level=req.level,
        npc=req.npc,
        option=req.option,
        scene=req.scene,
        mood=current_mood,
        history=session_store[sid]   # 把当前历史传进去
    )
    return result

# --------------- 本地调试入口 ---------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)