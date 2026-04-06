# rag/qa_pipeline.py

import time
import logging
import sys
from llm.ollama_client import call_llm
from config.settings import PREVIEW_CHARS, TOP_K, USE_COT, USE_STRUCTURED_COT
from rag.reranker import rerank_documents
from rag.chain_of_thought import generate_with_cot, ReasoningChain
from rag.smart_router import smart_route
from utils.unanswered_logger import log_unanswered_question
from typing import Tuple, Optional, Any


# 设置日志过滤器，隐藏技术性模型加载信息
class TechnicalLogFilter(logging.Filter):
    """过滤技术性日志消息，如模型加载进度条等"""
    
    def filter(self, record):
        message = record.getMessage()
        # 过滤掉技术性日志
        technical_keywords = [
            "Loading weights:",
            "BertModel LOAD REPORT",
            "UNEXPECTED",
            "can be ignored when loading from different task/architecture",
            "Batches:",
            "100%|",
            "█████",
            "it/s]"
        ]
        
        for keyword in technical_keywords:
            if keyword in message:
                return False
        return True

# 应用日志过滤器到相关的日志记录器
def setup_log_filtering():
    """设置日志过滤，隐藏技术性消息"""
    # 获取常见的技术日志记录器
    loggers_to_filter = [
        'transformers',
        'sentence_transformers', 
        'torch',
        'tqdm',
        'urllib3',
        'requests'
    ]
    
    filter_instance = TechnicalLogFilter()
    
    for logger_name in loggers_to_filter:
        logger = logging.getLogger(logger_name)
        logger.addFilter(filter_instance)
        # 设置较高的日志级别，只显示警告和错误
        logger.setLevel(logging.WARNING)

# 在模块加载时设置日志过滤
setup_log_filtering()


def _doc_content_to_str(content: Any, max_chars: Optional[int] = None) -> str:
    """将 Document.content 转为字符串，避免 DataFrame 进入 Pydantic/JSON 导致 schema 错误。"""
    if content is None:
        return ""
    if isinstance(content, str):
        s = content
    else:
        try:
            if hasattr(content, "to_string"):
                s = content.to_string()
            elif hasattr(content, "to_json"):
                s = content.to_json()
            else:
                s = str(content)
        except Exception:
            s = str(content)
    if max_chars is not None and len(s) > max_chars:
        return s[:max_chars]
    return s


def _meta_to_serializable(meta: Optional[dict]) -> Optional[dict]:
    """确保 meta 仅含可 JSON 序列化的值，避免 DataFrame/ndarray 等触发 Pydantic 错误。"""
    if not meta:
        return meta
    out = {}
    for k, v in meta.items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, dict):
            out[k] = _meta_to_serializable(v) or {}
        elif isinstance(v, (list, tuple)):
            out[k] = [
                x if isinstance(x, (str, int, float, bool, type(None))) else str(x)
                for x in v
            ]
        else:
            out[k] = str(v)
    return out


def _is_context_useful(docs, min_docs=3, min_score=0.6):
    """
    【论文注释】
    判断检索到的上下文是否具备回答价值
    """
    if not docs:
        return False

    valid_docs = [
        d for d in docs
        if getattr(d, "score", 1.0) >= min_score
    ]
    # 至少有若干条文档达到更高相似度时，才认为上下文可靠，避免低相关度文档驱动回答
    return len(valid_docs) >= min_docs


