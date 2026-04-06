import requests
from typing import List, Any

# Haystack 2.x: 使用新的组件系统（本地模型时使用）
from haystack.components.embedders import (
    SentenceTransformersTextEmbedder,
    SentenceTransformersDocumentEmbedder,
)
from haystack.utils.device import ComponentDevice
from config.settings import (
    EMBEDDING_MODEL,
    EMBEDDING_BACKEND,
    DASHSCOPE_API_KEY,
    DASHSCOPE_EMBEDDING_MODEL,
)


def get_retriever(document_store):
    """
    【论文注释】
    本函数构建基于向量相似度的语义检索器（Embedding Retriever），
    用于在向量数据库中召回与用户问题语义最相近的文档片段。
    
    注意：Haystack 2.x 中，retriever 直接从 document_store 获取，
    不再需要单独的 EmbeddingRetriever 类。
    
    返回：document_store 本身，因为在 Haystack 2.x 中，
    document_store 提供了 search 方法。
    """
    # Haystack 2.x: document_store 本身就可以用于检索
    # 实际的检索逻辑在 kb_manager 中通过 document_store 的方法实现
    return document_store


def get_text_embedder():
    """
    获取文本嵌入器（用于查询）
    """
    if EMBEDDING_BACKEND == "dashscope":
        return DashScopeTextEmbedder()

    embedder = SentenceTransformersTextEmbedder(
        model=EMBEDDING_MODEL,
        device=ComponentDevice.from_str("cpu"),  # 使用本地模型
    )
    embedder.warm_up()
    return embedder


def get_document_embedder():
    """
    获取文档嵌入器（用于文档索引）
    """
    if EMBEDDING_BACKEND == "dashscope":
        return DashScopeDocumentEmbedder()

    embedder = SentenceTransformersDocumentEmbedder(
        model=EMBEDDING_MODEL,
        device=ComponentDevice.from_str("cpu"),  # 使用本地模型
    )
    embedder.warm_up()
    return embedder


class DashScopeTextEmbedder:
    """
    使用阿里云 DashScope Embedding 的查询向量生成器。
    提供与 Haystack Embedder 兼容的 run(text=...) 接口。
    """

    def __init__(self):
        if not DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY 未配置，请在 config/settings.py 中设置")
        self.api_key = DASHSCOPE_API_KEY
        self.model = DASHSCOPE_EMBEDDING_MODEL
        self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    def _embed(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }
        resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data:
            raise RuntimeError(f"DashScope Embedding 响应异常: {data}")
        return [item["embedding"] for item in data["data"]]

    def run(self, text: str):
        """
        与 SentenceTransformersTextEmbedder.run 保持一致，返回 {"embedding": [...]}
        """
        if not text:
            return {"embedding": []}
        embeddings = self._embed([text])
        return {"embedding": embeddings[0]}


class DashScopeDocumentEmbedder:
    """
    使用阿里云 DashScope Embedding 的文档向量生成器。
    提供与 Haystack DocumentEmbedder 兼容的 run(documents=[...]) 接口。
    """

    def __init__(self):
        if not DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY 未配置，请在 config/settings.py 中设置")
        self.api_key = DASHSCOPE_API_KEY
        self.model = DASHSCOPE_EMBEDDING_MODEL
        self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    def _embed(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }
        resp = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data:
            raise RuntimeError(f"DashScope Embedding 响应异常: {data}")
        return [item["embedding"] for item in data["data"]]

    def run(self, documents: List[Any]):
        """
        与 SentenceTransformersDocumentEmbedder.run 保持一致，
        返回 {"documents": 带有 embedding 向量的 Document 列表}
        """
        if not documents:
            return {"documents": []}

        # 提取文本内容
        texts: List[str] = []
        for d in documents:
            content = getattr(d, "content", "") or ""
            if not isinstance(content, str):
                content = str(content)
            texts.append(content)

        vectors = self._embed(texts)

        # 将向量挂到 Document.embedding 上，Haystack 2.x 会识别
        for d, emb in zip(documents, vectors):
            setattr(d, "embedding", emb)

        return {"documents": documents}

