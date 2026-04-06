from haystack.document_stores import FAISSDocumentStore

# 加载已有索引
document_store = FAISSDocumentStore.load("haystack_faiss.faiss")

# 获取所有文档
docs = document_store.get_all_documents()
print(f"数据库中共有 {len(docs)} 条文档")

# 打印前几条
for d in docs[:5]:
    print(d.content, d.meta)
