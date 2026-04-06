#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入 CSV 文件到 FAISS 知识库 (Haystack 2.x 版本)
"""

import os
import pandas as pd
import hashlib
from pathlib import Path

try:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore
except ImportError:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore

from haystack import Document
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.utils.device import ComponentDevice

# =======================
# 配置
# =======================
CSV_FOLDER = "./csv_data"  # CSV 文件夹
EMBEDDING_MODEL = "BAAI/bge-small-zh"  # 使用 BGE 中文模型
EMBEDDING_DIM = 512  # bge-small-zh 的向量维度
INDEX_PATH = "faiss_index"

def generate_doc_id(source_file: str, row_index: int, content: str) -> str:
    """生成文档ID"""
    hash_input = f"{source_file}_{row_index}_{content[:500]}".encode("utf-8")
    return hashlib.md5(hash_input).hexdigest()

def read_csv_file(path):
    """读取 CSV 文件，尝试多种编码"""
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb2312", "latin1"]
    
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"  ✓ 成功读取 {os.path.basename(path)}，编码: {enc}")
            return df
        except Exception:
            continue
    
    print(f"  ✗ 读取 {os.path.basename(path)} 失败")
    return None

def main():
    print("=" * 60)
    print("CSV 文件导入工具 (Haystack 2.x 版本)")
    print("=" * 60)
    
    # 检查目录
    if not os.path.exists(CSV_FOLDER):
        print(f"错误: 目录不存在: {CSV_FOLDER}")
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
        doc_embedder = SentenceTransformersDocumentEmbedder(
            model=EMBEDDING_MODEL,
            device=ComponentDevice.from_str("cpu")
        )
        doc_embedder.warm_up()
        print("✅ 文档嵌入器初始化成功")
    except Exception as e:
        print(f"❌ 嵌入器初始化失败: {e}")
        return
    
    # 3. 扫描 CSV 文件
    print(f"\n3. 扫描目录: {CSV_FOLDER}")
    csv_files = list(Path(CSV_FOLDER).glob("*.csv"))
    
    if not csv_files:
        print("❌ 没有找到 CSV 文件")
        return
    
    print(f"找到 {len(csv_files)} 个 CSV 文件")
    
    all_docs = []
    total_rows = 0
    
    for csv_file in csv_files:
        print(f"\n处理: {csv_file.name}")
        df = read_csv_file(str(csv_file))
        
        if df is None:
            continue
        
        # 假设前两列是问答对
        for idx, row in df.iterrows():
            try:
                question = str(row.iloc[0]).strip() if len(row) > 0 else ""
                answer = str(row.iloc[1]).strip() if len(row) > 1 else ""
                
                if question or answer:
                    content = f"问题/提纲: {question}\n详细解答: {answer}"
                    doc = Document(
                        content=content,
                        meta={
                            "source": csv_file.name,
                            "row_index": idx,
                            "type": "csv"
                        }
                    )
                    all_docs.append(doc)
                    total_rows += 1
            except Exception as e:
                print(f"    处理第 {idx} 行失败: {e}")
    
    if not all_docs:
        print("❌ 没有可处理的文档")
        return
    
    print(f"\n4. 处理 {len(all_docs)} 个文档...")
    
    # 4. 嵌入并写入
    try:
        embedding_result = doc_embedder.run(documents=all_docs)
        embedded_docs = embedding_result["documents"]
        
        store.write_documents(embedded_docs)
        print(f"✅ 成功写入 {len(embedded_docs)} 个文档")
        
        store.save(INDEX_PATH)
        print(f"✅ 索引已保存到: {INDEX_PATH}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 导入完成!")
    print(f"   文件数量: {len(csv_files)}")
    print(f"   文档数量: {len(all_docs)}")
    print(f"   索引文件: {INDEX_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()