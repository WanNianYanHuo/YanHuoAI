#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库管理测试：测试知识库的创建、删除、文档管理等功能
"""
import os
import sys
import unittest
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKnowledgeBaseManager(unittest.TestCase):
    """知识库管理测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_kb_manager"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_create_knowledge_base(self):
        """测试创建知识库"""
        from rag.kb_manager import kb_manager
        
        storage_key = kb_manager.create_knowledge_base(self.test_kb_id)
        self.assertIsNotNone(storage_key)

    def test_document_operations(self):
        """测试文档的增删改查操作"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 添加文档
        result = kb_manager.add_text(self.test_kb_id, "这是一个测试文档内容")
        self.assertIn("doc_count", result)
        self.assertGreater(result["doc_count"], 0)
        
        # 检查文档数量
        count = kb_manager.count_documents(self.test_kb_id)
        self.assertGreater(count, 0)
        
        # 列出文档
        docs = kb_manager.list_documents(self.test_kb_id, limit=10)
        self.assertGreater(len(docs), 0)
        
        # 获取文档 ID
        doc_id = docs[0]["id"]
        
        # 获取单个文档
        doc = kb_manager.get_document(self.test_kb_id, doc_id)
        self.assertIsNotNone(doc)
        
        # 更新文档
        updated_doc = {
            "content": "更新后的文档内容",
            "meta": {"updated": True}
        }
        kb_manager.update_document(self.test_kb_id, doc_id, updated_doc)
        
        # 验证更新
        updated = kb_manager.get_document(self.test_kb_id, doc_id)
        self.assertEqual(updated.content, "更新后的文档内容")
        
        # 删除文档
        result = kb_manager.delete_document(self.test_kb_id, doc_id)
        self.assertTrue(result)
        
        # 验证删除
        final_count = kb_manager.count_documents(self.test_kb_id)
        self.assertEqual(final_count, count - 1)

    def test_search_functionality(self):
        """测试搜索功能"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库并添加测试文档
        kb_manager.create_knowledge_base(self.test_kb_id)
        kb_manager.add_text(self.test_kb_id, "糖尿病是一种慢性疾病")
        kb_manager.add_text(self.test_kb_id, "高血压需要长期管理")
        kb_manager.add_text(self.test_kb_id, "健康饮食很重要")
        
        # 搜索测试
        results = kb_manager.search(self.test_kb_id, "糖尿病", top_k=5)
        self.assertGreater(len(results), 0)
        
        # 验证搜索结果包含相关内容
        found_diabetes = any("糖尿病" in result["content"] for result in results)
        self.assertTrue(found_diabetes)

    def test_knowledge_base_mapping(self):
        """测试知识库名称映射功能"""
        from rag.kb_manager import get_storage_key, get_display_id, list_storage_keys
        
        # 测试中文名称映射
        chinese_name = "中医测试库"
        storage_key = get_storage_key(chinese_name)
        self.assertTrue(storage_key.startswith("kb_"))
        
        # 测试反向映射
        display_id = get_display_id(storage_key)
        self.assertEqual(display_id, chinese_name)
        
        # 测试列出存储键
        storage_keys = list_storage_keys()
        self.assertIsInstance(storage_keys, list)


if __name__ == "__main__":
    unittest.main()