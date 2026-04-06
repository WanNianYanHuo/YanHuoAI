# storage/document_store.py
# Haystack 2.x 版本

import os
try:
    from haystack_integrations.document_stores.faiss import FAISSDocumentStore
except ImportError:
    raise ImportError(
        "需要安装 faiss-haystack 包。请运行: pip install faiss-haystack"
    )

from config.settings import FAISS_FILE, EMBEDDING_DIM

def get_document_store():
    """
    获取或创建 FAISS 文档存储（Haystack 2.x 版本）
    """
    os.makedirs(os.path.dirname(FAISS_FILE), exist_ok=True)
    
    base_path = FAISS_FILE.rsplit('.', 1)[0] if '.' in FAISS_FILE else FAISS_FILE
    index_path = base_path
    
    # 尝试加载已有索引
    if os.path.exists(f"{index_path}.faiss"):
        try:
            store = FAISSDocumentStore(
                index_path=index_path,
                embedding_dim=EMBEDDING_DIM
            )
            print(f"已加载已有 FAISS 索引: {index_path}.faiss")
            return store
        except Exception as e:
            print(f"加载索引文件失败: {e}")
            print("将创建新的索引")
    
    # 创建新的 document store
    print("初始化新的 FAISS 索引")
    store = FAISSDocumentStore(
        index_path=index_path,
        index_string="Flat",
        embedding_dim=EMBEDDING_DIM
    )
    
    return store