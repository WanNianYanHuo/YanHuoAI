# auth/jwt_auth.py
"""
JWT 认证模块
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import os

# JWT 配置
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


@dataclass
class TokenPayload:
    """Token 载荷"""
    user_id: int
    username: str
    exp: datetime


def create_access_token(user_id: int, username: str) -> str:
    """创建访问令牌"""
    expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expires,
        "iat": datetime.utcnow(),
    }
    
    # PyJWT 2.x+ 使用新 API
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证并解码 Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload["user_id"],
            "username": payload["username"],
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码 Token（不验证过期）"""
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        return {
            "user_id": payload["user_id"],
            "username": payload["username"],
        }
    except:
        return None