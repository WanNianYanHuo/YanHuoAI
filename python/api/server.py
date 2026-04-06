# -*- coding: utf-8 -*-
"""
RAG 统一 API 服务：供 前端调用，与 Vue 前端形成 前端 -> Python 链路。
使用 Haystack 2.x 和 Pydantic v2。
"""
import json
import os
import sys
import threading
import time
import uuid
import queue
from typing import Optional, List, Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 保证项目根在 path 中（以 python 目录为 cwd 启动时）
sys.path.insert(0, ".")

from api import auth_api
from rag.qa_pipeline import qa_ask
from llm.ollama_client import call_llm
from rag.kb_manager import (
    kb_manager,
    _resolve_kb_id as _resolve_kb_id_internal,
    get_storage_key,
    get_display_id,
    list_storage_keys,
    remove_mapping_for_display_id,
)
from config.settings import USE_COT, KB_ROOT

# Haystack 2.x: 导入 DuplicatePolicy
from haystack.document_stores.types import DuplicatePolicy


# 简单的内存级导入任务管理（单进程）
_IMPORT_TASKS: Dict[str, Dict[str, Any]] = {}
_IMPORT_LOCK = threading.Lock()

# 智能路由配置
SMART_ROUTER_TIMEOUT = 10  # 智能路由超时时间（秒）- 从30秒减少到10秒
USE_SIMPLE_ROUTER_FALLBACK = True  # 是否启用简化路由作为后备


def _normalize_for_dedupe(text: Any) -> str:
    """用于去重的归一化：去掉首尾空白并压缩中间空白。"""
    if text is None:
        return ""
    s = str(text).strip()
    if not s:
        return ""
    import re
    return re.sub(r"\s+", " ", s)


def _stable_doc_id_from_content(text: Any) -> str:
    """同样内容得到同样 id，用于自动跳过重复数据。"""
    norm = _normalize_for_dedupe(text)
    import hashlib
    h = hashlib.sha1(norm.encode("utf-8")).hexdigest()
    return f"doc_{h}"


def safe_smart_route(question: str, llm_backend: Optional[str] = None, timeout: int = SMART_ROUTER_TIMEOUT):
    """
    安全的智能路由调用，带超时和后备机制
    """
    def run_smart_route(q, question, backend):
        try:
            from rag.smart_router import smart_route
            result = smart_route(question, backend)
            q.put(("success", result))
        except Exception as e:
            q.put(("error", str(e)))
    
    print(f"[SAFE_ROUTER] 开始智能路由，超时: {timeout}s")
    
    # 使用线程和队列实现超时机制
    q = queue.Queue()
    thread = threading.Thread(target=run_smart_route, args=(q, question, llm_backend))
    
    start_time = time.time()
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        elapsed = time.time() - start_time
        print(f"[SAFE_ROUTER] 智能路由超时 ({elapsed:.1f}s)，切换到简化版本")
        
        if USE_SIMPLE_ROUTER_FALLBACK:
            try:
                from rag.smart_router_simple import smart_route_simple
                result = smart_route_simple(question, llm_backend)
                print(f"[SAFE_ROUTER] 简化路由成功: {result['strategy']}")
                return result
            except Exception as e:
                print(f"[SAFE_ROUTER] 简化路由也失败: {e}")
                # 返回默认结果
                return {
                    "complexity": "simple",
                    "strategy": "simple_rag",
                    "rewritten_question": question,
                    "keywords": "",
                    "timing": {"total_time": elapsed}
                }
        else:
            # 返回默认结果
            return {
                "complexity": "simple",
                "strategy": "simple_rag", 
                "rewritten_question": question,
                "keywords": "",
                "timing": {"total_time": elapsed}
            }
    else:
        # 正常完成
        elapsed = time.time() - start_time
        try:
            status, result = q.get_nowait()
            if status == "success":
                print(f"[SAFE_ROUTER] 智能路由成功: {result['strategy']}, 耗时: {elapsed:.2f}s")
                return result
            else:
                print(f"[SAFE_ROUTER] 智能路由失败: {result}")
                if USE_SIMPLE_ROUTER_FALLBACK:
                    from rag.smart_router_simple import smart_route_simple
                    return smart_route_simple(question, llm_backend)
                else:
                    return {
                        "complexity": "simple",
                        "strategy": "simple_rag",
                        "rewritten_question": question,
                        "keywords": "",
                        "timing": {"total_time": elapsed}
                    }
        except queue.Empty:
            print(f"[SAFE_ROUTER] 智能路由无响应")
            return {
                "complexity": "simple",
                "strategy": "simple_rag",
                "rewritten_question": question,
                "keywords": "",
                "timing": {"total_time": elapsed}
            }


app = FastAPI(
    title="RAG API",
    description="知识库问答接口，供前端调用",
    version="1.0",
)

# 允许浏览器前端直接跨域访问（包括预检 OPTIONS）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # 如需更严格可改为具体前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载认证与用户/知识库管理路由（/api/v1/...）
app.include_router(auth_api.router)

# 挂载进度状态管理路由
from api import progress_api
from api.progress_api import create_progress_callback, complete_progress, update_progress
app.include_router(progress_api.router)

# 挂载管理员路由（/api/v1/admin/...）
from api import admin_api
app.include_router(admin_api.router)


# ---------- 请求/响应模型 ----------
class RagAskRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = None
    kb_id: Optional[str] = None  # 未传或 "default" 时 fallback 到 CURRENT_KB
    llm_backend: Optional[str] = None  # "ollama" | "zhipu"
    use_cot: Optional[bool] = None
    use_kb: Optional[bool] = True
    use_smart_router: Optional[bool] = False  # 是否使用智能路由
    progress_session_id: Optional[str] = None  # 进度会话ID


