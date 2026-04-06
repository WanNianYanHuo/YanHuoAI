#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目启动入口：切换到 python 目录并启动 RAG 后端。

用法（从项目根或 python 目录均可）：
  python run.py
  或
  python python/run.py
"""
import os
import sys

# 定位 python 目录
if __name__ == "__main__":
    this_file = os.path.abspath(__file__)
    python_dir = os.path.dirname(this_file)
    os.chdir(python_dir)
    if python_dir not in sys.path:
        sys.path.insert(0, python_dir)

    import uvicorn
    from api.server import app

    print("=" * 60)
    print("  RAG 后端: http://127.0.0.1:8000  (文档: /docs)")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
