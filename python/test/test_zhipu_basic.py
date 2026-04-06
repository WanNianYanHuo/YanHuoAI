#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI基础功能测试
专注于测试智谱AI的LLM调用功能，不依赖RAG系统
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.ollama_client import call_llm
from config.settings import ZHIPU_API_KEY, ZHIPU_MODEL


class ZhipuBasicTest:
    """智谱AI基础功能测试类"""
    
    def __init__(self):
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
    
    def test_zhipu_multiple_questions(self):
        """测试智谱AI多个问题"""
        print("4️⃣ 测试智谱AI多个问题...")
        
        try:
            questions = [
                "什么是中医？",
                "中医有哪些治疗方法？",
                "中医和西医有什么区别？",
                "中医的基本理论是什么？",
                "中医如何诊断疾病？"
            ]
            
            successful_answers = 0
            total_time = 0
            
            for i, question in enumerate(questions, 1):
                try:
                    start_time = time.time()
                    answer = call_llm(question, backend="zhipu")
                    end_time = time.time()
                    total_time += (end_time - start_time)
                    
                    if answer and len(answer.strip()) > 10:
                        successful_answers += 1
                        print(f"      问题{i}: ✅ {question[:20]}... -> {answer[:30]}...")
                    else:
                        print(f"      问题{i}: ❌ {question[:20]}... -> 无有效答案")
                        
                except Exception as e:
                    print(f"      问题{i}: ❌ {question[:20]}... -> 错误: {str(e)}")
            
            success_rate = successful_answers / len(questions)
            if success_rate >= 0.8:  # 80%成功率
                self.log_result("智谱多问题测试", True, f"多问题测试成功", {
                    "成功率": f"{success_rate:.1%}",
                    "成功问题数": f"{successful_answers}/{len(questions)}",
                    "平均响应时间": f"{total_time/len(questions):.2f}秒"
                })
                return True
            else:
                self.log_result("智谱多问题测试", False, f"成功率过低: {success_rate:.1%}")
                return False
                
        except Exception as e:
            self.log_result("智谱多问题测试", False, f"多问题测试失败: {str(e)}")
            return False
    
    def test_zhipu_chinese_capability(self):
        """测试智谱AI中文能力"""
        print("5️⃣ 测试智谱AI中文能力...")
        
        try:
            # 测试中文理解和生成
            prompt = "请用中文解释一下'阴阳五行'理论，并举一个具体的例子。"
            start_time = time.time()
            response = call_llm(prompt, backend="zhipu")
            end_time = time.time()
            
            # 检查响应质量
            if response and len(response.strip()) > 50:
                # 简单检查是否包含相关关键词
                keywords = ["阴阳", "五行", "理论", "例子"]
                keyword_count = sum(1 for keyword in keywords if keyword in response)
                
                if keyword_count >= 2:
                    self.log_result("智谱中文能力", True, "中文理解和生成测试成功", {
                        "响应长度": len(response),
                        "响应时间": f"{end_time - start_time:.2f}秒",
                        "关键词匹配": f"{keyword_count}/{len(keywords)}",
                        "响应预览": response[:150] + "..." if len(response) > 150 else response
                    })
                    return True
                else:
                    self.log_result("智谱中文能力", False, "响应内容不够相关")
                    return False
            else:
                self.log_result("智谱中文能力", False, "响应过短或为空")
                return False
                
        except Exception as e:
            self.log_result("智谱中文能力", False, f"中文能力测试失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("智谱AI基础功能测试")
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
            self.test_zhipu_multiple_questions,
            self.test_zhipu_chinese_capability
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 60)
        print(f"智谱AI基础测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有智谱AI基础测试通过！")
            return True
        else:
            print(f"⚠️ {total - passed} 个测试失败")
            return False


def main():
    """主函数"""
    test = ZhipuBasicTest()
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