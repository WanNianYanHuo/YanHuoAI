# config/settings.py

from config.runtime import CURRENT_KB
import os

# 固定为 python 目录下的 knowledge_bases，与运行时的 cwd 无关（始终从 python 跑）
_PYTHON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_ROOT = os.path.join(_PYTHON_DIR, "knowledge_bases")

DB_FILE = os.path.join(KB_ROOT, CURRENT_KB, "docs.db")
FAISS_FILE = os.path.join(KB_ROOT, CURRENT_KB, "faiss.index")


# ===== Embedding 配置 =====
# 可选: "local" | "dashscope"
# 运行在线环境时推荐使用阿里云 DashScope，避免在服务器上加载本地大模型。
EMBEDDING_BACKEND = "dashscope"

# 本地 Embedding 配置（当 EMBEDDING_BACKEND="local" 时使用）
EMBEDDING_MODEL = "BAAI/bge-small-zh"
LOCAL_EMBEDDING_DIM = 512  # bge-small-zh 的向量维度是 512

# DashScope Embedding 配置（当 EMBEDDING_BACKEND="dashscope" 时使用）
DASHSCOPE_API_KEY = "sk-53d8334b345843d9a34da788f55aa4e8"  # 请替换为你的 API Key
DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v1"  # DashScope 的文本嵌入模型
DASHSCOPE_EMBEDDING_DIM = 1536  # text-embedding-v1 的向量维度

# 统一给 kb_manager 使用的向量维度
if EMBEDDING_BACKEND == "dashscope":
    EMBEDDING_DIM = DASHSCOPE_EMBEDDING_DIM
else:
    EMBEDDING_DIM = LOCAL_EMBEDDING_DIM

# Embedding 缓存配置
EMBEDDING_CACHE_ENABLED = True
EMBEDDING_CACHE_DIR = os.path.join(KB_ROOT, "_embedding_cache")

DOC_FOLDER = "./docs"
TXT_FOLDER = "./demo/txt_data"
OLLAMA_URL = "http://10.10.52.215:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:70b"
OLLAMA_TIMEOUT = 600  # 大模型/云模型响应慢，单位秒（671b 建议 300～600）

# 检索 Top K：值越大召回越多但容易引入噪声
TOP_K = 3  # 根据需求调整为 3
PREVIEW_CHARS = 200

# 文档切分长度
CHUNK_SIZE = 500  # 文档切分长度：500 字符
CHUNK_OVERLAP = 50  # 切分重叠：50 字符

# ===== Rerank 配置 =====
# 可选: "local" | "dashscope"
RERANK_BACKEND = "dashscope"  # 使用阿里云 DashScope qwen3-vl-rerank

# DashScope Rerank 配置
DASHSCOPE_RERANK_MODEL = "qwen3-vl-rerank"
RERANK_TOP_N = 10  # 仅处理前 10 个文档以降低成本（标准做法：检索 Top50 → Rerank Top10 → LLM Top3）

# ===== LLM backend =====
LLM_BACKEND = "zhipu"   # 可选: "ollama" | "zhipu"

# ===== 推理链 (Chain of Thought) =====
# 启用推理链思考模式，配合智能路由使用
USE_COT = True           # 是否启用推理链思考模式，True=启用，False=禁用
USE_STRUCTURED_COT = False  # 先关闭结构化 JSON 输出，后续需要再开启

# ===== ZhipuAI =====
ZHIPU_API_KEY = "423f6cd5e21943c196f6899d1a496665.wsWjaFurFniStfj2"
ZHIPU_MODEL = "glm-4-flash"   # 或 glm-3-turbo