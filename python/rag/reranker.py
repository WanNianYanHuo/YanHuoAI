from llm.ollama_client import call_llm
from config.settings import RERANK_BACKEND


def _content_str(doc):
    """文档内容统一为字符串，避免 DataFrame 等类型进入 LLM 或序列化。"""
    c = getattr(doc, "content", "")
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if hasattr(c, "to_string"):
        return c.to_string()
    if hasattr(c, "to_json"):
        return c.to_json()
    return str(c)


def rerank_documents(question, docs, top_n=5):
    """
    【论文注释】
    本模块利用大语言模型或专用 Rerank API 对初步召回的候选文档进行相关性重排序，
    以弥补向量检索在语义细粒度判断上的不足。
    
    支持两种后端：
    1. local: 使用本地 LLM 进行重排序
    2. dashscope: 使用阿里云 DashScope Rerank API
    """

    if not docs:
        return []
    
    backend = RERANK_BACKEND.lower()
    
    if backend == "dashscope":
        # 使用 DashScope Rerank API
        return _rerank_with_dashscope(question, docs, top_n)
    elif backend == "local":
        # 使用本地 LLM
        return _rerank_with_local_llm(question, docs, top_n)
    else:
        print(f"[RERANK] 不支持的后端: {backend}，使用原始排序")
        return docs[:top_n]


def _rerank_with_dashscope(question, docs, top_n=5):
    """使用 DashScope API 进行重排序"""
    try:
        from rerank.dashscope_rerank import rerank_documents_with_dashscope
        
        reranked = rerank_documents_with_dashscope(
            query=question,
            documents=docs,
            top_n=top_n
        )
        
        return reranked
        
    except Exception as e:
        print(f"[RERANK] DashScope 重排序失败，使用原始排序: {e}")
        return docs[:top_n]


def _rerank_with_local_llm(question, docs, top_n=5):
    """使用本地 LLM 进行重排序"""
    scored_docs = []

    for doc in docs:
        prompt = f"""
问题：
{question}

候选文档内容：
{_content_str(doc)}

请判断该文档与问题的相关性，给出 0-10 的整数评分。
只输出数字。
"""
        try:
            resp = call_llm(prompt)
            score = int(resp.strip())
        except Exception:
            score = 0

        scored_docs.append((score, doc))

    # 按评分排序
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    # 【工程兜底】如果所有评分为 0，仍然返回原顺序前 top_n
    if all(score == 0 for score, _ in scored_docs):
        return docs[:top_n]

    reranked = []
    for score, doc in scored_docs[:top_n]:
        doc.score = float(score)
        reranked.append(doc)

    return reranked
