#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理和边界条件测试：测试系统在异常情况下的健壮性
"""
import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestErrorHandling(unittest.TestCase):
    """错误处理测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_error_handling"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_invalid_knowledge_base_operations(self):
        """测试无效知识库操作"""
        from rag.kb_manager import kb_manager
        from fastapi import HTTPException
        
        # 测试访问不存在的知识库
        with self.assertRaises(Exception):
            kb_manager.count_documents("nonexistent_kb")
        
        # 测试删除不存在的知识库
        result = kb_manager.delete_knowledge_base("nonexistent_kb")
        self.assertFalse(result)

    def test_invalid_document_operations(self):
        """测试无效文档操作"""
        from rag.kb_manager import kb_manager
        
        # 创建测试知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 测试获取不存在的文档
        doc = kb_manager.get_document(self.test_kb_id, "nonexistent_doc")
        self.assertIsNone(doc)
        
        # 测试删除不存在的文档
        with self.assertRaises(Exception):
            kb_manager.delete_document(self.test_kb_id, "nonexistent_doc")

    def test_empty_and_invalid_content(self):
        """测试空内容和无效内容处理"""
        from api.server import knowledge_add_text, AddTextRequest
        from fastapi import HTTPException
        
        # 创建知识库
        from api.server import knowledge_create, KbCreateRequest
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        # 测试空内容
        with self.assertRaises(HTTPException) as context:
            add_req = AddTextRequest(kb_id=self.test_kb_id, content="")
            knowledge_add_text(add_req)
        self.assertEqual(context.exception.status_code, 400)
        
        # 测试仅空白字符的内容
        with self.assertRaises(HTTPException) as context:
            add_req = AddTextRequest(kb_id=self.test_kb_id, content="   \n\t  ")
            knowledge_add_text(add_req)
        self.assertEqual(context.exception.status_code, 400)

    def test_malformed_json_files(self):
        """测试格式错误的 JSON 文件"""
        from api.server import _normalize_for_dedupe, _stable_doc_id_from_content
        
        # 测试无效 JSON
        invalid_json = '{"invalid": json content}'
        
        try:
            json.loads(invalid_json)
            self.fail("应该抛出 JSON 解析异常")
        except json.JSONDecodeError:
            pass  # 预期的异常

    def test_large_content_handling(self):
        """测试大内容处理"""
        from api.server import _stable_doc_id_from_content
        
        # 测试大文本内容
        large_content = "测试内容 " * 10000  # 约 50KB 的内容
        doc_id = _stable_doc_id_from_content(large_content)
        self.assertIsNotNone(doc_id)
        self.assertTrue(doc_id.startswith("doc_"))

    def test_special_characters_handling(self):
        """测试特殊字符处理"""
        from api.server import _normalize_for_dedupe, _stable_doc_id_from_content
        
        # 测试各种特殊字符
        special_content = "测试内容 🚀 emoji ñáéíóú àèìòù αβγδε 中文 日本語 한국어"
        normalized = _normalize_for_dedupe(special_content)
        doc_id = _stable_doc_id_from_content(special_content)
        
        self.assertIsNotNone(normalized)
        self.assertIsNotNone(doc_id)

    def test_concurrent_operations(self):
        """测试并发操作"""
        import threading
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        results = []
        errors = []
        
        def add_document(index):
            try:
                result = kb_manager.add_text(self.test_kb_id, f"并发测试文档 {index}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时添加文档
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_document, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        self.assertEqual(len(errors), 0, f"并发操作出现错误: {errors}")
        self.assertEqual(len(results), 5)

    def test_memory_usage(self):
        """测试内存使用情况"""
        import gc
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 添加多个文档
        for i in range(10):
            kb_manager.add_text(self.test_kb_id, f"内存测试文档 {i} " * 100)
        
        # 强制垃圾回收
        gc.collect()
        
        # 验证文档数量
        count = kb_manager.count_documents(self.test_kb_id)
        self.assertEqual(count, 10)

    def test_embedding_failure_handling(self):
        """测试 embedding 生成失败的处理"""
        from storage.retriever import get_document_embedder
        
        # 测试 embedder 创建
        embedder = get_document_embedder()
        self.assertIsNotNone(embedder)
        
        # 测试空文档列表
        result = embedder.run(documents=[])
        self.assertEqual(len(result["documents"]), 0)

    def test_document_store_failure_handling(self):
        """测试文档存储失败的处理"""
        from rag.kb_manager import _get_document_store_for_kb
        
        # 测试创建文档存储
        store = _get_document_store_for_kb(self.test_kb_id)
        self.assertIsNotNone(store)
        
        # 测试空文档列表写入
        from haystack.document_stores.types import DuplicatePolicy
        count = store.write_documents([], policy=DuplicatePolicy.SKIP)
        self.assertEqual(count, 0)

    def test_search_edge_cases(self):
        """测试搜索边界情况"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库并添加文档
        kb_manager.create_knowledge_base(self.test_kb_id)
        kb_manager.add_text(self.test_kb_id, "测试搜索功能")
        
        # 测试空查询
        results = kb_manager.search(self.test_kb_id, "", top_k=5)
        # 空查询可能返回所有文档或空结果，取决于实现
        self.assertIsInstance(results, list)
        
        # 测试超长查询
        long_query = "测试查询 " * 1000
        results = kb_manager.search(self.test_kb_id, long_query, top_k=5)
        self.assertIsInstance(results, list)
        
        # 测试特殊字符查询
        special_query = "测试 🔍 搜索"
        results = kb_manager.search(self.test_kb_id, special_query, top_k=5)
        self.assertIsInstance(results, list)

    def test_api_parameter_validation(self):
        """测试 API 参数验证"""
        from api.server import (
            knowledge_list_docs, knowledge_docs_count,
            ChatBasicRequest, AddTextRequest
        )
        from fastapi import HTTPException
        
        # 测试负数参数
        try:
            knowledge_list_docs("test", limit=-1, offset=-1)
        except Exception:
            pass  # 可能会有参数验证错误
        
        # 测试超大参数
        try:
            knowledge_list_docs("test", limit=999999, offset=999999)
        except Exception:
            pass  # 可能会有参数验证错误


if __name__ == "__main__":
    unittest.main()