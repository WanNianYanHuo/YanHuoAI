#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试：测试整个系统的端到端功能
"""
import os
import sys
import unittest
import json
import tempfile
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntegration(unittest.TestCase):
    """集成测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_integration"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_complete_workflow(self):
        """测试完整的工作流程"""
        from api.server import (
            knowledge_create, knowledge_add_text, knowledge_list_docs,
            knowledge_docs_count, knowledge_doc_detail, knowledge_doc_delete,
            KbCreateRequest, AddTextRequest
        )
        
        # 1. 创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        create_result = knowledge_create(create_req)
        self.assertEqual(create_result["status"], "ok")
        
        # 2. 添加多个文档
        test_contents = [
            "糖尿病是一种慢性疾病，需要长期管理。",
            "高血压患者应该注意饮食控制。",
            "心脏病的预防包括规律运动。",
            "中医理论强调整体观念。",
            "健康生活方式对疾病预防很重要。"
        ]
        
        doc_ids = []
        for content in test_contents:
            add_req = AddTextRequest(kb_id=self.test_kb_id, content=content)
            add_result = knowledge_add_text(add_req)
            self.assertEqual(add_result["status"], "ok")
            doc_ids.append(add_result["doc_id"])
        
        # 3. 验证文档数量
        count_result = knowledge_docs_count(self.test_kb_id)
        self.assertEqual(count_result["count"], len(test_contents))
        
        # 4. 列出文档
        docs_list = knowledge_list_docs(self.test_kb_id, limit=10, offset=0)
        self.assertEqual(len(docs_list), len(test_contents))
        
        # 5. 获取文档详情
        if docs_list:
            first_doc = docs_list[0]
            doc_detail = knowledge_doc_detail(self.test_kb_id, first_doc.id)
            self.assertEqual(doc_detail.id, first_doc.id)
            self.assertIsNotNone(doc_detail.content)
        
        # 6. 搜索功能测试
        from rag.kb_manager import kb_manager
        search_results = kb_manager.search(self.test_kb_id, "糖尿病", top_k=3)
        self.assertGreater(len(search_results), 0)
        
        # 验证搜索结果相关性
        found_diabetes = any("糖尿病" in result["content"] for result in search_results)
        self.assertTrue(found_diabetes)
        
        # 7. 删除文档
        if docs_list:
            delete_result = knowledge_doc_delete(self.test_kb_id, docs_list[0].id)
            self.assertEqual(delete_result["status"], "deleted")
            
            # 验证删除后的数量
            new_count = knowledge_docs_count(self.test_kb_id)
            self.assertEqual(new_count["count"], len(test_contents) - 1)

    def test_file_upload_workflow(self):
        """测试文件上传工作流程"""
        # 创建测试 JSONL 文件
        test_data = [
            {
                "id": "integration_test_1",
                "title": "集成测试文档1",
                "content": "这是第一个集成测试文档，用于验证文件上传功能。"
            },
            {
                "id": "integration_test_2", 
                "title": "集成测试文档2",
                "content": "这是第二个集成测试文档，包含更多测试内容。"
            },
            {
                "question": "什么是集成测试？",
                "answer": "集成测试是验证多个组件协同工作的测试方法。"
            }
        ]
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            for item in test_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
            temp_file = f.name
        
        try:
            # 模拟文件上传处理
            from api.server import knowledge_create, KbCreateRequest
            
            # 创建知识库
            create_req = KbCreateRequest(kb_id=self.test_kb_id)
            knowledge_create(create_req)
            
            # 读取并处理文件内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 模拟 JSONL 处理逻辑
            def _extract_from_item(item):
                if isinstance(item, dict):
                    for key in ("content", "text", "body"):
                        if key in item and isinstance(item[key], str):
                            return item[key]
                return None

            def _build_qa_content(obj: dict):
                # 优先处理问答格式
                q = obj.get("question")
                a = obj.get("answer")
                if isinstance(q, str) and q.strip() and isinstance(a, str) and a.strip():
                    return f"问题：{q.strip()}\n答案：{a.strip()}"
                
                # 处理标准格式：{title, content}
                title = obj.get("title")
                content = obj.get("content")
                if isinstance(title, str) and title.strip() and isinstance(content, str) and content.strip():
                    return f"标题：{title.strip()}\n内容：{content.strip()}"
                
                # fallback
                return _extract_from_item(obj)
            
            # 处理每一行
            from api.server import knowledge_add_text, AddTextRequest
            processed_count = 0
            
            for line_no, line in enumerate(content.splitlines(), start=1):
                s = line.strip()
                if not s:
                    continue
                
                try:
                    obj = json.loads(s)
                    if not isinstance(obj, dict):
                        continue
                    
                    text = _build_qa_content(obj)
                    if not text:
                        continue
                    
                    # 添加到知识库
                    add_req = AddTextRequest(kb_id=self.test_kb_id, content=text)
                    knowledge_add_text(add_req)
                    processed_count += 1
                    
                except Exception as e:
                    print(f"处理第 {line_no} 行时出错: {e}")
            
            # 验证处理结果
            self.assertEqual(processed_count, 3)
            
            # 验证知识库中的文档数量
            from api.server import knowledge_docs_count
            count_result = knowledge_docs_count(self.test_kb_id)
            self.assertGreater(count_result["count"], 0)
            
            # 测试搜索功能
            from rag.kb_manager import kb_manager
            search_results = kb_manager.search(self.test_kb_id, "集成测试", top_k=5)
            self.assertGreater(len(search_results), 0)
            
        finally:
            os.unlink(temp_file)

    def test_error_recovery(self):
        """测试错误恢复能力"""
        from api.server import (
            knowledge_create, knowledge_add_text,
            KbCreateRequest, AddTextRequest
        )
        from fastapi import HTTPException
        
        # 创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        # 测试部分成功的批量操作
        test_contents = [
            "正常文档内容1",
            "",  # 空内容，应该失败
            "正常文档内容2",
            "   ",  # 仅空白，应该失败
            "正常文档内容3"
        ]
        
        success_count = 0
        error_count = 0
        
        for content in test_contents:
            try:
                add_req = AddTextRequest(kb_id=self.test_kb_id, content=content)
                knowledge_add_text(add_req)
                success_count += 1
            except HTTPException:
                error_count += 1
        
        # 验证部分成功
        self.assertEqual(success_count, 3)
        self.assertEqual(error_count, 2)
        
        # 验证成功的文档确实被添加
        from api.server import knowledge_docs_count
        count_result = knowledge_docs_count(self.test_kb_id)
        self.assertGreater(count_result["count"], 0)

    def test_system_consistency(self):
        """测试系统一致性"""
        from api.server import (
            knowledge_create, knowledge_add_text, knowledge_list_docs,
            knowledge_docs_count, KbCreateRequest, AddTextRequest
        )
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        # 通过不同接口添加文档
        # 1. 通过 API 接口添加
        add_req = AddTextRequest(kb_id=self.test_kb_id, content="通过 API 添加的文档")
        knowledge_add_text(add_req)
        
        # 2. 通过 kb_manager 添加
        kb_manager.add_text(self.test_kb_id, "通过 kb_manager 添加的文档")
        
        # 验证两种方式添加的文档都能被检索到
        # 通过 API 检查
        api_count = knowledge_docs_count(self.test_kb_id)
        api_docs = knowledge_list_docs(self.test_kb_id, limit=10, offset=0)
        
        # 通过 kb_manager 检查
        manager_count = kb_manager.count_documents(self.test_kb_id)
        manager_docs = kb_manager.list_documents(self.test_kb_id, limit=10)
        
        # 验证一致性
        self.assertEqual(api_count["count"], manager_count)
        self.assertEqual(len(api_docs), len(manager_docs))
        self.assertEqual(api_count["count"], 2)

    def test_performance_under_load(self):
        """测试负载下的性能"""
        from api.server import (
            knowledge_create, knowledge_add_text,
            KbCreateRequest, AddTextRequest
        )
        import threading
        import time
        
        # 创建知识库
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        
        # 并发添加文档
        def add_documents_worker(worker_id, num_docs):
            for i in range(num_docs):
                content = f"负载测试文档 Worker-{worker_id} Doc-{i}"
                add_req = AddTextRequest(kb_id=self.test_kb_id, content=content)
                knowledge_add_text(add_req)
        
        start_time = time.time()
        
        # 创建多个线程
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=add_documents_worker, args=(worker_id, 5))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"并发添加 15 个文档耗时: {duration:.2f} 秒")
        
        # 验证所有文档都被添加
        from api.server import knowledge_docs_count
        count_result = knowledge_docs_count(self.test_kb_id)
        self.assertEqual(count_result["count"], 15)
        
        # 性能断言
        self.assertLess(duration, 120, "并发操作不应超过 2 分钟")


if __name__ == "__main__":
    unittest.main()