# api/auth_api.py
"""
用户认证和知识库管理 API
"""

import sys
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime

# 确保路径正确
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import user_db, User
from auth.jwt_auth import create_access_token, verify_token, decode_token
from config.settings import KB_ROOT


# ========== 请求/响应模型 ==========

class RegisterRequest(BaseModel):
    username: str
    email: str  # Changed from EmailStr to avoid email-validator dependency
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str
    last_login: Optional[str]
    knowledge_bases: List[dict]


class KbInfoResponse(BaseModel):
    kb_id: str
    kb_name: str
    created_at: str
    is_default: bool
    doc_count: int = 0


class CreateKbRequest(BaseModel):
    kb_name: str


class ChatHistorySaveRequest(BaseModel):
    kb_id: Optional[str] = None
    session_id: str
    question: str
    answer: str
    llm_backend: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ChatSessionCreateRequest(BaseModel):
    kb_id: Optional[str] = None
    llm_backend: Optional[str] = None


class ChatSessionItem(BaseModel):
    session_id: str
    kb_id: str
    title: str
    llm_backend: Optional[str]
    created_at: str
    updated_at: str


# ========== 依赖函数 ==========

def get_current_user(
    authorization: str = Header(None, alias="Authorization")
) -> Optional[dict]:
    """
    获取当前登录用户（可选认证）
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        return None
    
    user = user_db.get_user_by_id(token_data["user_id"])
    if not user:
        return None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
    }


def require_auth(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    需要认证的依赖
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# ========== 路由 ==========

router = APIRouter(prefix="/api/v1", tags=["认证"])


@router.post("/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """
    用户注册
    """
    # 验证用户名格式
    username = req.username.strip()
    if len(username) < 3 or len(username) > 20:
        return AuthResponse(
            success=False,
            message="用户名长度必须在 3-20 个字符之间"
        )
    
    # 验证密码强度
    password = req.password
    if len(password) < 6:
        return AuthResponse(
            success=False,
            message="密码长度至少 6 个字符"
        )
    
    # 检查用户名是否已存在
    if user_db.get_user_by_username(username):
        return AuthResponse(
            success=False,
            message="用户名已存在"
        )
    
    # 检查邮箱是否已注册
    if user_db.get_user_by_email(str(req.email)):
        return AuthResponse(
            success=False,
            message="邮箱已被注册"
        )
    
    # 创建用户
    try:
        user = user_db.create_user(
            username=username,
            email=str(req.email),
            password=password
        )
        
        # 创建 Token
        token = create_access_token(user.id, user.username)
        
        return AuthResponse(
            success=True,
            message="注册成功",
            user=user.to_dict(),
            token=token
        )
        
    except Exception as e:
        return AuthResponse(
            success=False,
            message=f"注册失败: {str(e)}"
        )


@router.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """
    用户登录（支持用户名或邮箱）
    """
    username_or_email = req.username.strip()
    
    # 先尝试用用户名查找
    user = user_db.get_user_by_username(username_or_email)
    
    # 如果找不到，尝试用邮箱查找
    if not user:
        user = user_db.get_user_by_email(username_or_email)
    
    if not user:
        return AuthResponse(
            success=False,
            message="用户名或密码错误"
        )
    
    # 验证密码
    if not user_db.check_password(req.password, user.password_hash):
        return AuthResponse(
            success=False,
            message="用户名或密码错误"
        )
    
    # 更新最后登录时间
    user_db.update_last_login(user.id)
    
    # 创建 Token
    token = create_access_token(user.id, user.username)
    
    return AuthResponse(
        success=True,
        message="登录成功",
        user=user.to_dict(),
        token=token
    )


@router.get("/auth/me", response_model=UserInfoResponse)
def get_current_user_info(current_user: dict = Depends(require_auth)):
    """
    获取当前用户信息
    """
    user = user_db.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户的知识库列表
    kb_list = user_db.get_user_knowledge_bases(user.id)
    
    return UserInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
        knowledge_bases=kb_list
    )


# ========== 知识库管理 ==========

@router.get("/knowledge-bases")
def list_knowledge_bases(current_user: Optional[dict] = Depends(get_current_user)):
    """
    列出当前用户的知识库
    - 已登录用户：返回该用户的知识库
    - 未登录用户：返回空列表
    """
    if not current_user:
        return {
            "success": True,
            "knowledge_bases": [],
            "message": "请先登录查看您的知识库"
        }
    
    kb_list = user_db.get_user_knowledge_bases(current_user["user_id"])
    
    # 获取每个知识库的文档数量
    for kb in kb_list:
        kb_dir = os.path.join(KB_ROOT, kb["kb_id"])
        db_path = os.path.join(kb_dir, "docs.db")
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("SELECT COUNT(*) FROM document")
                kb["doc_count"] = cursor.fetchone()[0]
                conn.close()
            except:
                kb["doc_count"] = 0
        else:
            kb["doc_count"] = 0
    
    return {
        "success": True,
        "knowledge_bases": kb_list
    }


@router.post("/knowledge-bases")
def create_knowledge_base(
    req: CreateKbRequest,
    current_user: dict = Depends(require_auth)
):
    """
    为当前用户创建新知识库
    """
    kb_name = req.kb_name.strip()
    if not kb_name:
        raise HTTPException(status_code=400, detail="知识库名称不能为空")
    
    if len(kb_name) > 50:
        raise HTTPException(status_code=400, detail="知识库名称不能超过 50 个字符")
    
    # 创建知识库
    try:
        kb_id = user_db.create_knowledge_base(
            user_id=current_user["user_id"],
            kb_name=kb_name
        )
        
        return {
            "success": True,
            "message": "知识库创建成功",
            "kb_id": kb_id,
            "kb_name": kb_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@router.delete("/knowledge-bases/{kb_id}")
def delete_knowledge_base(
    kb_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    删除当前用户的知识库
    """
    # 检查权限
    if not user_db.check_kb_access(current_user["user_id"], kb_id):
        raise HTTPException(status_code=403, detail="无权访问该知识库")
    
    # 不能删除默认知识库
    kb_list = user_db.get_user_knowledge_bases(current_user["user_id"])
    for kb in kb_list:
        if kb["kb_id"] == kb_id and kb["is_default"]:
            raise HTTPException(status_code=400, detail="默认知识库无法删除，请创建新知识库后重试")
    
    # 删除知识库
    success = user_db.delete_knowledge_base(current_user["user_id"], kb_id)
    
    if success:
        return {
            "success": True,
            "message": "知识库删除成功"
        }
    else:
        raise HTTPException(status_code=500, detail="删除知识库失败")


