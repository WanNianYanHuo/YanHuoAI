#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试配置：测试相关的配置和工具函数
"""
import os
import sys
import tempfile
import shutil
from contextlib import contextmanager

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfig:
    """测试配置类"""
    
    # 测试数据
    SAMPLE_DOCUMENTS = [
        {
            "id": "doc1",
            "title": "糖尿病基础知识",
            "content": "糖尿病是一种慢性疾病，主要特征是血糖水平持续升高。患者需要通过饮食控制、运动和药物治疗来管理病情。"
        },
        {
            "id": "doc2", 
            "title": "高血压管理",
            "content": "高血压是心血管疾病的主要危险因素。患者应该定期监测血压，保持健康的生活方式，必要时服用降压药物。"
        },
        {
            "id": "doc3",
            "title": "中医理论基础",
            "content": "中医理论强调整体观念和辨证论治。通过望、闻、问、切四诊合参，了解患者的体质和病情，制定个性化的治疗方案。"
        }
    ]
    
    # 问答格式数据
    QA_DOCUMENTS = [
        {
            "question": "什么是糖尿病？",
            "answer": "糖尿病是一种以高血糖为特征的代谢性疾病，分为1型和2型两种主要类型。",
            "options": {
                "A": "传染性疾病",
                "B": "代谢性疾病", 
                "C": "遗传性疾病",
                "D": "免疫性疾病"
            }
        },
        {
            "question": "高血压的正常范围是多少？",
            "answer": "正常血压范围是收缩压小于120mmHg，舒张压小于80mmHg。"
        }
    ]
    
    # 测试用的大文档
    LARGE_DOCUMENT = {
        "id": "large_doc",
        "title": "大文档测试",
        "content": "这是一个用于测试的大文档。" * 1000  # 约 15KB
    }
    
    # 性能测试配置
    PERFORMANCE_CONFIG = {
        "small_batch_size": 10,
        "medium_batch_size": 50,
        "large_batch_size": 100,
        "concurrent_workers": 3,
        "search_iterations": 20
    }
    
    # 错误测试数据
    ERROR_TEST_DATA = {
        "empty_content": "",
        "whitespace_only": "   \n\t  ",
        "very_long_content": "测试内容 " * 50000,  # 约 200KB
        "special_characters": "测试 🚀 emoji ñáéíóú αβγδε 中文 日本語 한국어",
        "malformed_json": '{"invalid": json content}',
        "null_values": None
    }


class TestUtils:
    """测试工具类"""
    
    @staticmethod
    def create_temp_jsonl_file(data_list):
        """创建临时 JSONL 文件"""
        import json
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False, encoding='utf-8'
        )
        
        try:
            for item in data_list:
                temp_file.write(json.dumps(item, ensure_ascii=False) + '\n')
            temp_file.flush()
            return temp_file.name
        finally:
            temp_file.close()
    
    @staticmethod
    def create_temp_json_file(data):
        """创建临时 JSON 文件"""
        import json
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        )
        
        try:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.flush()
            return temp_file.name
        finally:
            temp_file.close()
    
    @staticmethod
    def create_temp_text_file(content):
        """创建临时文本文件"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        
        try:
            temp_file.write(content)
            temp_file.flush()
            return temp_file.name
        finally:
            temp_file.close()
    
    @staticmethod
    def cleanup_temp_file(file_path):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass
    
    @staticmethod
    def measure_time(func, *args, **kwargs):
        """测量函数执行时间"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    def measure_memory_usage(func, *args, **kwargs):
        """测量函数内存使用"""
        import psutil
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 获取最终内存
        final_memory = process.memory_info().rss
        memory_diff = final_memory - initial_memory
        
        return result, memory_diff
    
    @staticmethod
    def create_test_knowledge_base(kb_id, documents=None):
        """创建测试知识库并添加文档"""
        from api.server import knowledge_create, knowledge_add_text, KbCreateRequest, AddTextRequest
        
        # 创建知识库
        create_req = KbCreateRequest(kb_id=kb_id)
        knowledge_create(create_req)
        
        # 添加文档
        if documents is None:
            documents = TestConfig.SAMPLE_DOCUMENTS
        
        doc_ids = []
        for doc in documents:
            if isinstance(doc, dict):
                if "content" in doc:
                    content = doc["content"]
                elif "title" in doc and "content" in doc:
                    content = f"标题：{doc['title']}\n内容：{doc['content']}"
                else:
                    content = str(doc)
            else:
                content = str(doc)
            
            add_req = AddTextRequest(kb_id=kb_id, content=content)
            result = knowledge_add_text(add_req)
            doc_ids.append(result["doc_id"])
        
        return doc_ids
    
    @staticmethod
    def cleanup_test_knowledge_base(kb_id):
        """清理测试知识库"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(kb_id)
        except Exception:
            pass


