t.append({
                "id": doc.id,
                "content": doc.content,
                "meta": doc.meta,
                "score": doc.score if hasattr(doc, "score") else None,
            })
        return result

    def create_knowledge_base(self, kb_name: str) -> str:
        """创建知识库目录。"""
        storage_key = get_storage_key(kb_name)
        kb_dir = os.path.join(KB_ROOT, storage_key)
        os.makedirs(kb_dir, exist_ok=True)
        return storage_key

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库目录。"""
        import shutil
        
        resolved = _resolve_kb_id(kb_id)
        kb_dir = os.path.join(KB_ROOT, resolved)
        
        if os.path.exists(kb_dir):
            shutil.rmtree(kb_dir)
            return True
        
        return False


# 单例
kb_manager = KnowledgeBaseManager()
