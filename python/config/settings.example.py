# config/settings.example.py
# 配置文件示例 - 复制此文件为 settings.py 并修改配置

from config.runtime import CURRENT_KB
import os

# 固定为 python 目录下的 knowledge_bases（与运行时 cwd 无关）
_PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_ROOT = os.path.join(_PYTHON_DIR, "knowledge_bases")

DB_FILE = os.path.join(KB_ROOT, CURRENT_KB, "docs.db")
FAISS_FILE = os.path.join(KB_ROOT, CURRENT_KB, "faiss.index")


# ===== Embedding 配置 =====
# 可选: "local" | "dashscope"
EMBEDDING_BACKEND = "dashscope"  # 推荐使用 DashScope

# 本地 Embedding 配置（当 EMBEDDING_BACKEND="local" 时使用）
EMBEDDING_MODEL = "BAAI/bge-small-zh"
EMBEDDING_DIM = 512

# DashScope Embedding 配置（当 EMBEDDING_BACKEND="dashscope" 时使用）
DASHSCOPE_API_KEY = "YOUR_DASHSCOPE_API_KEY"  # ⚠️ 必须替换为你的 API Key
DASHSCOPE_EMBEDDING_MODEL = "qwen3-vl-embedding"
DASHSCOPE_EMBEDDING_DIM = 1536

# Embedding 缓存配置
EMBEDDING_CACHE_ENABLED = True  # 强烈推荐启用
EMBEDDING_CACHE_DIR = os.path.join(KB_ROOT, "_embedding_cache")

DOC_FOLDER = "./docs"
TXT_FOLDER = "./demo/txt_data"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"
OLLAMA_TIMEOUT = 600

# 检索 Top K
TOP_K = 3
PREVIEW_CHARS = 200

# 文档切分长度
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ===== Rerank 配置 =====
# 可选: "local" | "dashscope"
RERANK_BACKEND = "dashscope"  # 推荐使用 DashScope

# DashScope Rerank 配置
DASHSCOPE_RERANK_MODEL = "qwen3-vl-rerank"
RERANK_TOP_N = 10  # 仅处理前 10 个文档以降低成本

# ===== LLM backend =====
LLM_BACKEND = "zhipu"   # 可选: "ollama" | "zhipu"

# ===== 推理链 (Chain of Thought) =====
USE_COT = False
USE_STRUCTURED_COT = False

# ===== ZhipuAI =====
ZHIPU_API_KEY = "YOUR_ZHIPU_API_KEY"  # ⚠️ 必须替换为你的 API Key
ZHIPU_MODEL = "glm-4-flash"