@contextmanager
def temporary_knowledge_base(kb_id, documents=None):
    """临时知识库上下文管理器"""
    try:
        doc_ids = TestUtils.create_test_knowledge_base(kb_id, documents)
        yield kb_id, doc_ids
    finally:
        TestUtils.cleanup_test_knowledge_base(kb_id)


@contextmanager
def temporary_file(content, suffix='.txt'):
    """临时文件上下文管理器"""
    if suffix == '.jsonl':
        temp_file = TestUtils.create_temp_jsonl_file(content)
    elif suffix == '.json':
        temp_file = TestUtils.create_temp_json_file(content)
    else:
        temp_file = TestUtils.create_temp_text_file(content)
    
    try:
        yield temp_file
    finally:
        TestUtils.cleanup_temp_file(temp_file)


class MockObjects:
    """模拟对象类"""
    
    @staticmethod
    def mock_upload_file(content, filename="test.txt", content_type="text/plain"):
        """模拟上传文件对象"""
        from io import BytesIO
        
        class MockFile:
            def __init__(self, content, filename, content_type):
                self.filename = filename
                self.content_type = content_type
                self._content = content.encode('utf-8') if isinstance(content, str) else content
                self.file = BytesIO(self._content)
            
            async def read(self):
                return self._content
        
        return MockFile(content, filename, content_type)


# 测试装饰器
def skip_if_no_gpu(test_func):
    """如果没有 GPU 则跳过测试"""
    import unittest
    
    def wrapper(*args, **kwargs):
        try:
            import torch
            if not torch.cuda.is_available():
                raise unittest.SkipTest("需要 GPU 支持")
        except ImportError:
            raise unittest.SkipTest("需要 PyTorch 支持")
        
        return test_func(*args, **kwargs)
    
    return wrapper


def skip_if_slow(test_func):
    """如果设置了跳过慢速测试则跳过"""
    import unittest
    
    def wrapper(*args, **kwargs):
        if os.environ.get('SKIP_SLOW_TESTS', '').lower() in ('1', 'true', 'yes'):
            raise unittest.SkipTest("跳过慢速测试")
        
        return test_func(*args, **kwargs)
    
    return wrapper


def requires_internet(test_func):
    """需要网络连接的测试"""
    import unittest
    import socket
    
    def wrapper(*args, **kwargs):
        try:
            # 尝试连接到公共 DNS 服务器
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except OSError:
            raise unittest.SkipTest("需要网络连接")
        
        return test_func(*args, **kwargs)
    
    return wrapper


if __name__ == "__main__":
    # 测试配置和工具
    print("测试配置和工具类")
    print(f"样本文档数量: {len(TestConfig.SAMPLE_DOCUMENTS)}")
    print(f"问答文档数量: {len(TestConfig.QA_DOCUMENTS)}")
    print(f"大文档大小: {len(TestConfig.LARGE_DOCUMENT['content'])} 字符")
    
    # 测试临时文件创建
    with temporary_file("测试内容") as temp_file:
        print(f"创建临时文件: {temp_file}")
        assert os.path.exists(temp_file)
    
    print("配置和工具测试完成")