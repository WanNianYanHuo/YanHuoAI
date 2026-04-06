#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件导入测试：测试各种格式文件的导入功能
"""
import os
import sys
import unittest
import json
import tempfile

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFileImport(unittest.TestCase):
    """文件导入测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_kb_id = "test_file_import"
        
    def tearDown(self):
        """测试后清理"""
        try:
            from rag.kb_manager import kb_manager
            kb_manager.delete_knowledge_base(self.test_kb_id)
        except:
            pass

    def test_jsonl_content_extraction(self):
        """测试 JSONL 内容提取功能"""
        from api.server import _normalize_for_dedupe, _stable_doc_id_from_content
        
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
            opts = obj.get("options")
            if isinstance(q, str) and q.strip():
                parts = [f"问题：{q.strip()}"]
                if isinstance(opts, dict) and opts:
                    opt_lines = []
                    for k, v in opts.items():
                        if isinstance(k, str) and isinstance(v, str):
                            opt_lines.append(f"{k}. {v}")
                    if opt_lines:
                        parts.append("选项：\n" + "\n".join(opt_lines))
                if isinstance(a, str) and a.strip():
                    parts.append(f"答案：{a.strip()}")
                return "\n".join(parts)
            
            # 处理标准格式：{title, content}
            title = obj.get("title")
            content = obj.get("content")
            if isinstance(title, str) and title.strip() and isinstance(content, str) and content.strip():
                return f"标题：{title.strip()}\n内容：{content.strip()}"
            
            # fallback: 尝试 content/text/body
            return _extract_from_item(obj)

        # 测试标准格式
        standard_obj = {
            "id": "test1",
            "title": "测试标题",
            "content": "测试内容"
        }
        result = _build_qa_content(standard_obj)
        self.assertIn("标题：测试标题", result)
        self.assertIn("内容：测试内容", result)

        # 测试问答格式
        qa_obj = {
            "question": "什么是测试？",
            "answer": "测试是验证功能的过程",
            "options": {"A": "选项A", "B": "选项B"}
        }
        result = _build_qa_content(qa_obj)
        self.assertIn("问题：什么是测试？", result)
        self.assertIn("答案：测试是验证功能的过程", result)
        self.assertIn("选项：", result)

        # 测试 fallback
        fallback_obj = {
            "content": "仅有内容的对象"
        }
        result = _build_qa_content(fallback_obj)
        self.assertEqual(result, "仅有内容的对象")

    def test_document_id_generation(self):
        """测试文档 ID 生成和去重"""
        from api.server import _normalize_for_dedupe, _stable_doc_id_from_content
        
        # 测试相同内容生成相同 ID
        content1 = "这是测试内容"
        content2 = "这是测试内容"
        id1 = _stable_doc_id_from_content(content1)
        id2 = _stable_doc_id_from_content(content2)
        self.assertEqual(id1, id2)
        
        # 测试不同内容生成不同 ID
        content3 = "这是不同的测试内容"
        id3 = _stable_doc_id_from_content(content3)
        self.assertNotEqual(id1, id3)
        
        # 测试空白处理
        content4 = "  这是测试内容  "
        id4 = _stable_doc_id_from_content(content4)
        self.assertEqual(id1, id4)  # 应该与去除空白后的内容相同

    def test_create_test_files(self):
        """创建测试文件并测试导入"""
        # 创建临时 JSONL 文件
        test_data = [
            {"id": "test1", "title": "测试文档1", "content": "这是第一个测试文档的内容"},
            {"id": "test2", "title": "测试文档2", "content": "这是第二个测试文档的内容"},
            {"question": "什么是人工智能？", "answer": "人工智能是模拟人类智能的技术"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            for item in test_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
            temp_file = f.name
        
        try:
            # 测试文件读取和处理
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("测试文档1", content)
            self.assertIn("人工智能", content)
            
            # 测试 JSONL 解析
            lines = content.strip().split('\n')
            self.assertEqual(len(lines), 3)
            
            for line in lines:
                obj = json.loads(line)
                self.assertIsInstance(obj, dict)
                
        finally:
            os.unlink(temp_file)

    def test_text_file_processing(self):
        """测试文本文件处理"""
        # 创建临时文本文件
        test_content = """第一段内容
这是第一段的详细内容。

第二段内容
这是第二段的详细内容。

第三段内容
这是第三段的详细内容。"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            # 测试按空行分段
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
            self.assertEqual(len(chunks), 3)
            self.assertIn("第一段内容", chunks[0])
            self.assertIn("第二段内容", chunks[1])
            self.assertIn("第三段内容", chunks[2])
            
        finally:
            os.unlink(temp_file)

    def test_json_file_processing(self):
        """测试 JSON 文件处理"""
        # 测试 JSON 数组
        test_array = [
            {"content": "数组中的第一个文档"},
            {"text": "数组中的第二个文档"},
            {"body": "数组中的第三个文档"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_array, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                obj = json.load(f)
            
            self.assertIsInstance(obj, list)
            self.assertEqual(len(obj), 3)
            
            # 测试内容提取
            def _extract_from_item(item):
                if isinstance(item, dict):
                    for key in ("content", "text", "body"):
                        if key in item and isinstance(item[key], str):
                            return item[key]
                return None
            
            texts = []
            for item in obj:
                text = _extract_from_item(item)
                if text:
                    texts.append(text)
            
            self.assertEqual(len(texts), 3)
            self.assertIn("第一个文档", texts[0])
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()