@router.get("/knowledge-bases/{kb_id}/info")
def get_knowledge_base_info(
    kb_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    获取知识库详情
    """
    # 检查权限
    if not user_db.check_kb_access(current_user["user_id"], kb_id):
        raise HTTPException(status_code=403, detail="无权访问该知识库")
    
    kb_list = user_db.get_user_knowledge_bases(current_user["user_id"])
    kb_info = None
    for kb in kb_list:
        if kb["kb_id"] == kb_id:
            kb_info = kb
            break
    
    if not kb_info:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 获取文档数量
    kb_dir = os.path.join(KB_ROOT, kb_id)
    db_path = os.path.join(kb_dir, "docs.db")
    doc_count = 0
    if os.path.exists(db_path):
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM document")
            doc_count = cursor.fetchone()[0]
            conn.close()
        except:
            pass
    
    return {
        "success": True,
        "kb_id": kb_id,
        "kb_name": kb_info["kb_name"],
        "created_at": kb_info["created_at"],
        "is_default": kb_info["is_default"],
        "doc_count": doc_count
    }


# ========== 会话 & 会话历史 ==========

@router.post("/chat/session", response_model=ChatSessionItem)
def create_chat_session(
    req: ChatSessionCreateRequest,
    current_user: dict = Depends(require_auth),
):
    """创建一个新的会话，会话归属于当前用户 + 指定知识库"""
    kb_id = (req.kb_id or "").strip()
    if not kb_id:
        kb_id = ""
    try:
        session_id = user_db.create_chat_session(
            user_id=current_user["user_id"],
            kb_id=kb_id,
            llm_backend=req.llm_backend,
        )
        meta = user_db.get_chat_session(current_user["user_id"], session_id)
        return ChatSessionItem(
            session_id=session_id,
            kb_id=meta["kb_id"],
            title=meta["title"] or "",
            llm_backend=meta["llm_backend"] or None,
            created_at=meta["created_at"],
            updated_at=meta["updated_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {e}")


@router.get("/chat/sessions", response_model=list[ChatSessionItem])
def list_chat_sessions(
    kb_id: str = "",
    current_user: dict = Depends(require_auth),
):
    """列出当前用户在指定知识库下的所有会话"""
    kb_id = (kb_id or "").strip()
    try:
        items = user_db.list_chat_sessions(current_user["user_id"], kb_id)
        return [
            ChatSessionItem(
                session_id=i["session_id"],
                kb_id=kb_id,
                title=i["title"],
                llm_backend=i["llm_backend"] or None,
                created_at=i["created_at"],
                updated_at=i["updated_at"],
            )
            for i in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {e}")


@router.delete("/chat/session/{session_id}")
def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(require_auth),
):
    """删除当前用户的指定会话及其历史记录"""
    ok = user_db.delete_chat_session(current_user["user_id"], session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True}


def _generate_session_title(question: str, answer: str, llm_backend: Optional[str]) -> str:
    """
    使用首轮问答让大模型生成会话标题。
    """
    from llm.ollama_client import call_llm

    q = (question or "").strip()
    a = (answer or "").strip()
    if not q and not a:
        return ""
    prompt = (
        "请根据下面这一轮问答内容，生成一个简短的中文标题，不超过20个字，"
        "不要带引号或标点，只输出标题本身。\n\n"
        f"【问题】{q}\n\n【回答】{a}\n\n【标题】"
    )
    try:
        title = call_llm(prompt, stream_callback=None, on_complete=None, backend=llm_backend)
        title = (title or "").strip().splitlines()[0]
        return title[:40]
    except Exception:
        # 兜底：截取问题前若干字
        return q[:20] or "新的会话"


@router.post("/chat/history/save")
def save_chat_history(
    req: ChatHistorySaveRequest,
    current_user: dict = Depends(require_auth),
):
    """
    保存一轮会话记录到当前用户的持久化数据库中。
    - 每次请求保存一条问答（question + answer），按 user_id + kb_id + session_id 归档
    - 如果该会话尚未有标题，则自动用首轮问答生成标题
    """
    kb_id = (req.kb_id or "").strip()
    session_id = (req.session_id or "").strip()
    question = (req.question or "").strip()
    answer = (req.answer or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    if not question or not answer:
        raise HTTPException(status_code=400, detail="question 和 answer 不能为空")

    try:
        user_db.append_chat_history(
            user_id=current_user["user_id"],
            kb_id=kb_id,
            session_id=session_id,
            question=question,
            answer=answer,
        )

        # 如会话还没有标题，则用当前这一轮问答生成一个
        meta = user_db.get_chat_session(current_user["user_id"], session_id)
        title = meta["title"] or ""
        if not title:
            title = _generate_session_title(question, answer, req.llm_backend)
            if title:
                user_db.set_chat_session_title(current_user["user_id"], session_id, title)
                meta = user_db.get_chat_session(current_user["user_id"], session_id)

        return {
            "success": True,
            "session_id": session_id,
            "title": meta["title"] if meta else title,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存会话失败: {e}")


@router.get("/chat/history", response_model=list[ChatMessage])
def get_chat_history(
    kb_id: str = "",
    session_id: str = "",
    current_user: dict = Depends(require_auth),
):
    """
    获取当前用户在指定知识库 + 会话下的历史会话消息（按时间顺序）。
    前端可按 role=user/assistant 将其还原为多轮问答。
    """
    kb_id = (kb_id or "").strip()
    session_id = (session_id or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    try:
        records = user_db.get_chat_history(
            user_id=current_user["user_id"],
            kb_id=kb_id,
            session_id=session_id,
        )
        return [ChatMessage(**r) for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取会话失败: {e}")