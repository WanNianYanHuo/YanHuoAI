#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础功能测试：测试 Haystack 2.x 基本组件和导入
"""
import os
import sys
import unittest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicFunctionality(unittest.TestCase):
    """基础功能测试类"""

    def test_haystack_imports(self):
        """测试 Haystack 2.x 基本导入"""
        try:
            from haystack import Document
            from haystack.document_stores.types import DuplicatePolicy
            from haystack_integrations.document_stores.faiss import FAISSDocumentStore
            self.assertTrue(True, "Haystack 2.x 导入成功")
        except ImportError as e:
            self.fail(f"Haystack 2.x 导入失败: {e}")

    def test_document_creation(self):
        """测试文档创建"""
        from haystack import Document
        
        doc = Document(
            id="test_doc",
            content="测试文档内容",
            meta={"source": "test", "type": "unit_test"}
        )
        
        self.assertEqual(doc.id, "test_doc")
        self.assertEqual(doc.content, "测试文档内容")
        self.assertEqual(doc.meta["source"], "test")

    def test_embedder_creation(self):
        """测试 embedding 模型创建"""
        try:
            from storage.retriever import get_document_embedder, get_text_embedder
            
            doc_embedder = get_document_embedder()
            text_embedder = get_text_embedder()
            
            self.assertIsNotNone(doc_embedder)
            self.assertIsNotNone(text_embedder)
        except Exception as e:
            self.fail(f"Embedder 创建失败: {e}")

    def test_faiss_document_store_creation(self):
        """测试 FAISS document store 创建"""
        try:
            from rag.kb_manager import _get_document_store_for_kb
            
            store = _get_document_store_for_kb("test_basic")
            self.assertIsNotNone(store)
        except Exception as e:
            self.fail(f"FAISS DocumentStore 创建失败: {e}")


if __name__ == "__main__":
    unittest.main()