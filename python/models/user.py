# models/user.py
"""
用户认证模型和数据库管理
"""

import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import os

# 数据库路径
USER_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")

# 导入 KB_ROOT 用于创建知识库目录
from config.settings import KB_ROOT


@dataclass
class User:
    """用户数据模型"""
    id: int
    username: str
    email: str
    password_hash: str
    role: str
    created_at: str
    last_login: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }


class UserDatabase:
    """用户数据库管理类"""
    
    def __init__(self, db_path: str = USER_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            # 检查表是否存在
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # 创建用户表
                conn.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        created_at TEXT NOT NULL,
                        last_login TEXT
                    )
                """)
            else:
                # 检查是否有 role 列
                cursor = conn.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'role' not in columns:
                    # 添加 role 列
                    conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            
            # 用户知识库关联表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_knowledge_bases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    kb_id TEXT NOT NULL,
                    kb_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, kb_id)
                )
            """)
            
            # 用户会话历史表：按用户 + 知识库 + 会话分组存储对话消息
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    kb_id TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,             -- 'user' 或 'assistant'
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_user_kb_time
                ON user_chat_history(user_id, kb_id, created_at)
            """)
            # 如历史表已存在但缺少 session_id 列，则添加（迁移旧数据）
            cursor = conn.execute("PRAGMA table_info(user_chat_history)")
            chat_cols = [col[1] for col in cursor.fetchall()]
            if "session_id" not in chat_cols:
                conn.execute("ALTER TABLE user_chat_history ADD COLUMN session_id TEXT")

            # 用户会话元数据表：管理会话列表与标题
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    kb_id TEXT NOT NULL,
                    session_id TEXT NOT NULL UNIQUE,
                    title TEXT,
                    llm_backend TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_kb
                ON user_chat_sessions(user_id, kb_id, created_at)
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_kb_user_id 
                ON user_knowledge_bases(user_id)
            """)
            
            conn.commit()
            
            # 创建默认管理员账户
            admin = self.get_user_by_username('admin')
            if not admin:
                admin_password_hash = self._hash_password('admin123')
                conn.execute("""
                    INSERT INTO users (username, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, ('admin', 'admin@example.com', admin_password_hash, 'admin', datetime.now().isoformat()))
                conn.commit()
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> User:
        """创建新用户"""
        password_hash = self._hash_password(password)
        created_at = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO users (username, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, role, created_at))
            
            user_id = cursor.lastrowid
            
            # 创建默认知识库
            default_kb_id = f"kb_{user_id:04d}"
            conn.execute("""
                INSERT INTO user_knowledge_bases (user_id, kb_id, kb_name, created_at, is_default)
                VALUES (?, ?, ?, ?, 1)
            """, (user_id, default_kb_id, f"{username}的默认知识库", created_at))
            
            conn.commit()
            
            return User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                created_at=created_at,
                last_login=None
            )
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            
            return self._row_to_user(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            return self._row_to_user(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            
            return self._row_to_user(row) if row else None
    
    def verify_password(self, user: User, password: str) -> bool:
        """验证密码"""
        return self._hash_password(password) == user.password_hash
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """将数据库行转换为 User 对象"""
        # 检查 role 列是否存在
        try:
            role = row["role"]
        except (IndexError, KeyError):
            role = "user"
        
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=role,
            created_at=row["created_at"],
            last_login=row["last_login"],
        )
    
    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hash_obj.hex()}"
    
    def check_password(self, password: str, password_hash: str) -> bool:
        """检查密码是否匹配"""
        try:
            salt, hash_val = password_hash.split(":")
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return new_hash.hex() == hash_val
        except:
            return False
    
    # ========== 知识库管理方法 ==========
    
    def get_user_knowledge_bases(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有知识库"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT kb_id, kb_name, created_at, is_default
                FROM user_knowledge_bases
                WHERE user_id = ?
                ORDER BY created_at ASC
            """, (user_id,)).fetchall()
            
            return [
                {
                    "kb_id": row["kb_id"],
                    "kb_name": row["kb_name"],
                    "created_at": row["created_at"],
                    "is_default": bool(row["is_default"]),
                }
                for row in rows
            ]
    
    def create_knowledge_base(self, user_id: int, kb_name: str) -> str:
        """为用户创建新知识库"""
        # 延迟导入以避免循环依赖
        from rag.kb_manager import get_storage_key
        
        # 检查用户是否已有同名知识库
        existing_kbs = self.get_user_knowledge_bases(user_id)
        for kb in existing_kbs:
            if kb["kb_name"] == kb_name:
                raise Exception("知识库名称已存在")
        
        # 生成 storage_key
        kb_id = get_storage_key(kb_name)
        
        # 如果生成的 kb_id 对应的目录已存在（被其他知识库占用），添加后缀
        kb_dir = os.path.join(KB_ROOT, kb_id)
        counter = 1
        while os.path.exists(kb_dir):
            kb_id = f"{get_storage_key(kb_name)}_{counter}"
            kb_dir = os.path.join(KB_ROOT, kb_id)
            counter += 1
        
        created_at = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_knowledge_bases (user_id, kb_id, kb_name, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, kb_id, kb_name, created_at))
            
            conn.commit()
        
        # 创建物理目录
        os.makedirs(kb_dir, exist_ok=True)
        
        return kb_id
    
    def delete_knowledge_base(self, user_id: int, kb_id: str) -> bool:
        """删除用户的知识库"""
        import shutil
        
        with self._get_connection() as conn:
            # 检查知识库是否属于该用户
            row = conn.execute("""
                SELECT kb_id FROM user_knowledge_bases
                WHERE user_id = ? AND kb_id = ?
            """, (user_id, kb_id)).fetchone()
            
            if not row:
                return False
            
            # 从数据库删除
            conn.execute("""
                DELETE FROM user_knowledge_bases
                WHERE user_id = ? AND kb_id = ?
            """, (user_id, kb_id))
            
            conn.commit()
        
        # 删除物理目录
        kb_dir = os.path.join(KB_ROOT, kb_id)
        if os.path.exists(kb_dir):
            shutil.rmtree(kb_dir)
        
        return True
    
    def get_default_kb_id(self, user_id: int) -> Optional[str]:
        """获取用户的默认知识库 ID"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT kb_id FROM user_knowledge_bases
                WHERE user_id = ? AND is_default = 1
            """, (user_id,)).fetchone()
            
            return row["kb_id"] if row else None
    
    def check_kb_access(self, user_id: int, kb_id: str) -> bool:
        """检查用户是否有权限访问该知识库"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT 1 FROM user_knowledge_bases
                WHERE user_id = ? AND kb_id = ?
            """, (user_id, kb_id)).fetchone()
            
            return row is not None

    # ========== 会话 & 历史管理 ==========

    def create_chat_session(self, user_id: int, kb_id: str, llm_backend: Optional[str] = None) -> str:
        """为用户在指定 kb 下创建新会话，返回 session_id"""
        kb_id = kb_id or ""
        sid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_chat_sessions (user_id, kb_id, session_id, title, llm_backend, created_at, updated_at)
                VALUES (?, ?, ?, NULL, ?, ?, ?)
                """,
                (user_id, kb_id, sid, llm_backend or "", now, now),
            )
            conn.commit()
        return sid

    def list_chat_sessions(self, user_id: int, kb_id: str) -> List[Dict[str, Any]]:
        """列出用户在指定 kb 下的所有会话"""
        kb_id = kb_id or ""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT session_id, title, llm_backend, created_at, updated_at
                FROM user_chat_sessions
                WHERE user_id = ? AND kb_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id, kb_id),
            ).fetchall()
        return [
            {
                "session_id": row["session_id"],
                "title": row["title"] or "",
                "llm_backend": row["llm_backend"] or "",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def delete_chat_session(self, user_id: int, session_id: str) -> bool:
        """删除指定会话及其历史"""
        with self._get_connection() as conn:
            # 确认会话属于该用户
            row = conn.execute(
                """
                SELECT id FROM user_chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "DELETE FROM user_chat_history WHERE user_id = ? AND session_id = ?",
                (user_id, session_id),
            )
            conn.execute(
                "DELETE FROM user_chat_sessions WHERE user_id = ? AND session_id = ?",
                (user_id, session_id),
            )
            conn.commit()
        return True

    def get_chat_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """获取单个会话元数据"""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT kb_id, session_id, title, llm_backend, created_at, updated_at
                FROM user_chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            ).fetchone()
        if not row:
            return None
        return {
            "kb_id": row["kb_id"],
            "session_id": row["session_id"],
            "title": row["title"] or "",
            "llm_backend": row["llm_backend"] or "",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def set_chat_session_title(self, user_id: int, session_id: str, title: str):
        """更新会话标题"""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE user_chat_sessions
                SET title = ?, updated_at = ?
                WHERE user_id = ? AND session_id = ?
                """,
                (title, datetime.now().isoformat(), user_id, session_id),
            )
            conn.commit()

    def append_chat_history(self, user_id: int, kb_id: str, session_id: str, question: str, answer: str):
        """追加一轮问答到用户会话历史（按 user_id + kb_id + session_id 记录）"""
        kb_id = kb_id or ""
        session_id = session_id or ""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            # 一轮问答存两条：用户提问 + 助手回答
            conn.execute(
                """
                INSERT INTO user_chat_history (user_id, kb_id, session_id, role, content, created_at)
                VALUES (?, ?, ?, 'user', ?, ?)
                """,
                (user_id, kb_id, session_id, question, now),
            )
            conn.execute(
                """
                INSERT INTO user_chat_history (user_id, kb_id, session_id, role, content, created_at)
                VALUES (?, ?, ?, 'assistant', ?, ?)
                """,
                (user_id, kb_id, session_id, answer, now),
            )
            # 更新会话的最近时间
            conn.execute(
                """
                UPDATE user_chat_sessions
                SET updated_at = ?
                WHERE user_id = ? AND session_id = ?
                """,
                (now, user_id, session_id),
            )
            conn.commit()

    def get_chat_history(self, user_id: int, kb_id: str, session_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """获取指定用户在某个 kb + 会话下最近的会话历史（按时间顺序）"""
        kb_id = kb_id or ""
        session_id = session_id or ""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM user_chat_history
                WHERE user_id = ? AND kb_id = ? AND session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (user_id, kb_id, session_id, limit),
            ).fetchall()
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


# 全局用户数据库实例
user_db = UserDatabase()