def qa_ask(
    question: str,
    retriever,
    use_cot: Optional[bool] = None,
    return_reasoning: bool = False,
    stream_callback=None,
    on_complete=None,
    llm_backend=None,
    kb_id: Optional[str] = None,
    use_kb: bool = True,
    use_smart_router: bool = False,  # 是否使用智能路由
    progress_callback=None,  # 进度回调函数
):
    """
    多阶段 RAG 问答流程：向量检索 → 扩大召回 → 重排序 → 上下文评估 → 回答生成（可选推理链）。
    返回含 timing 统计（retrieve_time, rerank_time, generate_time, total_time），可选推理链。
    
    Args:
        use_smart_router: 是否使用智能路由自动判断问题复杂度

    Returns:
        (答案文本, 引用列表, reasoning_chain 或 None, timing_dict)
        timing_dict 为 None 表示未统计（如提前返回）。
    """
    if use_cot is None:
        use_cot = USE_COT

    start_total = time.time()
    timing = {
        "retrieve_time": 0.0,
        "rerank_time": 0.0,
        "generate_time": 0.0,
        "total_time": 0.0,
        "router_time": 0.0,  # 路由耗时
    }
    
    # ========= 0️⃣ 智能路由（可选） =========
    router_result = None
    actual_question = question  # 实际用于检索的问题
    
    if use_smart_router:
        if progress_callback:
            progress_callback("智能路由", "正在分析问题复杂度...")
        
        # 使用安全的智能路由，带超时和后备机制
        try:
            # 避免循环导入，在运行时导入
            import importlib
            server_module = importlib.import_module('api.server')
            router_result = server_module.safe_smart_route(question, llm_backend)
        except (ImportError, AttributeError):
            # 如果无法导入安全路由，回退到原始路由
            router_result = smart_route(question, llm_backend)
        
        timing["router_time"] = router_result["timing"]["total_time"]
        
        # 根据路由结果决定是否使用 CoT
        if router_result["strategy"] == "cot_rag":
            use_cot = True
            # 使用重写后的问题进行检索
            actual_question = router_result["rewritten_question"]
            if progress_callback:
                progress_callback("重写问题", "正在优化问题表述...")
            print(f"[ROUTER] 复杂问题，使用 CoT 模式，重写问题: {actual_question}")
        else:
            use_cot = False
            print(f"[ROUTER] 简单问题，使用普通 RAG 模式")
        
        # 保存路由信息到 timing
        timing["router_info"] = {
            "complexity": router_result["complexity"],
            "strategy": router_result["strategy"],
            "rewritten_question": router_result["rewritten_question"],
            "keywords": router_result["keywords"],
        }

    docs = []
    context_valid = False
    context = ""

    # ========= 1️⃣ 初始向量检索（可选） =========
    if use_kb and retriever is not None:
        if progress_callback:
            progress_callback("知识检索", "正在搜索相关文档...")
            
        from storage.retriever import get_text_embedder
        
        start_retrieve = time.time()
        
        # Haystack 2.x: 使用 text embedder 生成查询嵌入
        embedder = get_text_embedder()
        
        # 使用实际问题（可能是重写后的）进行检索
        query_result = embedder.run(text=actual_question)
        query_embedding = query_result["embedding"]
        
        # 使用 document store 的 search 方法
        docs = retriever.search(
            query_embedding=query_embedding,
            top_k=TOP_K
        )
        
        if not docs or len(docs) < 3:
            if progress_callback:
                progress_callback("扩展检索", "正在扩大搜索范围...")
            expand_query = question + " 诊疗 指南 共识 建议"
            query_result = embedder.run(text=expand_query)
            query_embedding = query_result["embedding"]
            docs = retriever.search(
                query_embedding=query_embedding,
                top_k=TOP_K * 3
            )
        timing["retrieve_time"] = round(time.time() - start_retrieve, 3)

        if not docs:
            # 知识库完全无命中：记录日志，但后续仍让模型基于通识作答
            log_unanswered_question(question, reason="知识库中未检索到相关文档，将退回模型通识回答")

        # ========= 3️⃣ 重排序 =========
        if progress_callback:
            progress_callback("重排序", "正在优化文档相关性...")
            
        start_rerank = time.time()
        try:
            reranked = rerank_documents(question, docs, top_n=5)
            if reranked:
                docs = reranked
        except Exception as e:
            print("重排序失败，回退原始排序：", e)
        docs = docs[:5]
        timing["rerank_time"] = round(time.time() - start_rerank, 3)

        # ========= 4️⃣ 上下文有效性判定 =========
        context_valid = _is_context_useful(docs)
        if not context_valid:
            # 记录一次"知识库未提供有效支撑"的情况，后续改为通识回答
            log_unanswered_question(question, reason="检索到的内容相关度过低，将退回模型通识回答")

        # ========= 5️⃣ 构造上下文 =========
        if progress_callback:
            progress_callback("上下文构建", "正在构建回答上下文...")
        context = "\n".join(f"[{i+1}] {_doc_content_to_str(d.content)}" for i, d in enumerate(docs))

    # ========= 6️⃣ 生成答案 =========
    reasoning_chain = None
    start_generate = time.time()
    if use_cot:
        if progress_callback:
            progress_callback("深度推理", "正在启动推理链分析...")
        # 若上下文无效，则传入空上下文，等价于"纯模型通识回答"
        used_context = context if context_valid else ""
        answer, reasoning_chain = generate_with_cot(
            question=question,
            context=used_context,
            compact=False,
            extract_answer_only=not return_reasoning,
            stream_callback=stream_callback,
            on_complete=on_complete,
            llm_backend=llm_backend,
            # 流式输出时禁用结构化 JSON（否则模型会把 JSON 模板逐段输出到前端）
            use_structured=bool(USE_STRUCTURED_COT and stream_callback is None),
            progress_callback=progress_callback,  # 传递进度回调给 CoT
        )
    else:
        if progress_callback:
            progress_callback("答案生成", "正在生成回答...")
        # 普通模式：不再使用外部模板文件，但在这里给出简单指令，
        # 明确要求“不要重复分析资料和问题”，只给简洁结论。
        if context_valid and use_kb:
            # 有有效知识库上下文时：把上下文和问题给模型，并强调不要复述上下文
            prompt = (
                "你是专业的中医问答助手。下面是与用户问题相关的资料，请在心里阅读并理解，"
                "但在回答中不要逐字复述这些资料内容，也不要长篇解释你是如何分析资料的，"
                "只需综合资料给出简明结论。\n\n"
                f"{context}\n\n"
                f"用户问题：{question}\n\n"
                "请用简体中文直接回答这个问题，重点给出结论和关键依据，"
                "不要重复地描述“分析资料”“理解问题”等过程，"
                "整体长度控制在 1-2 段话之内。"
            )
        else:
            # 无有效上下文或未使用知识库时：直接用问题，要求简洁回答
            prompt = (
                "你是专业的中医问答助手。\n\n"
                f"用户问题：{question}\n\n"
                "请用简体中文直接、简洁地回答这个问题，"
                "不要重复地描述“分析问题”“整理思路”等过程，也不要自我解释，"
                "控制在 1-2 段话之内。"
            )

        # 创建包装的完成回调，发送完成进度
        def wrapped_on_complete(timing):
            if progress_callback:
                progress_callback("生成完成", "回答生成完毕...")
            if on_complete:
                on_complete(timing)

        answer = call_llm(
            prompt,
            stream_callback=stream_callback,
            on_complete=wrapped_on_complete,
            backend=llm_backend,
        )
        if not answer:
            answer = "模型未能生成有效回答。"
    timing["generate_time"] = round(time.time() - start_generate, 3)
    timing["total_time"] = round(time.time() - start_total, 3)
    _log_timing(kb_id, timing)

    # 标记此次回答是否实际使用了知识库上下文
    timing["kb_used"] = bool(use_kb and context_valid)

    # 保存所有检索到的文档（用于调试模式）
    if use_kb and docs:
        all_docs = [
            {
                "content": _doc_content_to_str(d.content, PREVIEW_CHARS),
                "meta": _meta_to_serializable(getattr(d, "meta", None)),
                "score": getattr(d, "score", None),
            }
            for d in docs[:10]  # 最多返回前10条
        ]
        timing["all_docs"] = all_docs
    else:
        timing["all_docs"] = []

    # 若未使用知识库，则不返回引用文献，并在回答末尾追加简单提示
    if use_kb and context_valid:
        refs = [
            {
                "content": _doc_content_to_str(d.content, PREVIEW_CHARS),
                "meta": _meta_to_serializable(getattr(d, "meta", None)),
                "score": getattr(d, "score", None),
            }
            for d in docs
        ]
    else:
        refs = []
        if use_kb:
            answer = f"{answer}\n\n（提示：未在当前知识库中检索到足够相关的内容，本回答主要基于模型通识推理。）"
        else:
            answer = f"{answer}\n\n（提示：本次回答未使用知识库检索，仅基于模型通识推理。）"
    if return_reasoning:
        return answer, refs, reasoning_chain, timing
    return answer, refs, None, timing


def _log_timing(kb_id: Optional[str], timing: dict):
    """控制台打印: [KB=zhongyi] retrieve=0.23 rerank=0.41 generate=1.32 total=2.12"""
    kb = kb_id or "default"
    parts = " ".join(f"{k}={v}" for k, v in timing.items() if isinstance(v, (int, float)))
    print(f"[KB={kb}] {parts}")
