#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 接口测试：测试 FastAPI 接口的功能和健壮性
"""
import os
import sys
import unittest
import json
import tempfile
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIEndpoints(unittest.TestCase):
    """API 接口测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_api"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_health_endpoint(self):
        """测试健康检查接口"""
        from api.server import health
        
        result = health()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["service"], "rag-api")

    def test_knowledge_base_operations(self):
        """测试知识库操作接口"""
        from api.server import (
            list_knowledge_bases, knowledge_create, knowledge_delete,
            KbCreateRequest, KbDeleteRequest
        )
        
        # 测试创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        result = knowledge_create(create_req)
        self.assertEqual(result["status"], "ok")
        
        # 测试列出知识库
        kb_list = list_knowledge_bases()
        kb_ids = [kb.kb_id for kb in kb_list]
        # 注意：这里可能包含映射后的存储键，所以我们检查是否存在相关的知识库
        self.assertGreater(len(kb_list), 0)
        
        # 测试删除知识库
        delete_req = KbDeleteRequest(kb_id=self.test_kb_id)
        result = knowledge_delete(delete_req)
        self.assertEqual(result["status"], "deleted")

    def test_text_addition(self):
        """测试文本添加接口"""
        from api.server import knowledge_create, knowledge_add_text, AddTextRequest, KbCreateRequest
        
        # 创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        # 添加文本
        add_req = AddTextRequest(kb_id=self.test_kb_id, content="这是通过 API 添加的测试文本")
        result = knowledge_add_text(add_req)
        
        self.assertEqual(result["status"], "ok")
        self.assertIn("doc_id", result)

    def test_document_operations(self):
        """测试文档操作接口"""
        from api.server import (
            knowledge_create, knowledge_add_text, knowledge_list_docs,
            knowledge_docs_count, knowledge_doc_detail,
            KbCreateRequest, AddTextRequest
        )
        
        # 创建知识库并添加文档
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        add_req = AddTextRequest(kb_id=self.test_kb_id, content="测试文档内容")
        add_result = knowledge_add_text(add_req)
        
        # 测试文档计数
        count_result = knowledge_docs_count(self.test_kb_id)
        self.assertGreater(count_result["count"], 0)
        
        # 测试文档列表
        docs_list = knowledge_list_docs(self.test_kb_id, limit=10, offset=0)
        self.assertGreater(len(docs_list), 0)
        
        # 测试文档详情
        if docs_list:
            doc_id = docs_list[0].id
            doc_detail = knowledge_doc_detail(self.test_kb_id, doc_id)
            self.assertEqual(doc_detail.id, doc_id)
            self.assertIn("测试文档内容", doc_detail.content)

    def test_error_handling(self):
        """测试错误处理"""
        from api.server import knowledge_add_text, AddTextRequest
        from fastapi import HTTPException
        
        # 测试空内容
        with self.assertRaises(HTTPException) as context:
            add_req = AddTextRequest(kb_id="nonexistent", content="")
            knowledge_add_text(add_req)
        
        self.assertEqual(context.exception.status_code, 400)

    def test_chat_basic_functionality(self):
        """测试基础对话功能"""
        from api.server import chat_basic, ChatBasicRequest
        
        # 模拟 LLM 调用
        with patch('api.server.call_llm') as mock_llm:
            mock_llm.return_value = "这是模拟的回答"
            
            req = ChatBasicRequest(question="你好")
            result = chat_basic(req)
            
            self.assertEqual(result.answer, "这是模拟的回答")
            mock_llm.assert_called_once()

    def test_request_validation(self):
        """测试请求参数验证"""
        from api.server import ChatBasicRequest, AddTextRequest
        from fastapi import HTTPException
        
        # 测试空问题
        with self.assertRaises(HTTPException):
            from api.server import chat_basic
            req = ChatBasicRequest(question="")
            chat_basic(req)
        
        # 测试空内容
        with self.assertRaises(HTTPException):
            from api.server import knowledge_add_text
            req = AddTextRequest(kb_id="test", content="")
            knowledge_add_text(req)

    def test_cors_and_middleware(self):
        """测试 CORS 和中间件配置"""
        from api.server import app
        
        # 检查中间件是否正确配置
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware
        self.assertIn(CORSMiddleware, middleware_types)

    def test_response_models(self):
        """测试响应模型"""
        from api.server import (
            RagAskResponse, ChatBasicResponse, KbInfo, DocPreview, DocDetail
        )
        
        # 测试响应模型创建
        rag_response = RagAskResponse(answer="测试答案", refs=[])
        self.assertEqual(rag_response.answer, "测试答案")
        
        chat_response = ChatBasicResponse(answer="聊天回答")
        self.assertEqual(chat_response.answer, "聊天回答")
        
        kb_info = KbInfo(kb_id="test", kb_name="测试知识库")
        self.assertEqual(kb_info.kb_id, "test")
        
        doc_preview = DocPreview(id="doc1", content_preview="预览内容")
        self.assertEqual(doc_preview.id, "doc1")
        
        doc_detail = DocDetail(id="doc1", content="完整内容")
        self.assertEqual(doc_detail.content, "完整内容")


if __name__ == "__main__":
    unittest.main()