#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能测试：测试系统在不同负载下的性能表现
"""
import os
import sys
import unittest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPerformance(unittest.TestCase):
    """性能测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_performance"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_document_addition_performance(self):
        """测试文档添加性能"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 测试批量添加文档的性能
        start_time = time.time()
        
        for i in range(50):  # 添加 50 个文档
            content = f"性能测试文档 {i}，包含一些测试内容用于验证添加性能。" * 10
            kb_manager.add_text(self.test_kb_id, content)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"添加 50 个文档耗时: {duration:.2f} 秒")
        print(f"平均每个文档: {duration/50:.3f} 秒")
        
        # 验证文档数量
        count = kb_manager.count_documents(self.test_kb_id)
        self.assertEqual(count, 50)
        
        # 性能断言（根据实际情况调整）
        self.assertLess(duration, 300, "添加 50 个文档不应超过 5 分钟")

    def test_search_performance(self):
        """测试搜索性能"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库并添加测试数据
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 添加不同类型的文档
        test_docs = [
            "糖尿病是一种慢性疾病，需要长期管理和治疗。",
            "高血压患者应该注意饮食和运动。",
            "心脏病的预防非常重要，包括健康生活方式。",
            "癌症的早期发现和治疗是关键。",
            "中医理论强调整体观念和辨证论治。"
        ] * 10  # 重复 10 次，总共 50 个文档
        
        for i, content in enumerate(test_docs):
            kb_manager.add_text(self.test_kb_id, f"{content} 文档编号: {i}")
        
        # 测试搜索性能
        queries = ["糖尿病", "高血压", "心脏病", "癌症", "中医"]
        
        start_time = time.time()
        
        for query in queries:
            for _ in range(10):  # 每个查询重复 10 次
                results = kb_manager.search(self.test_kb_id, query, top_k=5)
                self.assertGreater(len(results), 0)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"执行 50 次搜索耗时: {duration:.2f} 秒")
        print(f"平均每次搜索: {duration/50:.3f} 秒")
        
        # 性能断言
        self.assertLess(duration, 60, "50 次搜索不应超过 1 分钟")

    def test_concurrent_operations_performance(self):
        """测试并发操作性能"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        def add_documents_batch(batch_id, num_docs):
            """添加一批文档"""
            results = []
            for i in range(num_docs):
                content = f"并发测试文档 批次{batch_id}-{i}，内容较长用于测试性能。" * 5
                result = kb_manager.add_text(self.test_kb_id, content)
                results.append(result)
            return results
        
        # 测试并发添加文档
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for batch_id in range(3):
                future = executor.submit(add_documents_batch, batch_id, 10)
                futures.append(future)
            
            # 等待所有任务完成
            all_results = []
            for future in as_completed(futures):
                batch_results = future.result()
                all_results.extend(batch_results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"并发添加 30 个文档耗时: {duration:.2f} 秒")
        
        # 验证结果
        self.assertEqual(len(all_results), 30)
        
        # 验证文档数量
        count = kb_manager.count_documents(self.test_kb_id)
        self.assertEqual(count, 30)

    def test_large_document_handling(self):
        """测试大文档处理性能"""
        from rag.kb_manager import kb_manager
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 创建大文档（约 10KB）
        large_content = "这是一个大文档的内容。" * 500
        
        start_time = time.time()
        
        # 添加大文档
        result = kb_manager.add_text(self.test_kb_id, large_content)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"添加大文档（约 10KB）耗时: {duration:.2f} 秒")
        
        # 验证添加成功
        self.assertIn("doc_count", result)
        
        # 测试搜索大文档
        start_time = time.time()
        results = kb_manager.search(self.test_kb_id, "大文档", top_k=5)
        end_time = time.time()
        search_duration = end_time - start_time
        
        print(f"搜索大文档耗时: {search_duration:.3f} 秒")
        
        self.assertGreater(len(results), 0)

    def test_memory_efficiency(self):
        """测试内存使用效率"""
        import psutil
        import gc
        from rag.kb_manager import kb_manager
        
        # 获取初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建知识库
        kb_manager.create_knowledge_base(self.test_kb_id)
        
        # 添加多个文档
        for i in range(20):
            content = f"内存效率测试文档 {i}，包含较多内容用于测试内存使用。" * 20
            kb_manager.add_text(self.test_kb_id, content)
        
        # 执行多次搜索
        for i in range(10):
            kb_manager.search(self.test_kb_id, f"测试 {i}", top_k=5)
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.1f} MB")
        print(f"最终内存: {final_memory:.1f} MB")
        print(f"内存增长: {memory_increase:.1f} MB")
        
        # 内存增长不应过大（根据实际情况调整阈值）
        self.assertLess(memory_increase, 500, "内存增长不应超过 500MB")

    def test_api_response_time(self):
        """测试 API 响应时间"""
        from api.server import (
            knowledge_create, knowledge_add_text, knowledge_list_docs,
            knowledge_docs_count, KbCreateRequest, AddTextRequest
        )
        
        # 测试创建知识库的响应时间
        start_time = time.time()
        create_req = KbCreateRequest(kb_id=self.test_kb_id)
        knowledge_create(create_req)
        create_time = time.time() - start_time
        
        print(f"创建知识库响应时间: {create_time:.3f} 秒")
        
        # 测试添加文本的响应时间
        start_time = time.time()
        add_req = AddTextRequest(kb_id=self.test_kb_id, content="API 响应时间测试文档")
        knowledge_add_text(add_req)
        add_time = time.time() - start_time
        
        print(f"添加文本响应时间: {add_time:.3f} 秒")
        
        # 测试列出文档的响应时间
        start_time = time.time()
        knowledge_list_docs(self.test_kb_id, limit=10, offset=0)
        list_time = time.time() - start_time
        
        print(f"列出文档响应时间: {list_time:.3f} 秒")
        
        # 测试文档计数的响应时间
        start_time = time.time()
        knowledge_docs_count(self.test_kb_id)
        count_time = time.time() - start_time
        
        print(f"文档计数响应时间: {count_time:.3f} 秒")
        
        # 响应时间断言
        self.assertLess(create_time, 5, "创建知识库不应超过 5 秒")
        self.assertLess(add_time, 30, "添加文本不应超过 30 秒")
        self.assertLess(list_time, 2, "列出文档不应超过 2 秒")
        self.assertLess(count_time, 2, "文档计数不应超过 2 秒")


if __name__ == "__main__":
    unittest.main()