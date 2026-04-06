#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动 Python RAG 后端服务（统一入口）。

用法（必须在 python 目录下执行）：
  cd python
  python scripts/run/run_backend.py

或从项目根：
  python python/scripts/run/run_backend.py

启动后：
  - 接口文档（Swagger）： http://127.0.0.1:8000/docs
  - 接口文档（ReDoc）：   http://127.0.0.1:8000/redoc
  - 健康检查：           http://127.0.0.1:8000/health
"""
import os
import sys

# 保证以 python 目录为工作目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
os.chdir(PYTHON_DIR)
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

HOST = "0.0.0.0"
PORT = 8000


def main():
    base = f"http://127.0.0.1:{PORT}"
    print("=" * 60)
    print("  Python RAG 服务启动中...")
    print("=" * 60)
    print(f"  健康检查:     {base}/health")
    print(f"  接口文档(Swagger): {base}/docs")
    print(f"  接口文档(ReDoc):   {base}/redoc")
    print("=" * 60)

    import uvicorn
    from api.server import app

    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