class ChatBasicRequest(BaseModel):
    """
    纯大模型对话请求：不经过 RAG / 推理链，只做最小可用对话能力。
    """
    question: str
    llm_backend: Optional[str] = None  # "ollama" | "zhipu"


class ChatBasicResponse(BaseModel):
    """
    纯大模型对话响应。
    """
    answer: str


class RefItem(BaseModel):
    content: str
    meta: Optional[dict] = None
    score: Optional[float] = None


class RagAskResponse(BaseModel):
    answer: str
    refs: List[RefItem]
    reasoning: Optional[str] = None
    reasoning_json: Optional[str] = None  # 结构化 CoT 的 JSON，供 Java 存储
    timing: Optional[dict] = None


class KbInfo(BaseModel):
    kb_id: str
    kb_name: str


class AddTextRequest(BaseModel):
    kb_id: str
    content: str


class DocPreview(BaseModel):
    id: str
    content_preview: str
    meta: Optional[dict] = None


class DocDetail(BaseModel):
    id: str
    content: str
    meta: Optional[dict] = None


class DocUpdateRequest(BaseModel):
    kb_id: str
    doc_id: str
    content: str


class DocDeleteRequest(BaseModel):
    kb_id: str
    doc_id: str


class KbCreateRequest(BaseModel):
    kb_id: str


class KbDeleteRequest(BaseModel):
    kb_id: str


def _refs_to_list(refs: list) -> List[RefItem]:
    return [
        RefItem(
            content=r.get("content", ""),
            meta=r.get("meta"),
            score=r.get("score"),
        )
        for r in (refs or [])
    ]


@app.get("/health")
def health():
    """健康检查，供 前端 探测 Python 服务是否可用"""
    return {"status": "ok", "service": "rag-api"}


def _stream_basic(question: str, llm_backend: Optional[str]):
    """
    纯大模型对话的流式生成：
    - 不经过知识库检索
    - 不启用推理链 / 结构化输出
    SSE payload 与 /rag/ask/stream 保持风格一致（message + done）。
    """
    chunks: List[str] = []

    def collect(chunk: str):
        chunks.append(chunk)

    try:
        answer = call_llm(
            question,
            stream_callback=collect,
            on_complete=None,
            backend=llm_backend,
        )
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        return

    # 若后端未实际触发流式回调，则用完整 answer 兜底
    if not chunks and answer:
        chunks.append(answer)

    for chunk in chunks:
        payload = {"message": {"content": chunk}, "done": False}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    final_payload = {
        "message": {"content": ""},
        "done": True,
        "done_reason": "stop",
    }
    yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"


