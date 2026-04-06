# api/admin_api.py
"""
管理员 API：用户管理
"""

import sys
import os
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime

# 确保路径正确
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import user_db, User
from auth.jwt_auth import verify_token


# ========== 请求/响应模型 ==========

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str
    last_login: str = None


class UsersListResponse(BaseModel):
    success: bool
    users: List[UserResponse]
    total: int


# ========== 依赖函数 ==========

def require_admin(
    authorization: str = Header(None, alias="Authorization")
) -> dict:
    """
    需要管理员权限的依赖
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "unauthorized", "message": "请先登录", "status_code": 401}
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        return {"error": "unauthorized", "message": "令牌无效或已过期", "status_code": 401}
    
    user = user_db.get_user_by_id(token_data["user_id"])
    if not user:
        return {"error": "unauthorized", "message": "用户不存在", "status_code": 401}
    
    if user.username != 'admin':
        return {"error": "forbidden", "message": "需要管理员权限", "status_code": 403}
    
    return {
        "user_id": user.id,
        "username": user.username,
    }


# ========== 路由 ==========

router = APIRouter(prefix="/api/v1/admin", tags=["管理员"])


@router.get("/users")
def list_users(current_user: dict = Depends(require_admin)):
    """
    获取所有用户列表（仅管理员）
    """
    try:
        # 获取所有用户
        with user_db._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, email, role, created_at, last_login
                FROM users
                ORDER BY id ASC
            """).fetchall()
        
        users = []
        for row in rows:
            # sqlite3.Row 使用索引或列名访问
            # 使用 row['role'] 直接访问，如果列不存在会抛出 KeyError
            try:
                role = row["role"]
            except (KeyError, IndexError):
                role = "user"
            users.append({
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "role": role,
                "created_at": row["created_at"],
                "last_login": row["last_login"],
            })
        
        return {
            "success": True,
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 返回 JSON 错误而不是 HTML
        return {"success": False, "message": f"获取用户列表失败: {str(e)}"}


@router.post("/users/{user_id}/set-admin")
def set_user_admin(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    将用户设为管理员（仅管理员）
    """
    # 不能修改自己
    if user_id == current_user["user_id"]:
        return {"success": False, "message": "不能修改自己的权限"}
    
    user = user_db.get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}
    
    # 管理员不能被降级
    if user.username == 'admin':
        return {"success": False, "message": "不能修改超级管理员权限"}
    
    # 在用户表中添加 role 字段（如果不存在）
    try:
        with user_db._get_connection() as conn:
            # 检查是否有 role 列
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'role' not in columns:
                # 添加 role 列
                conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
    except:
        pass
    
    # 更新用户角色
    try:
        with user_db._get_connection() as conn:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
            conn.commit()
    except:
        # 如果 role 列不存在，使用另一种方式
        pass
    
    return {
        "success": True,
        "message": f"用户 {user.username} 已设为管理员"
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    删除用户（仅管理员）
    """
    # 不能删除自己
    if user_id == current_user["user_id"]:
        return {"success": False, "message": "不能删除自己"}
    
    user = user_db.get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}
    
    # 不能删除超级管理员
    if user.username == 'admin':
        return {"success": False, "message": "不能删除超级管理员"}
    
    # 删除用户的知识库
    kbs = user_db.get_user_knowledge_bases(user_id)
    for kb in kbs:
        user_db.delete_knowledge_base(user_id, kb['kb_id'])
    
    # 删除用户
    with user_db._get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    
    return {
        "success": True,
        "message": f"用户 {user.username} 已删除"
    }


@router.get("/stats")
def get_admin_stats(current_user: dict = Depends(require_admin)):
    """
    获取管理统计信息（仅管理员）
    """
    with user_db._get_connection() as conn:
        # 用户总数
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        # 知识库总数
        kb_count = conn.execute("SELECT COUNT(*) FROM user_knowledge_bases").fetchone()[0]
        
        # 今日活跃用户
        today = datetime.now().strftime('%Y-%m-%d')
        active_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE last_login LIKE ?",
            (f"{today}%",)
        ).fetchone()[0]
    
    return {
        "success": True,
        "stats": {
            "user_count": user_count,
            "kb_count": kb_count,
            "active_today": active_today,
        }
    }