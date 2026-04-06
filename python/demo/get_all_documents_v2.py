#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取并显示知识库中的所有文档 (Haystack 2.x 版本)
"""

try:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore
except ImportError:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore

# =======================
# 配置
# =======================
INDEX_PATH = "faiss_index"  # 索引路径

def main():
    print("=" * 60)
    print("查看知识库文档 (Haystack 2.x 版本)")
    print("=" * 60)
    
    # 加载已有索引
    try:
        document_store = FAISSDocumentStore(
            index_path=INDEX_PATH,
            embedding_dim=512  # 需要与创建时一致
        )
        print(f"✅ 成功加载索引: {INDEX_PATH}")
    except Exception as e:
        print(f"❌ 加载索引失败: {e}")
        return
    
    # 获取所有文档 (Haystack 2.x: 不传 filters 参数)
    docs = document_store.filter_documents()
    
    print(f"\n数据库中共有 {len(docs)} 条文档")
    print("-" * 60)
    
    # 打印前几条
    for i, d in enumerate(docs[:5], 1):
        print(f"\n文档 {i}:")
        print(f"  ID: {d.id}")
        print(f"  内容: {d.content[:100]}..." if len(d.content) > 100 else f"  内容: {d.content}")
        print(f"  Meta: {d.meta}")
        print(f"  Score: {getattr(d, 'score', 'N/A')}")
    
    if len(docs) > 5:
        print(f"\n... 还有 {len(docs) - 5} 条文档")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()