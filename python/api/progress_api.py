# -*- coding: utf-8 -*-
"""
进度状态管理API
独立于流式响应的进度状态系统
"""

import json
import time
import uuid
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import threading

# 全局进度状态存储
_progress_store: Dict[str, Dict[str, Any]] = {}
_progress_lock = threading.Lock()

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


class ProgressStatus(BaseModel):
    """进度状态模型"""
    session_id: str
    stage: str
    message: str
    timestamp: float
    is_active: bool = True
    is_completed: bool = False


class ProgressResponse(BaseModel):
    """进度响应模型"""
    session_id: str
    current_stage: Optional[str] = None
    current_message: Optional[str] = None
    is_active: bool = False
    is_completed: bool = False
    timestamp: Optional[float] = None
    stages_completed: int = 0


def create_progress_session() -> str:
    """创建新的进度会话"""
    session_id = str(uuid.uuid4())
    with _progress_lock:
        _progress_store[session_id] = {
            "current_stage": None,
            "current_message": None,
            "is_active": False,
            "is_completed": False,
            "timestamp": time.time(),
            "stages_completed": 0,
            "created_at": time.time(),
            "stage_history": []  # 添加阶段历史记录
        }
    return session_id


def update_progress(session_id: str, stage: str, message: str):
    """更新进度状态（带去重逻辑和历史记录）"""
    with _progress_lock:
        if session_id in _progress_store:
            current_data = _progress_store[session_id]
            
            # 检查是否是重复更新
            if (current_data.get("current_stage") == stage and 
                current_data.get("current_message") == message):
                return  # 跳过重复更新
            
            # 只有在阶段真正变化时才增加计数和记录历史
            stages_completed = current_data["stages_completed"]
            if current_data.get("current_stage") != stage:
                stages_completed += 1
                # 记录到历史
                current_data["stage_history"].append({
                    "stage": stage,
                    "message": message,
                    "timestamp": time.time()
                })
            
            _progress_store[session_id].update({
                "current_stage": stage,
                "current_message": message,
                "is_active": True,
                "is_completed": False,
                "timestamp": time.time(),
                "stages_completed": stages_completed
            })


def complete_progress(session_id: str):
    """完成进度"""
    with _progress_lock:
        if session_id in _progress_store:
            _progress_store[session_id].update({
                "current_stage": "已完成",
                "current_message": "处理完成",
                "is_active": False,
                "is_completed": True,
                "timestamp": time.time()
            })


def get_progress(session_id: str) -> Optional[Dict[str, Any]]:
    """获取进度状态"""
    with _progress_lock:
        return _progress_store.get(session_id)


def cleanup_old_sessions():
    """清理超过1小时的旧会话"""
    current_time = time.time()
    with _progress_lock:
        expired_sessions = [
            sid for sid, data in _progress_store.items()
            if current_time - data.get("created_at", 0) > 3600  # 1小时
        ]
        for sid in expired_sessions:
            del _progress_store[sid]


@router.post("/create", response_model=dict)
def create_session():
    """创建新的进度会话"""
    session_id = create_progress_session()
    return {"session_id": session_id, "status": "created"}


@router.get("/{session_id}", response_model=ProgressResponse)
def get_session_progress(session_id: str):
    """获取指定会话的进度状态"""
    progress_data = get_progress(session_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="进度会话不存在")
    
    return ProgressResponse(
        session_id=session_id,
        current_stage=progress_data.get("current_stage"),
        current_message=progress_data.get("current_message"),
        is_active=progress_data.get("is_active", False),
        is_completed=progress_data.get("is_completed", False),
        timestamp=progress_data.get("timestamp"),
        stages_completed=progress_data.get("stages_completed", 0)
    )


@router.get("/{session_id}/stream")
async def stream_session_progress(session_id: str):
    """
    SSE流式推送进度状态
    前端通过EventSource连接此端点，实时接收进度更新
    """
    async def event_generator():
        """生成SSE事件流"""
        import asyncio
        
        # 检查会话是否存在
        progress_data = get_progress(session_id)
        if not progress_data:
            yield f"data: {json.dumps({'error': '进度会话不存在'}, ensure_ascii=False)}\n\n"
            return
        
        last_stage = None
        last_timestamp = 0
        
        # 持续推送进度更新，直到完成
        while True:
            progress_data = get_progress(session_id)
            if not progress_data:
                break
            
            current_stage = progress_data.get("current_stage")
            current_timestamp = progress_data.get("timestamp", 0)
            is_completed = progress_data.get("is_completed", False)
            
            # 只在状态变化时推送
            if current_stage and (current_stage != last_stage or current_timestamp != last_timestamp):
                event_data = {
                    "session_id": session_id,
                    "current_stage": current_stage,
                    "current_message": progress_data.get("current_message"),
                    "is_active": progress_data.get("is_active", False),
                    "is_completed": is_completed,
                    "timestamp": current_timestamp,
                    "stages_completed": progress_data.get("stages_completed", 0)
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
                last_stage = current_stage
                last_timestamp = current_timestamp
            
            # 如果已完成，发送完成事件后退出
            if is_completed:
                await asyncio.sleep(0.1)  # 确保完成事件被发送
                break
            
            # 短暂等待后继续检查
            await asyncio.sleep(0.1)  # 100ms检查一次，快速响应
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@router.get("/{session_id}/history")
def get_session_history(session_id: str):
    """获取指定会话的阶段历史"""
    progress_data = get_progress(session_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="进度会话不存在")
    
    return {
        "session_id": session_id,
        "stage_history": progress_data.get("stage_history", []),
        "current_stage": progress_data.get("current_stage"),
        "is_completed": progress_data.get("is_completed", False)
    }


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """删除进度会话"""
    with _progress_lock:
        if session_id in _progress_store:
            del _progress_store[session_id]
            return {"session_id": session_id, "status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="进度会话不存在")


@router.get("/")
def list_active_sessions():
    """列出所有活跃的进度会话"""
    cleanup_old_sessions()  # 清理旧会话
    
    with _progress_lock:
        active_sessions = []
        for session_id, data in _progress_store.items():
            if data.get("is_active", False):
                active_sessions.append({
                    "session_id": session_id,
                    "current_stage": data.get("current_stage"),
                    "current_message": data.get("current_message"),
                    "timestamp": data.get("timestamp"),
                    "stages_completed": data.get("stages_completed", 0)
                })
        return {"active_sessions": active_sessions, "count": len(active_sessions)}


# 进度回调函数生成器
def create_progress_callback(session_id: str):
    """创建进度回调函数"""
    last = {"stage": None, "message": None}

    def progress_callback(stage: str, message: str):
        # 如果阶段和文案都没变，则不再打印/更新，避免日志重复刷屏
        if last["stage"] == stage and last["message"] == message:
            return
        last["stage"] = stage
        last["message"] = message
        update_progress(session_id, stage, message)
        print(f"[PROGRESS][{session_id[:8]}] [{stage}] {message}")
    
    return progress_callback