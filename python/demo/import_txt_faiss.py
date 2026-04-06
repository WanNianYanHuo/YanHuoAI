import os
import hashlib
from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import EmbeddingRetriever

# =======================
# 配置
# =======================
TXT_FOLDER = "./txt_data"             # TXT 文件夹
DB_FILE = "haystack_docs.db"          # SQLite 数据库文件
FAISS_FILE = "haystack_faiss.faiss"  # FAISS 索引文件
EMBEDDING_MODEL = "BAAI/bge-small-zh"  # BGE Small 中文模型
EMBEDDING_DIM = 512  # bge-small-zh 的向量维度

# =======================
# 生成文档唯一 ID
# =======================
def generate_doc_id(source_file: str, content: str) -> str:
    hash_input = f"{source_file}_{content}".encode("utf-8")
    return hashlib.md5(hash_input).hexdigest()

# =======================
# 初始化 DocumentStore
# =======================
if os.path.exists(FAISS_FILE):
    document_store = FAISSDocumentStore.load(FAISS_FILE)
    print("已加载已有 FAISS 索引")
else:
    document_store = FAISSDocumentStore(
        sql_url=f"sqlite:///{DB_FILE}",
        embedding_dim=EMBEDDING_DIM,
        faiss_index_factory_str="Flat"
    )
    print("创建新的 DocumentStore")

retriever = EmbeddingRetriever(
    document_store=document_store,
    embedding_model=EMBEDDING_MODEL
)

# =======================
# 获取已存在文档 ID
# =======================
existing_docs = document_store.get_all_documents()
existing_ids = set(d.id for d in existing_docs)
print(f"当前数据库已有文档数量: {len(existing_ids)}")

# =======================
# 读取 TXT 文件
# =======================
def read_txt_file(path):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb2312", "latin1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    print(f"无法读取文件: {path}")
    return None

all_new_docs = []

for fname in os.listdir(TXT_FOLDER):
    if fname.endswith(".txt"):
        txt_path = os.path.join(TXT_FOLDER, fname)

        # 读取 TXT 内容
        content = read_txt_file(txt_path)
        if content is None:
            continue

        doc_id = generate_doc_id(fname, content)

        if doc_id not in existing_ids:
            all_new_docs.append({
                "id": doc_id,
                "content": content,
                "meta": {"source_file": fname}
            })

print(f"去重后需要写入的文档数量: {len(all_new_docs)}")

# =======================
# 写入数据库并生成向量索引
# =======================
if all_new_docs:
    document_store.write_documents(all_new_docs)
    document_store.update_embeddings(retriever)
    document_store.save(FAISS_FILE)
    print("新文档已加入知识库并更新向量索引")
else:
    print("没有新文档需要写入")