@app.post("/chat/basic/stream")
def chat_basic_stream(req: ChatBasicRequest):
    """
    纯对话流式接口：
    - 不用知识库（无 RAG）
    - 不启用推理链 / 结构化输出
    - 返回 SSE 流，前端可使用 EventSource / 流式 fetch 消费
    """
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    return StreamingResponse(
        _stream_basic(question, req.llm_backend),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat/basic", response_model=ChatBasicResponse)
def chat_basic(req: ChatBasicRequest):
    """
    最小可用对话接口：
    - 不经过知识库检索（不使用 RAG）
    - 不启用推理链 / 结构化输出
    仅将用户问题直接转发给当前配置的大模型后返回答案。
    """
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    # 直接调用统一 LLM 封装；后续如需系统提示可在这里最小范围扩展
    answer = call_llm(
        question,
        stream_callback=None,
        on_complete=None,
        backend=req.llm_backend,
    )
    if not answer:
        answer = "模型未能生成有效回答。"
    return ChatBasicResponse(answer=answer)


@app.get("/knowledge/bases", response_model=List[KbInfo])
def list_knowledge_bases():
    """
    列出可用知识库：扫描 KB_ROOT 下的子目录（存储目录名），返回对用户展示的 kb_id/kb_name。
    含中文等非 ASCII 名称会映射为 ASCII 存储目录：
      - kb_id:   对外暴露的“知识库 ID”（storage_key，例如 kb_0001）
      - kb_name: 对用户展示的名称（原始中文/自定义名称）
    """
    kbs: List[KbInfo] = []
    for storage_key in list_storage_keys():
        display_id = get_display_id(storage_key)
        # kb_id 使用内部存储目录名（保证 ASCII/稳定），kb_name 使用映射后的展示名
        kbs.append(KbInfo(kb_id=storage_key, kb_name=display_id))
    return kbs


def _resolve_kb_id(kb_id: Optional[str]) -> str:
    """与 kb_manager 一致：未传或 default/haystack 时用 CURRENT_KB。"""
    return _resolve_kb_id_internal(kb_id)


@app.post("/knowledge/create")
def knowledge_create(req: KbCreateRequest):
    """
    新建知识库目录：仅创建 knowledge_bases/{storage_key} 目录（非 ASCII 名会映射为 ASCII），不写入任何文档。
    若已存在则返回 400。
    """
    kb_id = (req.kb_id or "").strip()
    if not kb_id:
        raise HTTPException(status_code=400, detail="kb_id 不能为空")
    storage_key = get_storage_key(kb_id)
    kb_dir = os.path.join(KB_ROOT, storage_key)
    if os.path.exists(kb_dir):
        raise HTTPException(status_code=400, detail="该知识库已存在")
    try:
        os.makedirs(kb_dir, exist_ok=False)
        return {"kb_id": kb_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {e}")


@app.post("/knowledge/delete")
def knowledge_delete(req: KbDeleteRequest):
    """
    删除指定知识库目录及其内容（docs.db / faiss.index 等）。
    """
    kb_id_raw = (req.kb_id or "").strip()
    if not kb_id_raw:
        raise HTTPException(status_code=400, detail="kb_id 不能为空")
    # 兼容两种传参形式：
    #  - 传展示名（中文等）时，通过映射解析到 storage_key
    #  - 传 storage_key（kb_0001 等）时，直接作为物理目录名
    storage_key = get_storage_key(kb_id_raw)
    display_id = get_display_id(storage_key)
    kb_dir = os.path.join(KB_ROOT, storage_key)
    try:
        import shutil
        if os.path.isdir(kb_dir):
            shutil.rmtree(kb_dir)
            # 从映射中移除展示名（若存在）；优先使用映射得到的展示名，其次退回到原始传入值
            remove_mapping_for_display_id(display_id or kb_id_raw)
            return {"kb_id": kb_id_raw, "status": "deleted"}

        # 兜底：历史版本可能直接创建了中文目录（未走映射），映射目录不存在时尝试删除原始目录
        legacy_dir = os.path.join(KB_ROOT, kb_id_raw)
        if os.path.isdir(legacy_dir):
            shutil.rmtree(legacy_dir)
            remove_mapping_for_display_id(display_id or kb_id_raw)
            return {"kb_id": kb_id_raw, "status": "deleted"}

        raise HTTPException(status_code=404, detail="知识库不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {e}")


@app.post("/knowledge/add_text")
def knowledge_add_text(req: AddTextRequest):
    """
    向指定知识库追加一段纯文本内容：
      1. 利用 rag.kb_manager 为该 kb_id 获取/创建文档库
      2. 生成文档 embedding
      3. 写入文档并保存 FAISS 索引
    """
    import traceback
    from haystack import Document

    display_id = (req.kb_id or "").strip()
    resolved = _resolve_kb_id(req.kb_id)
    text = (req.content or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="content 不能为空")

    try:
        # 1️⃣ 获取/创建指定知识库的 DocumentStore（resolved 为 ASCII 存储目录名）
        from rag.kb_manager import _get_document_store_for_kb
        from storage.retriever import get_document_embedder

        store = _get_document_store_for_kb(resolved)

        # 2️⃣ 创建文档（使用稳定 id 实现自动去重）
        doc_id = _stable_doc_id_from_content(text)
        doc = Document(
            id=doc_id,
            content=text,
            meta={"kb_id": display_id, "source": "api.knowledge_add_text", "content_hash_id": doc_id},
        )

        # 3️⃣ Haystack 2.x: 先生成 embedding，再写入
        embedder = get_document_embedder()
        result = embedder.run(documents=[doc])
        embedded_docs = result["documents"]
        
        store.write_documents(embedded_docs, policy=DuplicatePolicy.SKIP)
        
        # 手动保存FAISS索引到磁盘
        try:
            # 尝试不同的保存方法
            if hasattr(store, 'save'):
                store.save(store.index_path)
                print(f"[KB={resolved}] FAISS索引已保存到磁盘 (方法1)")
            elif hasattr(store, 'save_to_disk'):
                store.save_to_disk(store.index_path)
                print(f"[KB={resolved}] FAISS索引已保存到磁盘 (方法2)")
            else:
                print(f"[KB={resolved}] 警告：未找到保存方法，数据可能不会持久化")
        except Exception as save_error:
            print(f"[KB={resolved}] 保存FAISS索引失败: {save_error}")
            # 尝试手动保存索引文件
            try:
                import faiss
                if hasattr(store, 'index') and hasattr(store, 'index_path'):
                    faiss.write_index(store.index, f"{store.index_path}.faiss")
                    print(f"[KB={resolved}] 使用faiss.write_index保存成功")
            except Exception as manual_save_error:
                print(f"[KB={resolved}] 手动保存也失败: {manual_save_error}")

        return {"kb_id": display_id, "status": "ok", "doc_id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        err_msg = f"{type(e).__name__}: {e}"
        tb = traceback.format_exc()
        print(f"[knowledge/add_text] {err_msg}\n{tb}")
        raise HTTPException(status_code=500, detail=f"写入知识库失败: {err_msg}")


@app.get("/knowledge/docs", response_model=List[DocPreview])
def knowledge_list_docs(kb_id: str, limit: int = 20, offset: int = 0):
    """
    查看指定知识库中的文档列表（仅预览）：
      - kb_id: 知识库 ID
      - limit/offset: 分页参数
    返回每条文档的 id / 内容前 200 字 / meta。
    """
    try:
        store, _ = _get_sql_store_for_kb(kb_id)
        # Haystack 2.x: 使用 filter_documents() 获取所有文档
        all_docs = store.filter_documents()
        slice_docs = all_docs[offset : offset + limit]

        def _preview(text: Any, max_len: int = 200) -> str:
            if text is None:
                return ""
            s = str(text)
            return s if len(s) <= max_len else s[:max_len]

        return [
            DocPreview(
                id=str(d.id if hasattr(d, "id") else ""),
                content_preview=_preview(d.content if hasattr(d, "content") else ""),
                meta=d.meta if hasattr(d, "meta") else None,
            )
            for d in slice_docs
        ]
    except HTTPException as e:
        # 若该知识库尚未创建 docs.db（例如刚创建还未导入任何文档），视为“空列表”而不是错误，
        # 这样前端不会提示“加载文档列表失败”，而是正常显示 0 条记录。
        if getattr(e, "status_code", None) == 404:
            return []
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取知识库文档失败: {e}")


@app.get("/knowledge/docs/count")
def knowledge_docs_count(kb_id: str):
    """返回指定知识库的文档总数，供前端分页。"""
    try:
        store, resolved = _get_sql_store_for_kb(kb_id)
    except HTTPException as e:
        # 尚未创建 docs.db 时返回 0，而不是 404，让前端能够正常展示“空知识库”。
        if getattr(e, "status_code", None) == 404:
            return {"kb_id": kb_id, "resolved": None, "count": 0}
        raise

    try:
        if hasattr(store, "count_documents"):
            n = store.count_documents()
        elif hasattr(store, "get_document_count"):
            n = store.get_document_count()
        else:
            raise RuntimeError("DocumentStore 不支持 count_documents/get_document_count")
        # 对外 kb_id 保持为调用方传入的展示名，resolved 用于调试查看内部存储目录
        return {"kb_id": kb_id, "resolved": resolved, "count": int(n)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_sql_store_for_kb(kb_id: str):
    """仅用于查阅/修改：返回该知识库的 FAISSDocumentStore（Haystack 2.x）。"""
    resolved = _resolve_kb_id(kb_id)
    from rag.kb_manager import _get_document_store_for_kb
    try:
        store = _get_document_store_for_kb(resolved)
        return store, resolved
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"该知识库尚未创建文档数据库: {e}")


@app.get("/knowledge/docs/detail", response_model=DocDetail)
def knowledge_doc_detail(kb_id: str, doc_id: str):
    """获取单条文档全文，供查阅与编辑。"""
    store, resolved = _get_sql_store_for_kb(kb_id)
    # Haystack 2.x: 使用 filter_documents 查找文档
    docs = store.filter_documents(filters={"field": "id", "operator": "==", "value": doc_id})
    if not docs:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc = docs[0]
    content = doc.content if hasattr(doc, "content") else None
    if content is not None and not isinstance(content, str):
        content = str(content)
    return DocDetail(
        id=str(doc.id if hasattr(doc, "id") else ""),
        content=content or "",
        meta=doc.meta if hasattr(doc, "meta") else None,
    )


@app.put("/knowledge/docs/update")
def knowledge_doc_update(req: DocUpdateRequest):
    """修改知识库内一条文档的内容：先删后增，再重建向量索引。"""
    import uuid
    from haystack import Document
    from rag.kb_manager import _get_document_store_for_kb
    from storage.retriever import get_document_embedder

    display_id = (req.kb_id or "").strip()
    resolved = _resolve_kb_id(req.kb_id)
    text = (req.content or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="content 不能为空")
    try:
        store = _get_document_store_for_kb(resolved)
        store.delete_documents([req.doc_id])
        doc = Document(
            id=str(uuid.uuid4()),
            content=text,
            meta={"kb_id": display_id, "source": "api.knowledge_doc_update", "replaced_id": req.doc_id},
        )
        
        # Haystack 2.x: 先生成 embedding，再写入
        embedder = get_document_embedder()
        result = embedder.run(documents=[doc])
        embedded_docs = result["documents"]
        
        store.write_documents(embedded_docs)
        
        # 手动保存FAISS索引到磁盘
        try:
            store.save(store.index_path)
            print(f"[KB={resolved}] 文档更新后FAISS索引已保存到磁盘")
        except Exception as save_error:
            print(f"[KB={resolved}] 保存FAISS索引失败: {save_error}")
            # 降级尝试手动写索引文件
            try:
                import faiss  # type: ignore
                if hasattr(store, "index") and hasattr(store, "index_path"):
                    faiss.write_index(store.index, f"{store.index_path}.faiss")
                    print(f"[KB={resolved}] 使用 faiss.write_index 手动保存成功 (knowledge_doc_update)")
            except Exception as manual_err:
                print(f"[KB={resolved}] 手动保存索引失败 (knowledge_doc_update): {manual_err}")
        
        return {"kb_id": display_id, "doc_id": req.doc_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档失败: {e}")


@app.delete("/knowledge/docs/delete")
def knowledge_doc_delete(kb_id: str, doc_id: str):
    """删除知识库内一条文档。"""
    from rag.kb_manager import _get_document_store_for_kb

    display_id = (kb_id or "").strip()
    resolved = _resolve_kb_id(kb_id)
    try:
        store = _get_document_store_for_kb(resolved)
        store.delete_documents([doc_id])
        
        # 手动保存FAISS索引到磁盘
        try:
            store.save(store.index_path)
            print(f"[KB={resolved}] 文档删除后FAISS索引已保存到磁盘")
        except Exception as save_error:
            print(f"[KB={resolved}] 保存FAISS索引失败: {save_error}")
            try:
                import faiss  # type: ignore
                if hasattr(store, "index") and hasattr(store, "index_path"):
                    faiss.write_index(store.index, f"{store.index_path}.faiss")
                    print(f"[KB={resolved}] 使用 faiss.write_index 手动保存成功 (knowledge_doc_delete)")
            except Exception as manual_err:
                print(f"[KB={resolved}] 手动保存索引失败 (knowledge_doc_delete): {manual_err}")
        
        return {"kb_id": display_id, "doc_id": doc_id, "status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {e}")


@app.post("/knowledge/upload_file")
async def knowledge_upload_file(
    kb_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    上传文件导入知识库：
      - 支持文本类文件（.txt/.md/.json）
      - JSON 支持：
          1) 列表，每个元素有 content/text 字段
          2) 单个对象，含 content/text
    """
    resolved = _resolve_kb_id(kb_id)
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    try:
        raw = await file.read()
        texts: List[str] = []
        metas: List[dict] = []

        def _extract_from_item(item: Any) -> Optional[str]:
            if isinstance(item, dict):
                for key in ("content", "text", "body"):
                    if key in item and isinstance(item[key], str):
                        return item[key]
            return None

        def _build_qa_content(obj: dict) -> Optional[str]:
            """
            针对常见题库 JSONL：{question, options, answer, ...}
            以及标准格式：{title, content, ...}
            组装成可检索文本。
            """
            # 优先处理问答格式
            q = obj.get("question")
            a = obj.get("answer")
            opts = obj.get("options")
            if isinstance(q, str) and q.strip():
                parts = [f"问题：{q.strip()}"]
                if isinstance(opts, dict) and opts:
                    # options: {"A":"...","B":"..."}
                    opt_lines = []
                    for k, v in opts.items():
                        if isinstance(k, str) and isinstance(v, str):
                            opt_lines.append(f"{k}. {v}")
                    if opt_lines:
                        parts.append("选项：\n" + "\n".join(opt_lines))
                if isinstance(a, str) and a.strip():
                    parts.append(f"答案：{a.strip()}")
                return "\n".join(parts)
            
            # 处理标准格式：{title, content}
            title = obj.get("title")
            content = obj.get("content")
            if isinstance(title, str) and title.strip() and isinstance(content, str) and content.strip():
                return f"标题：{title.strip()}\n内容：{content.strip()}"
            
            # fallback: 尝试 content/text/body
            return _extract_from_item(obj)

        if ext == ".json":
            try:
                obj = json.loads(raw.decode("utf-8", errors="ignore"))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")

            if isinstance(obj, list):
                for it in obj:
                    t = _extract_from_item(it)
                    if t:
                        texts.append(t)
                        metas.append({"filename": filename})
            elif isinstance(obj, dict):
                t = _extract_from_item(obj)
                if t:
                    texts.append(t)
                    metas.append({"filename": filename})
            else:
                raise HTTPException(status_code=400, detail="不支持的 JSON 结构")

        elif ext == ".jsonl":
            text_all = raw.decode("utf-8", errors="ignore")
            for line_no, line in enumerate(text_all.splitlines(), start=1):
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                except Exception:
                    # 非法 JSON 行直接跳过
                    continue
                if not isinstance(obj, dict):
                    continue
                t = _build_qa_content(obj)
                if not t:
                    continue
                meta_extra = {"filename": filename, "line_no": line_no}
                # 常见字段保留到 meta，便于后续过滤/展示
                for k in ("meta_info", "answer_idx", "source", "category"):
                    v = obj.get(k)
                    if v is not None:
                        meta_extra[k] = v
                texts.append(t)
                metas.append(meta_extra)

        else:
            # 其他文本文件按 utf-8 解码，按空行粗略分段
            text_all = raw.decode("utf-8", errors="ignore")
            chunks = [p.strip() for p in text_all.split("\n\n") if p.strip()]
            chunks = chunks or [text_all]
            texts.extend(chunks)
            metas.extend([{"filename": filename}] * len(chunks))

        if not texts:
            raise HTTPException(status_code=400, detail="未解析到可导入的文本内容")

        from haystack import Document
        from rag.kb_manager import _get_document_store_for_kb
        from storage.retriever import get_document_embedder

        store = _get_document_store_for_kb(resolved)

        # 创建 Document 对象列表
        docs = []
        seen = set()
        for i, t in enumerate(texts):
            # 用内容生成稳定 id：重复内容（跨次导入）会自动跳过
            doc_id = _stable_doc_id_from_content(t)
            if doc_id in seen:
                continue
            seen.add(doc_id)
            
            meta = {
                "kb_id": resolved,
                "source": "api.knowledge_upload_file",
                "content_hash_id": doc_id,
                "index": i,
            }
            if i < len(metas) and isinstance(metas[i], dict):
                meta.update(metas[i])
            else:
                meta["filename"] = filename
            
            doc = Document(id=doc_id, content=(t or "").strip(), meta=meta)
            docs.append(doc)

        t0 = time.time()
        print(f"[IMPORT][{resolved}] 开始生成 embedding，文档数={len(docs)}")
        
        # Haystack 2.x: 先生成 embedding
        embedder = get_document_embedder()
        result = embedder.run(documents=docs)
        embedded_docs = result["documents"]
        
        print(f"[IMPORT][{resolved}] Embedding 生成完成，用时={time.time() - t0:.2f}s")

        t1 = time.time()
        print(f"[IMPORT][{resolved}] 开始写入文档")
        store.write_documents(embedded_docs, policy=DuplicatePolicy.SKIP)
        print(f"[IMPORT][{resolved}] 文档写入完成，条数={len(embedded_docs)}，用时={time.time() - t1:.2f}s")

        # 手动保存FAISS索引到磁盘
        try:
            store.save(store.index_path)
            print(f"[IMPORT][{resolved}] FAISS索引已保存到磁盘")
        except Exception as save_error:
            print(f"[IMPORT][{resolved}] 保存FAISS索引失败: {save_error}")
            try:
                import faiss  # type: ignore
                if hasattr(store, "index") and hasattr(store, "index_path"):
                    faiss.write_index(store.index, f"{store.index_path}.faiss")
                    print(f"[IMPORT][{resolved}] 使用 faiss.write_index 手动保存成功 (knowledge_upload_file)")
            except Exception as manual_err:
                print(f"[IMPORT][{resolved}] 手动保存索引失败 (knowledge_upload_file): {manual_err}")

        total = time.time() - t0

        return {
            "kb_id": kb_id,
            "file": filename,
            "submitted_docs": len(texts),
            "unique_in_file": len(docs),
            "timing": {
                "embed_seconds": round(t1 - t0, 3),
                "write_seconds": round(time.time() - t1, 3),
                "total_seconds": round(total, 3),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件导入失败: {e}")


def _run_import_task(task_id: str, kb_id: str, resolved: str, filename: str, texts: List[str], metas: List[dict]) -> None:
    """后台线程：执行导入+向量+索引，并更新任务进度。"""
    from rag.kb_manager import _get_document_store_for_kb
    from storage.retriever import get_retriever as make_retriever

    def _update(**kwargs):
        with _IMPORT_LOCK:
            task = _IMPORT_TASKS.get(task_id)
            if not task:
                return
            task.update(kwargs)

    try:
        _update(status="running", stage="prepare_docs", progress=5)

        from haystack import Document
        from storage.retriever import get_document_embedder
        
        store = _get_document_store_for_kb(resolved)
        
        # 创建 Document 对象列表
        docs = []
        seen = set()
        for i, t in enumerate(texts):
            doc_id = _stable_doc_id_from_content(t)
            if doc_id in seen:
                continue
            seen.add(doc_id)
            
            meta = {
                "kb_id": resolved,
                "source": "api.knowledge_upload_file_async",
                "content_hash_id": doc_id,
                "index": i,
            }
            if i < len(metas) and isinstance(metas[i], dict):
                meta.update(metas[i])
            else:
                meta["filename"] = filename
            
            doc = Document(id=doc_id, content=(t or "").strip(), meta=meta)
            docs.append(doc)

        _update(stage="generate_embeddings", progress=20, total_docs=len(docs))
        t0 = time.time()
        
        # Haystack 2.x: 先生成 embedding
        embedder = get_document_embedder()
        result = embedder.run(documents=docs)
        embedded_docs = result["documents"]
        
        embed_seconds = time.time() - t0
        print(f"[IMPORT-ASYNC][{resolved}][{task_id}] Embedding 生成完成，条数={len(embedded_docs)}，用时={embed_seconds:.2f}s")

        _update(stage="write_documents", progress=60)
        t1 = time.time()
        store.write_documents(embedded_docs, policy=DuplicatePolicy.SKIP)
        write_seconds = time.time() - t1
        print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 文档写入完成，条数={len(embedded_docs)}，用时={write_seconds:.2f}s")

        # 手动保存FAISS索引到磁盘
        try:
            store.save(store.index_path)
            print(f"[IMPORT-ASYNC][{resolved}][{task_id}] FAISS索引已保存到磁盘")
        except Exception as save_error:
            print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 保存FAISS索引失败: {save_error}")
            try:
                import faiss  # type: ignore
                if hasattr(store, "index") and hasattr(store, "index_path"):
                    faiss.write_index(store.index, f"{store.index_path}.faiss")
                    print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 使用 faiss.write_index 手动保存成功")
            except Exception as manual_err:
                print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 手动保存索引失败: {manual_err}")

        # 导入完成后执行一次全库去重（内容相同的文档仅保留一份）
        _update(stage="deduplication", progress=90)
        try:
            dedupe_req = KbDeleteRequest(kb_id=kb_id)
            dedupe_result = knowledge_dedupe(dedupe_req)
            removed = int(dedupe_result.get("removed_duplicates", 0))
            if removed:
                print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 去重完成，移除重复文档 {removed} 条")
        except Exception as dedupe_err:
            print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 去重阶段出错（忽略，不影响本次导入结果）: {dedupe_err}")

        _update(
            status="done",
            stage="finished",
            progress=100,
            result={
                "kb_id": kb_id,
                "file": filename,
                "submitted_docs": len(texts),
                "unique_in_file": len(docs),
                "timing": {
                    "embed_seconds": round(embed_seconds, 3),
                    "write_seconds": round(write_seconds, 3),
                },
            },
        )
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        print(f"[IMPORT-ASYNC][{resolved}][{task_id}] 任务失败: {e}\n{tb}")
        _update(status="error", stage="error", error=str(e), progress=100)


@app.post("/knowledge/upload_file_async")
async def knowledge_upload_file_async(
    kb_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    异步导入知识库：
      - 立即返回 task_id
      - 后台线程执行导入 + 向量 + 索引
      - 前端通过 /knowledge/upload_status 轮询进度
    """
    resolved = _resolve_kb_id(kb_id)
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    raw = await file.read()
    texts: List[str] = []
    metas: List[dict] = []

    def _extract_from_item(item: Any) -> Optional[str]:
        if isinstance(item, dict):
            for key in ("content", "text", "body"):
                if key in item and isinstance(item[key], str):
                    return item[key]
        return None

    def _build_qa_content(obj: dict) -> Optional[str]:
        # 优先处理问答格式
        q = obj.get("question")
        a = obj.get("answer")
        opts = obj.get("options")
        if isinstance(q, str) and q.strip():
            parts = [f"问题：{q.strip()}"]
            if isinstance(opts, dict) and opts:
                opt_lines = []
                for k, v in opts.items():
                    if isinstance(k, str) and isinstance(v, str):
                        opt_lines.append(f"{k}. {v}")
                if opt_lines:
                    parts.append("选项：\n" + "\n".join(opt_lines))
            if isinstance(a, str) and a.strip():
                parts.append(f"答案：{a.strip()}")
            return "\n".join(parts)
        
        # 处理标准格式：{title, content}
        title = obj.get("title")
        content = obj.get("content")
        if isinstance(title, str) and title.strip() and isinstance(content, str) and content.strip():
            return f"标题：{title.strip()}\n内容：{content.strip()}"
        
        # fallback: 尝试 content/text/body
        return _extract_from_item(obj)

    try:
        if ext == ".json":
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            if isinstance(obj, list):
                for it in obj:
                    t = _extract_from_item(it)
                    if t:
                        texts.append(t)
                        metas.append({"filename": filename})
            elif isinstance(obj, dict):
                t = _extract_from_item(obj)
                if t:
                    texts.append(t)
                    metas.append({"filename": filename})
            else:
                raise HTTPException(status_code=400, detail="不支持的 JSON 结构")
        elif ext == ".jsonl":
            text_all = raw.decode("utf-8", errors="ignore")
            for line_no, line in enumerate(text_all.splitlines(), start=1):
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue
                t = _build_qa_content(obj)
                if not t:
                    continue
                meta_extra = {"filename": filename, "line_no": line_no}
                for k in ("meta_info", "answer_idx", "source", "category"):
                    v = obj.get(k)
                    if v is not None:
                        meta_extra[k] = v
                texts.append(t)
                metas.append(meta_extra)
        else:
            text_all = raw.decode("utf-8", errors="ignore")
            chunks = [p.strip() for p in text_all.split("\n\n") if p.strip()] or [text_all]
            texts.extend(chunks)
            metas.extend([{"filename": filename}] * len(chunks))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {e}")

    if not texts:
        raise HTTPException(status_code=400, detail="未解析到可导入的文本内容")

    task_id = str(uuid.uuid4())
    with _IMPORT_LOCK:
        _IMPORT_TASKS[task_id] = {
            "status": "pending",
            "stage": "queued",
            "progress": 0,
            "kb_id": kb_id,
            "resolved": resolved,
            "file": filename,
        }

    t = threading.Thread(
        target=_run_import_task,
        args=(task_id, kb_id, resolved, filename, texts, metas),
        daemon=True,
    )
    t.start()

    return {"task_id": task_id, "status": "queued"}


@app.get("/knowledge/upload_status")
def knowledge_upload_status(task_id: str):
    """查询异步导入任务进度。"""
    with _IMPORT_LOCK:
        task = _IMPORT_TASKS.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        # 返回一个浅拷贝，避免外部修改
        return dict(task)

@app.post("/knowledge/dedupe")
def knowledge_dedupe(req: KbDeleteRequest):
    """
    对指定知识库做一次性去重清洗（按归一化 content 去重）：
    - 删除重复文档
    - 重建向量并保存索引
    """
    from rag.kb_manager import _get_document_store_for_kb
    from storage.retriever import get_retriever as make_retriever

    kb_id = (req.kb_id or "").strip()
    if not kb_id:
        raise HTTPException(status_code=400, detail="kb_id 不能为空")

    resolved = _resolve_kb_id(kb_id)
    try:
        store = _get_document_store_for_kb(resolved)
        # Haystack 2.x: 使用 filter_documents() 替代 get_all_documents()
        docs = store.filter_documents()
        seen = {}
        dup_ids = []
        for d in docs:
            did = str(getattr(d, "id", "") or "")
            norm = _normalize_for_dedupe(getattr(d, "content", ""))
            if not norm:
                continue
            key = _stable_doc_id_from_content(norm)
            if key in seen:
                dup_ids.append(did)
            else:
                seen[key] = did

        if dup_ids:
            store.delete_documents(dup_ids)
            
            # 手动保存FAISS索引到磁盘
            try:
                store.save(store.index_path)
                print(f"[KB={resolved}] 去重后FAISS索引已保存到磁盘")
            except Exception as save_error:
                print(f"[KB={resolved}] 保存FAISS索引失败: {save_error}")
                try:
                    import faiss  # type: ignore
                    if hasattr(store, "index") and hasattr(store, "index_path"):
                        faiss.write_index(store.index, f"{store.index_path}.faiss")
                        print(f"[KB={resolved}] 使用 faiss.write_index 手动保存成功 (knowledge_dedupe)")
                except Exception as manual_err:
                    print(f"[KB={resolved}] 手动保存索引失败 (knowledge_dedupe): {manual_err}")

        return {"kb_id": kb_id, "resolved": resolved, "removed_duplicates": len(dup_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"去重失败: {e}")


@app.post("/rag/ask", response_model=RagAskResponse)
def post_rag_ask(req: RagAskRequest):
    """一次性返回答案与引用，供非流式场景"""
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    use_kb = True if req.use_kb is None else bool(req.use_kb)
    kb_id = _resolve_kb_id(req.kb_id) if use_kb else None
    retriever = kb_manager.get_retriever(kb_id) if use_kb else None
    try:
        use_cot = req.use_cot if req.use_cot is not None else USE_COT
        answer, refs, reasoning_chain, timing = qa_ask(
            question,
            retriever,
            return_reasoning=True,
            stream_callback=None,
            on_complete=None,
            llm_backend=req.llm_backend,
            kb_id=kb_id,
            use_kb=use_kb,
        )
        reasoning_text = None
        reasoning_json_str = None
        if reasoning_chain is not None:
            if isinstance(reasoning_chain, dict):
                reasoning_json_str = json.dumps(reasoning_chain, ensure_ascii=False)
                reasoning_text = "【问题理解】{}\n【信息提取】{}\n【逻辑推理】{}\n【最终答案】{}".format(
                    reasoning_chain.get("problem_understanding", ""),
                    reasoning_chain.get("information_extraction", ""),
                    reasoning_chain.get("logical_reasoning", ""),
                    reasoning_chain.get("final_answer", answer),
                )
            else:
                reasoning_text = reasoning_chain.format_reasoning()
        return RagAskResponse(
            answer=answer,
            refs=_refs_to_list(refs),
            reasoning=reasoning_text,
            reasoning_json=reasoning_json_str,
            timing=timing,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _stream_rag(
    question: str,
    kb_id: Optional[str],
    llm_backend: Optional[str],
    use_cot: bool,
    use_kb: bool,
    use_smart_router: bool = False,
    progress_session_id: Optional[str] = None,
):
    """流式执行 RAG：专注于内容流式输出，进度通过独立API管理"""
    timing_holder = [None]
    chunks_collected = []

    # kb_id 可能为 None（前端选择"不使用知识库" 或 未显式传入）。
    # 与 /rag/ask 保持一致：当 use_kb=True 且 kb_id 为空/默认值时，fallback 到 CURRENT_KB。
    resolved_kb: Optional[str]
    if use_kb:
        # _resolve_kb_id 会处理 None / "default" / "haystack" 等，统一映射到 CURRENT_KB
        resolved_kb = _resolve_kb_id(kb_id)
    else:
        resolved_kb = None

    try:
        print(f"[RAG] kb_id={resolved_kb or 'none'}, use_smart_router={use_smart_router}, progress_session={progress_session_id}")

        # 创建进度回调函数（如果提供了会话ID）
        progress_callback = None
        if progress_session_id:
            progress_callback = create_progress_callback(progress_session_id)

        # 直接在回调中累积 chunk，便于 SSE 按顺序输出
        def collect(chunk: str):
            chunks_collected.append(chunk)

        # 包装 on_complete 回调，确保进度完成
        def wrapped_on_complete(timing):
            timing_holder[0] = timing
            # 确保进度完成
            if progress_session_id:
                complete_progress(progress_session_id)

        answer, refs, reasoning_chain, timing = qa_ask(
            question,
            kb_manager.get_retriever(resolved_kb) if (use_kb and resolved_kb) else None,
            use_cot=use_cot if use_cot is not None else USE_COT,
            return_reasoning=True,
            stream_callback=collect,
            on_complete=wrapped_on_complete,
            llm_backend=llm_backend,
            kb_id=resolved_kb,
            use_kb=use_kb,
            use_smart_router=use_smart_router,
            progress_callback=progress_callback,
        )
        timing_holder[0] = timing or timing_holder[0]

        # 额外确保进度完成（防止 on_complete 未被调用）
        if progress_session_id:
            complete_progress(progress_session_id)

    except Exception as e:
        # 如果有进度会话，标记为完成（错误状态）
        if progress_session_id:
            update_progress(progress_session_id, "错误", f"处理失败: {str(e)}")

        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        return

    # 若后端 LLM 未走流式（如某些 zhipu 调用），collect 不会收到 chunk，此时回退为一次性推送完整 answer
    if not chunks_collected and answer:
        chunks_collected.append(answer)

    for chunk in chunks_collected:
        yield f"data: {json.dumps({'message': {'content': chunk}, 'done': False}, ensure_ascii=False)}\n\n"

    refs_serial = [{"content": r.get("content", ""), "meta": r.get("meta"), "score": r.get("score")} for r in (refs or [])]

    # 构建最终payload，包含所有检索到的文档（用于调试模式）
    final_payload = {
        "message": {"content": ""},
        "done": True,
        "done_reason": "stop",
        "refs": refs_serial,
        "timing": timing_holder[0],
    }

    # 添加所有检索到的文档（用于调试模式显示）
    if timing_holder[0] and timing_holder[0].get("all_docs"):
        final_payload["allRefs"] = timing_holder[0]["all_docs"]
    if isinstance(reasoning_chain, dict):
        final_payload["reasoning"] = reasoning_chain
    yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"


@app.post("/rag/ask/stream")
def rag_ask_stream(req: RagAskRequest):
    """流式返回答案（SSE），与 Java OllamaChatService 转发格式一致；支持 kb_id 动态选择知识库。"""
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    use_cot = req.use_cot if req.use_cot is not None else USE_COT
    use_kb = True if req.use_kb is None else bool(req.use_kb)
    use_smart_router = req.use_smart_router if req.use_smart_router is not None else False
    return StreamingResponse(
        _stream_rag(question, req.kb_id, req.llm_backend, use_cot, use_kb, use_smart_router, req.progress_session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/test/smart-router")
def test_smart_router(data: dict):
    """测试智能路由功能"""
    question = data.get("question", "")
    llm_backend = data.get("llm_backend")
    
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    
    try:
        result = safe_smart_route(question, llm_backend)
        return {
            "success": True,
            "result": result,
            "message": "智能路由测试成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "智能路由测试失败"
        }


@app.get("/config/smart-router")
def get_smart_router_config():
    """获取智能路由配置"""
    return {
        "timeout": SMART_ROUTER_TIMEOUT,
        "use_fallback": USE_SIMPLE_ROUTER_FALLBACK
    }


@app.post("/config/smart-router")
def set_smart_router_config(config: dict):
    """设置智能路由配置"""
    global SMART_ROUTER_TIMEOUT, USE_SIMPLE_ROUTER_FALLBACK
    
    if "timeout" in config:
        SMART_ROUTER_TIMEOUT = max(5, min(120, int(config["timeout"])))
    
    if "use_fallback" in config:
        USE_SIMPLE_ROUTER_FALLBACK = bool(config["use_fallback"])
    
    return {
        "success": True,
        "config": {
            "timeout": SMART_ROUTER_TIMEOUT,
            "use_fallback": USE_SIMPLE_ROUTER_FALLBACK
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
