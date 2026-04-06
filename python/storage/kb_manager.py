# storage/kb_manager.py

import os
import shutil
from config.runtime import CURRENT_KB
from config.settings import KB_ROOT


def get_kb_path(kb_name: str) -> str:
    return os.path.join(KB_ROOT, kb_name)


def list_kbs():
    if not os.path.exists(KB_ROOT):
        return []
    return [
        d for d in os.listdir(KB_ROOT)
        if os.path.isdir(os.path.join(KB_ROOT, d)) and d != "_embedding_cache"
    ]


def create_kb(kb_name: str):
    path = get_kb_path(kb_name)
    if os.path.exists(path):
        raise ValueError(f"知识库 {kb_name} 已存在")

    os.makedirs(path, exist_ok=True)
    print(f"已创建知识库：{kb_name}")


def delete_kb(kb_name: str):
    path = get_kb_path(kb_name)
    if not os.path.exists(path):
        raise ValueError(f"知识库 {kb_name} 不存在")

    shutil.rmtree(path)
    print(f"已删除知识库：{kb_name}")
