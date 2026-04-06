import os
import pandas as pd
import hashlib
from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import EmbeddingRetriever

# =======================
# 导入csv_data下的文件夹
# =======================


# =======================
# 配置
# =======================
CSV_FOLDER = "./csv_data"            # CSV 文件夹
DB_FILE = "haystack_docs.db"         # SQLite 数据库文件
FAISS_FILE = "haystack_faiss.faiss" # FAISS 索引文件
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"  # 可换中文模型

# =======================
# 生成文档唯一 ID
# =======================
def generate_doc_id(source_file: str, row_index: int, content: str) -> str:
    hash_input = f"{source_file}_{row_index}_{content}".encode("utf-8")
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
        embedding_dim=768,
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
# 尝试多种编码读取 CSV
# =======================
def read_csv_file(path):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb2312", "latin1"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"成功读取 {os.path.basename(path)}，编码: {enc}")
            return df
        except Exception:
            continue
    print(f"读取 {os.path.basename(path)} 失败，跳过此文件")
    return None

# =======================
# 批量读取 CSV 并生成文档
# =======================
all_new_docs = []

for fname in os.listdir(CSV_FOLDER):
    if fname.endswith(".csv"):
        path = os.path.join(CSV_FOLDER, fname)
        df = read_csv_file(path)
        if df is None:
            continue

        for idx, row in df.iterrows():
            question = str(row.iloc[0]).strip()
            answer = str(row.iloc[1]).strip()
            content = f"问题/提纲: {question}\n详细解答: {answer}"
            doc_id = generate_doc_id(fname, idx, content)
            if doc_id not in existing_ids:
                all_new_docs.append({
                    "id": doc_id,
                    "content": content,
                    "meta": {"source_file": fname, "row_index": idx}
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
