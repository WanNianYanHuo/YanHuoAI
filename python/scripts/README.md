# 脚本工具

本目录存放与项目相关的独立脚本，供开发/运维使用。

## 启动脚本（scripts/run/）

| 脚本 | 说明 |
|------|------|
| `run/run_backend.py` | 启动 RAG 后端服务（需在 python 目录下执行，或使用根目录 `python run.py`） |
| `run/run_backend.bat` | Windows 一键启动后端（会先 cd 到 python 目录再执行） |

## 其他脚本

| 脚本 | 说明 |
|------|------|
| `pull_ollama_model.py` | 从本地 Ollama 服务拉取模型，默认 `deepseek-v3.1:671b-cloud`，需先启动 Ollama |
| `kb_validate_and_repair.py` | 知识库验证与修复：验证 `knowledge_bases` 完整性，或执行 `repair` 创建缺失目录/映射；支持 `status` 查看状态。建议启动服务器前在 `python/` 下运行一次 |

## 测试工具

数据库与后端图形测试工具已整合到 **test/** 目录：`test/db_and_backend_test_tool.py`。

运行前请确保已激活项目虚拟环境（如 `python/env`）并安装依赖（如 `pymysql`、`requests`）。
