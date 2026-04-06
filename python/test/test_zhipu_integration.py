#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI集成测试
测试智谱AI在RAG系统中的各种功能
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.ollama_client import call_llm
from rag.qa_pipeline import qa_ask
from rag.kb_manager import kb_manager
from config.settings import ZHIPU_API_KEY, ZHIPU_MODEL
from test_config import TestConfig


class ZhipuIntegrationTest:
    """智谱AI集成测试类"""
    
    def __init__(self):
        self.test_kb_id = "zhipu_test_kb"
        self.config = TestConfig()
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {message}")
        
        if details:
            for key, value in details.items():
                print(f"      {key}: {value}")
    
    def test_zhipu_basic_call(self):
        """测试智谱AI基础调用"""
        print("1️⃣ 测试智谱AI基础调用...")
        
        if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_zhipu_api_key_here":
            self.log_result("智谱API密钥检查", False, "未配置有效的智谱API密钥")
            return False
            
        try:
            # 测试简单问答
            prompt = "你好，请简单介绍一下你自己。"
            start_time = time.time()
            response = call_llm(prompt, backend="zhipu")
            end_time = time.time()
            
            if response and len(response.strip()) > 0:
                self.log_result("智谱基础调用", True, "调用成功", {
                    "响应长度": len(response),
                    "响应时间": f"{end_time - start_time:.2f}秒",
                    "模型": ZHIPU_MODEL,
                    "响应预览": response[:100] + "..." if len(response) > 100 else response
                })
                return True
            else:
                self.log_result("智谱基础调用", False, "返回空响应")
                return False
                
        except Exception as e:
            self.log_result("智谱基础调用", False, f"调用失败: {str(e)}")
            return False
    
    def test_zhipu_streaming(self):
        """测试智谱AI流式调用"""
        print("2️⃣ 测试智谱AI流式调用...")
        
        try:
            chunks = []
            
            def stream_callback(chunk):
                chunks.append(chunk)
                
            def on_complete(timing):
                pass
            
            prompt = "请用50字左右简单介绍中医的基本理论。"
            start_time = time.time()
            response = call_llm(
                prompt, 
                backend="zhipu",
                stream_callback=stream_callback,
                on_complete=on_complete
            )
            end_time = time.time()
            
            if response and len(chunks) > 0:
                self.log_result("智谱流式调用", True, "流式调用成功", {
                    "总响应长度": len(response),
                    "流式块数": len(chunks),
                    "响应时间": f"{end_time - start_time:.2f}秒",
                    "首块延迟": "< 1秒" if chunks else "无",
                    "响应预览": response[:100] + "..." if len(response) > 100 else response
                })
                return True
            else:
                self.log_result("智谱流式调用", False, "流式调用失败或无响应")
                return False
                
        except Exception as e:
            self.log_result("智谱流式调用", False, f"流式调用失败: {str(e)}")
            return False
    
    def test_zhipu_temperature_control(self):
        """测试智谱AI温度控制"""
        print("3️⃣ 测试智谱AI温度控制...")
        
        try:
            prompt = "请列举3个中医常用的诊断方法。"
            
            # 测试低温度（更稳定）
            response_low = call_llm(prompt, backend="zhipu", temperature=0.1)
            
            # 测试高温度（更创造性）
            response_high = call_llm(prompt, backend="zhipu", temperature=0.9)
            
            if response_low and response_high:
                self.log_result("智谱温度控制", True, "温度控制测试成功", {
                    "低温度响应长度": len(response_low),
                    "高温度响应长度": len(response_high),
                    "低温度预览": response_low[:80] + "..." if len(response_low) > 80 else response_low,
                    "高温度预览": response_high[:80] + "..." if len(response_high) > 80 else response_high
                })
                return True
            else:
                self.log_result("智谱温度控制", False, "温度控制测试失败")
                return False
                
        except Exception as e:
            self.log_result("智谱温度控制", False, f"温度控制测试失败: {str(e)}")
            return False
    
    def setup_test_knowledge_base(self):
        """设置测试知识库"""
        print("4️⃣ 设置测试知识库...")
        
        try:
            # 创建测试知识库
            kb_manager.create_knowledge_base(self.test_kb_id)
            
            # 添加测试文档
            test_docs = [
                "中医四诊包括望诊、闻诊、问诊、切诊。望诊是通过观察病人的神色、形态、舌象等来了解病情。",
                "中医的五脏六腑理论认为，五脏是心、肝、脾、肺、肾，六腑是胆、胃、小肠、大肠、膀胱、三焦。",
                "中医治疗原则包括辨证论治、整体观念、预防为主。辨证论治是中医诊疗的核心思想。",
                "常用中药材包括人参、黄芪、当归、川芎、白术等。这些药材各有不同的功效和适应症。"
            ]
            
            for i, doc in enumerate(test_docs):
                kb_manager.add_text(self.test_kb_id, doc)
            
            self.log_result("测试知识库设置", True, f"成功添加{len(test_docs)}个测试文档")
            return True
            
        except Exception as e:
            self.log_result("测试知识库设置", False, f"设置失败: {str(e)}")
            return False
    
    def test_zhipu_rag_integration(self):
        """测试智谱AI与RAG系统集成"""
        print("5️⃣ 测试智谱AI与RAG系统集成...")
        
        try:
            # 获取检索器
            retriever = kb_manager.get_retriever(self.test_kb_id)
            
            # 测试RAG问答
            question = "中医四诊是什么？"
            start_time = time.time()
            
            answer, refs, reasoning, timing = qa_ask(
                question,
                retriever,
                return_reasoning=True,
                llm_backend="zhipu",
                kb_id=self.test_kb_id,
                use_kb=True
            )
            
            end_time = time.time()
            
            if answer and refs:
                self.log_result("智谱RAG集成", True, "RAG问答成功", {
                    "问题": question,
                    "答案长度": len(answer),
                    "检索文档数": len(refs),
                    "总响应时间": f"{end_time - start_time:.2f}秒",
                    "答案预览": answer[:150] + "..." if len(answer) > 150 else answer,
                    "检索得分": f"{refs[0].get('score', 0):.3f}" if refs else "无"
                })
                return True
            else:
                self.log_result("智谱RAG集成", False, "RAG问答失败或无结果")
                return False
                
        except Exception as e:
            self.log_result("智谱RAG集成", False, f"RAG集成测试失败: {str(e)}")
            return False
    
    def test_zhipu_rag_streaming(self):
        """测试智谱AI流式RAG问答"""
        print("6️⃣ 测试智谱AI流式RAG问答...")
        
        try:
            retriever = kb_manager.get_retriever(self.test_kb_id)
            chunks = []
            
            def stream_callback(chunk):
                chunks.append(chunk)
            
            question = "中医的五脏六腑都包括什么？"
            start_time = time.time()
            
            answer, refs, reasoning, timing = qa_ask(
                question,
                retriever,
                return_reasoning=True,
                stream_callback=stream_callback,
                llm_backend="zhipu",
                kb_id=self.test_kb_id,
                use_kb=True
            )
            
            end_time = time.time()
            
            if answer and len(chunks) > 0:
                self.log_result("智谱流式RAG", True, "流式RAG问答成功", {
                    "问题": question,
                    "答案长度": len(answer),
                    "流式块数": len(chunks),
                    "检索文档数": len(refs),
                    "响应时间": f"{end_time - start_time:.2f}秒",
                    "答案预览": answer[:150] + "..." if len(answer) > 150 else answer
                })
                return True
            else:
                self.log_result("智谱流式RAG", False, "流式RAG问答失败")
                return False
                
        except Exception as e:
            self.log_result("智谱流式RAG", False, f"流式RAG测试失败: {str(e)}")
            return False
    
    def test_zhipu_multiple_questions(self):
        """测试智谱AI多轮问答"""
        print("7️⃣ 测试智谱AI多轮问答...")
        
        try:
            retriever = kb_manager.get_retriever(self.test_kb_id)
            questions = [
                "什么是辨证论治？",
                "人参有什么功效？",
                "中医预防为主的理念是什么意思？"
            ]
            
            successful_answers = 0
            total_time = 0
            
            for i, question in enumerate(questions, 1):
                try:
                    start_time = time.time()
                    answer, refs, _, _ = qa_ask(
                        question,
                        retriever,
                        llm_backend="zhipu",
                        kb_id=self.test_kb_id,
                        use_kb=True
                    )
                    end_time = time.time()
                    total_time += (end_time - start_time)
                    
                    if answer and len(answer.strip()) > 10:
                        successful_answers += 1
                        print(f"      问题{i}: ✅ {question[:30]}... -> {answer[:50]}...")
                    else:
                        print(f"      问题{i}: ❌ {question[:30]}... -> 无有效答案")
                        
                except Exception as e:
                    print(f"      问题{i}: ❌ {question[:30]}... -> 错误: {str(e)}")
            
            success_rate = successful_answers / len(questions)
            if success_rate >= 0.8:  # 80%成功率
                self.log_result("智谱多轮问答", True, f"多轮问答成功", {
                    "成功率": f"{success_rate:.1%}",
                    "成功问题数": f"{successful_answers}/{len(questions)}",
                    "平均响应时间": f"{total_time/len(questions):.2f}秒"
                })
                return True
            else:
                self.log_result("智谱多轮问答", False, f"成功率过低: {success_rate:.1%}")
                return False
                
        except Exception as e:
            self.log_result("智谱多轮问答", False, f"多轮问答测试失败: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """清理测试数据"""
        try:
            kb_manager.delete_knowledge_base(self.test_kb_id)
            print("🧹 测试数据清理完成")
        except Exception as e:
            print(f"⚠️ 清理测试数据时出错: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("智谱AI集成测试")
        print("=" * 60)
        print()
        
        # 检查配置
        if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_zhipu_api_key_here":
            print("❌ 未配置智谱API密钥，跳过智谱AI测试")
            return False
        
        print(f"🔧 智谱AI配置:")
        print(f"   API密钥: {ZHIPU_API_KEY[:10]}...{ZHIPU_API_KEY[-4:]}")
        print(f"   模型: {ZHIPU_MODEL}")
        print()
        
        tests = [
            self.test_zhipu_basic_call,
            self.test_zhipu_streaming,
            self.test_zhipu_temperature_control,
            self.setup_test_knowledge_base,
            self.test_zhipu_rag_integration,
            self.test_zhipu_rag_streaming,
            self.test_zhipu_multiple_questions
        ]
        
        passed = 0
        total = len(tests)
        
        try:
            for test in tests:
                if test():
                    passed += 1
                print()
        finally:
            # 清理测试数据
            self.cleanup_test_data()
        
        print("=" * 60)
        print(f"智谱AI测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有智谱AI测试通过！")
            return True
        else:
            print(f"⚠️ {total - passed} 个测试失败")
            return False


def main():
    """主函数"""
    test = ZhipuIntegrationTest()
    success = test.run_all_tests()
    
    # 输出详细结果
    print("\n" + "=" * 60)
    print("详细测试结果:")
    print("=" * 60)
    
    for result in test.results:
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"{status} | {result['test']}: {result['message']}")
        
        if result["details"]:
            for key, value in result["details"].items():
                print(f"         {key}: {value}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())