#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 核心演示 - Haystack 2.x 版本
简化版，仅用于演示
"""

import os
import glob
import pandas as pd
import requests

# Haystack 2.x 导入
try:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore
except ImportError:
    raise ImportError("需要安装 faiss-haystack 包: pip install faiss-haystack")

from haystack import Document
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.utils.device import ComponentDevice

# =======================
# 配置
# =======================
FAISS_FILE = "haystack_faiss.faiss"
EMBEDDING_MODEL = "BAAI/bge-small-zh"
EMBEDDING_DIM = 512
DOC_FOLDER = "./docs"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
TOP_K = 10
PREVIEW_CHARS = 200

# =======================
# 1️⃣ 初始化 DocumentStore
# =======================
def init_document_store():
    base_path = FAISS_FILE.rsplit('.', 1)[0] if '.' in FAISS_FILE else FAISS_FILE
    index_path = base_path
    
    if os.path.exists(f"{index_path}.faiss"):
        try:
            store = FAISSDocumentStore(
                index_path=index_path,
                embedding_dim=EMBEDDING_DIM
            )
            print("✅ 已加载已有 FAISS 索引")
            return store
        except Exception as e:
            print(f"加载索引失败: {e}")
    
    print("初始化新的 FAISS 索引")
    store = FAISSDocumentStore(
        index_path=index_path,
        index_string="Flat",
        embedding_dim=EMBEDDING_DIM
    )
    return store

# =======================
# 2️⃣ 初始化嵌入器
# =======================
def init_embedders():
    text_embedder = SentenceTransformersTextEmbedder(
        model=EMBEDDING_MODEL,
        device=ComponentDevice.from_str("cpu")
    )
    text_embedder.warm_up()
    
    doc_embedder = SentenceTransformersDocumentEmbedder(
        model=EMBEDDING_MODEL,
        device=ComponentDevice.from_str("cpu")
    )
    doc_embedder.warm_up()
    
    return text_embedder, doc_embedder

# =======================
# 3️⃣ 导入文档
# =======================
def import_documents(folder: str, document_store, doc_embedder):
    files = glob.glob(os.path.join(folder, "*"))
    new_docs = []
    
    for file in files:
        try:
            if file.endswith(".csv"):
                df = pd.read_csv(file, encoding="utf-8", on_bad_lines='skip')
                for _, row in df.iterrows():
                    content = str(row.iloc[0]) + "\n" + str(row.iloc[1])
                    meta = {"source": os.path.basename(file)}
                    new_docs.append(Document(content=content, meta=meta))
                    
            elif file.endswith(".txt"):
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    meta = {"source": os.path.basename(file)}
                    new_docs.append(Document(content=content, meta=meta))
                    
        except Exception as e:
            print(f"读取 {file} 出错:", e)

    if new_docs:
        print(f"导入 {len(new_docs)} 个新文档")
        result = doc_embedder.run(documents=new_docs)
        embedded_docs = result["documents"]
        document_store.write_documents(embedded_docs)
        print(f"✅ 文档嵌入并写入成功")
    else:
        print("没有新文档需要导入")

# =======================
# 4️⃣ Ollama 调用
# =======================
def call_ollama(prompt: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        print(f"Ollama 调用失败: {e}")
        return "模型调用失败"

# =======================
# 5️⃣ RAG 查询
# =======================
def rag_ask(question: str, document_store, text_embedder, top_k: int = TOP_K, preview_chars: int = PREVIEW_CHARS) -> dict:
    query_result = text_embedder.run(text=question)
    query_embedding = query_result["embedding"]
    
    docs = document_store.search(
        query_embedding=query_embedding,
        top_k=top_k
    )

    if not docs:
        return {"answer": "无法找到相关资料", "references": []}

    context = "\n".join([f"[{i+1}] {d.content}" for i, d in enumerate(docs)])
    prompt = f"""你是一个中医问答助手。
请基于【给定资料】回答问题。

【给定资料】
{context}

【问题】
{question}

【回答】
"""
    answer = call_ollama(prompt)

    references = []
    for d in docs:
        preview = d.content[:preview_chars] + ("..." if len(d.content) > preview_chars else "")
        references.append({
            "content": preview, 
            "meta": d.meta, 
            "score": getattr(d, "score", 0)
        })

    return {"answer": answer, "references": references}

# =======================
# 6️⃣ 主流程
# =======================
if __name__ == "__main__":
    print("=" * 80)
    print("RAG 核心演示 - Haystack 2.x 版本")
    print("=" * 80)
    
    print("\n1. 初始化 Document Store...")
    document_store = init_document_store()
    
    print("2. 初始化嵌入器...")
    text_embedder, doc_embedder = init_embedders()
    
    if os.path.exists(DOC_FOLDER):
        print(f"3. 导入文档从 {DOC_FOLDER}...")
        import_documents(DOC_FOLDER, document_store, doc_embedder)
    else:
        print(f"3. 文档目录 {DOC_FOLDER} 不存在，跳过导入")
    
    print("\n4. 测试 RAG 问答...")
    question = "中医气虚证的主要表现有哪些？"
    result = rag_ask(question, document_store, text_embedder)
    
    print("\n问题:", question)
    print("\n回答:\n", result["answer"])
    
    if result["references"]:
        print(f"\n引用文档 ({len(result['references'])} 个):")
        for i, ref in enumerate(result["references"], 1):
            print(f"----- 文档 {i} -----")
            print("内容:", ref["content"])
            print("meta:", ref["meta"])
            print("score:", ref["score"])
    
    print("\n" + "=" * 80)
    print("演示完成!")
    print("=" * 80)