#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入 TXT 文件到 FAISS 知识库 (Haystack 2.x 版本)
"""

import os
import hashlib
from pathlib import Path

try:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore
except ImportError:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore

from haystack import Document
from haystack.components.embedders.sentence_transformers_document_embedder import SentenceTransformersDocumentEmbedder
from haystack.components.embedders.sentence_transformers_text_embedder import SentenceTransformersTextEmbedder
from haystack.utils.device import ComponentDevice

# =======================
# 配置
# =======================
TXT_FOLDER = "./txt_data"  # TXT 文件目录
EMBEDDING_MODEL = "BAAI/bge-small-zh"  # 使用 BGE 中文模型
EMBEDDING_DIM = 512  # bge-small-zh 的向量维度
INDEX_PATH = "faiss_index"
INDEX_FILE = "faiss_index.faiss"

def generate_doc_id(source_file: str, content: str) -> str:
    """生成文档ID"""
    hash_input = f"{source_file}_{content[:1000]}".encode("utf-8")
    return hashlib.md5(hash_input).hexdigest()

def read_txt_file(filepath):
    """读取文本文件，尝试多种编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue
    
    # 如果所有编码都失败，使用二进制读取
    try:
        with open(filepath, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')
    except:
        return None

def main():
    print("=" * 60)
    print("TXT 文件导入工具 (Haystack 2.x 版本)")
    print("=" * 60)
    
    # 检查目录
    if not os.path.exists(TXT_FOLDER):
        print(f"错误: 目录不存在: {TXT_FOLDER}")
        return
    
    # 1. 初始化 Document Store
    print("1. 初始化 FAISS Document Store...")
    try:
        store = FAISSDocumentStore(
            index_path=INDEX_PATH,
            embedding_dim=EMBEDDING_DIM,
            index_string="Flat"
        )
        print(f"✅ Document Store 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 2. 初始化嵌入器
    print("2. 初始化嵌入器...")
    try:
        # 文档嵌入器
        doc_embedder = SentenceTransformersDocumentEmbedder(
            model=EMBEDDING_MODEL,
            device=ComponentDevice.from_str("cpu")
        )
        doc_embedder.warm_up()
        print("✅ 文档嵌入器初始化成功")
        
        # 文本嵌入器（用于查询，这里只用于演示）
        text_embedder = SentenceTransformersTextEmbedder(
            model=EMBEDDING_MODEL,
            device=ComponentDevice.from_str("cpu")
        )
        text_embedder.warm_up()
        print("✅ 文本嵌入器初始化成功")
    except Exception as e:
        print(f"❌ 嵌入器初始化失败: {e}")
        return
    
    # 3. 读取并处理 TXT 文件
    print(f"\n3. 扫描目录: {TXT_FOLDER}")
    txt_files = list(Path(TXT_FOLDER).glob("*.txt"))
    
    if not txt_files:
        print("❌ 没有找到 TXT 文件")
        return
    
    print(f"找到 {len(txt_files)} 个 TXT 文件")
    
    all_docs = []
    for txt_file in txt_files:
        try:
            content = read_txt_file(str(txt_file))
            if content:
                # 创建文档
                doc = Document(
                    content=content,
                    meta={
                        "source": txt_file.name,
                        "path": str(txt_file),
                        "type": "txt"
                    }
                )
                all_docs.append(doc)
                print(f"  ✓ 已加载: {txt_file.name} ({len(content)} 字符)")
            else:
                print(f"  ✗ 读取失败: {txt_file.name}")
        except Exception as e:
            print(f"  ✗ 处理失败 {txt_file.name}: {e}")
    
    if not all_docs:
        print("❌ 没有可处理的文档")
        return
    
    print(f"\n4. 处理 {len(all_docs)} 个文档...")
    
    # 4. 嵌入文档
    print("正在嵌入文档...")
    try:
        # 嵌入文档
        embedding_result = doc_embedder.run(documents=all_docs)
        embedded_docs = embedding_result["documents"]
        
        # 写入文档存储
        store.write_documents(embedded_docs)
        print(f"✅ 成功写入 {len(embedded_docs)} 个文档")
        
        # 保存索引
        store.save(INDEX_PATH)
        print(f"✅ 索引已保存到: {INDEX_PATH}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 导入完成!")
    print(f"   文档数量: {len(all_docs)}")
    print(f"   索引文件: {INDEX_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()