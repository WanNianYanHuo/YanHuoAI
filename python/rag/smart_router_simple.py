#!/usr/bin/env python3
"""
简化版智能路由模块
避免复杂的LLM调用可能导致的卡住问题
"""

import time
import re
from typing import Optional, Dict, Any

def simple_complexity_judge(question: str) -> str:
    """
    基于规则的简单复杂度判断，避免LLM调用
    """
    question = question.strip()
    
    # 复杂问题的特征
    complex_indicators = [
        # 长度指标
        len(question) > 50,
        
        # 关键词指标
        any(word in question for word in [
            "详细分析", "综合", "机制", "原理", "为什么", "如何预防", 
            "治疗方案", "诊疗建议", "对比", "区别", "关系", "影响因素",
            "病理", "生理", "药理", "并发症", "预后", "鉴别诊断"
        ]),
        
        # 句式指标
        "？" in question and question.count("？") > 1,
        "，" in question and question.count("，") > 2,
        
        # 复合问题指标
        any(word in question for word in ["以及", "同时", "另外", "此外", "包括"]),
        
        # 分析类问题
        any(word in question for word in ["分析", "解释", "说明", "阐述", "论述"]),
    ]
    
    # 简单问题的特征
    simple_indicators = [
        # 简单疑问词开头
        question.startswith(("什么是", "如何", "怎么", "哪些", "是否")),
        
        # 定义类问题
        any(word in question for word in ["定义", "概念", "含义"]),
        
        # 简单查询
        any(word in question for word in ["症状", "表现", "特点", "作用"]) and len(question) < 30,
    ]
    
    complex_score = sum(complex_indicators)
    simple_score = sum(simple_indicators)
    
    # 判断逻辑
    if complex_score >= 2:
        return "complex"
    elif simple_score >= 1 and complex_score == 0:
        return "simple"
    elif len(question) > 80:
        return "complex"
    else:
        return "simple"

def simple_question_rewrite(question: str) -> str:
    """
    基于规则的简单问题重写
    """
    # 基本清理
    question = question.strip()
    
    # 简单的重写规则
    replacements = {
        "怎么治": "如何治疗",
        "怎么办": "如何处理",
        "什么原因": "病因是什么",
        "为啥": "为什么",
        "咋": "怎么",
    }
    
    for old, new in replacements.items():
        question = question.replace(old, new)
    
    return question

def simple_extract_keywords(question: str) -> str:
    """
    基于规则的简单关键词提取
    """
    # 医学相关关键词库
    medical_terms = [
        # 疾病
        "糖尿病", "高血压", "冠心病", "脑梗", "肺炎", "感冒", "发热", "咳嗽",
        "头痛", "胸痛", "腹痛", "恶心", "呕吐", "腹泻", "便秘", "失眠",
        
        # 器官系统
        "心脏", "肺", "肝", "肾", "脾", "胃", "肠", "脑", "眼", "耳", "鼻", "喉",
        "血管", "神经", "肌肉", "骨骼", "皮肤",
        
        # 中医术语
        "气血", "阴阳", "五脏", "六腑", "经络", "穴位", "脉象", "舌象",
        "寒热", "虚实", "表里", "气虚", "血瘀", "痰湿", "火热",
        
        # 治疗方法
        "针灸", "推拿", "按摩", "拔罐", "刮痧", "艾灸", "中药", "汤剂",
        "丸剂", "散剂", "膏剂", "药膳", "食疗",
        
        # 诊断方法
        "望诊", "闻诊", "问诊", "切诊", "四诊", "辨证", "论治",
    ]
    
    # 提取出现在问题中的医学术语
    found_terms = []
    for term in medical_terms:
        if term in question:
            found_terms.append(term)
    
    # 如果找到的术语太少，添加一些通用词
    if len(found_terms) < 2:
        # 提取可能的关键词（简单的词语分割）
        words = re.findall(r'[\u4e00-\u9fff]+', question)  # 提取中文词语
        words = [w for w in words if len(w) >= 2 and w not in ["什么", "如何", "怎么", "为什么", "是否"]]
        found_terms.extend(words[:3])
    
    # 去重并限制数量
    keywords = list(dict.fromkeys(found_terms))[:5]
    
    return ",".join(keywords) if keywords else "医学咨询"

def smart_route_simple(
    question: str,
    llm_backend: Optional[str] = None,
    force_complexity: Optional[str] = None
) -> Dict[str, Any]:
    """
    简化版智能路由，避免LLM调用可能导致的卡住问题
    """
    start_total = time.time()
    
    print(f"[SIMPLE_ROUTER] 处理问题: {question[:50]}...")
    
    # 1. 判断复杂度
    if force_complexity:
        complexity = force_complexity
        judge_time = 0.0
        print(f"[SIMPLE_ROUTER] 强制指定复杂度: {complexity}")
    else:
        start_judge = time.time()
        complexity = simple_complexity_judge(question)
        judge_time = time.time() - start_judge
        print(f"[SIMPLE_ROUTER] 复杂度判断: {complexity}, 耗时: {judge_time:.3f}s")
    
    # 2. 问题重写（仅复杂问题）
    rewrite_time = 0.0
    if complexity == "complex":
        start_rewrite = time.time()
        rewritten_question = simple_question_rewrite(question)
        rewrite_time = time.time() - start_rewrite
        print(f"[SIMPLE_ROUTER] 问题重写: {question} -> {rewritten_question}")
    else:
        rewritten_question = question
    
    # 3. 关键词提取（仅复杂问题）
    keyword_time = 0.0
    if complexity == "complex":
        start_keyword = time.time()
        keywords = simple_extract_keywords(rewritten_question)
        keyword_time = time.time() - start_keyword
        print(f"[SIMPLE_ROUTER] 关键词提取: {keywords}")
    else:
        keywords = simple_extract_keywords(question)
    
    total_time = time.time() - start_total
    
    result = {
        "complexity": complexity,
        "strategy": "cot_rag" if complexity == "complex" else "simple_rag",
        "rewritten_question": rewritten_question,
        "keywords": keywords,
        "timing": {
            "judge_time": judge_time,
            "rewrite_time": rewrite_time,
            "keyword_time": keyword_time,
            "total_time": total_time
        }
    }
    
    print(f"[SIMPLE_ROUTER] 路由结果: {result['strategy']}, 总耗时: {total_time:.3f}s")
    
    return result

# 测试函数
def test_simple_router():
    """测试简化版智能路由"""
    test_cases = [
        "什么是高血压？",
        "糖尿病有哪些症状？",
        "请详细分析糖尿病患者出现视力模糊、多饮多尿、体重下降等症状的病理机制，并提供综合的诊疗建议，包括药物治疗、饮食调理和生活方式干预的具体方案。",
        "中医如何调理脾胃虚弱？",
        "高血压和糖尿病的关系是什么？如何预防并发症？",
    ]
    
    print("🧪 测试简化版智能路由")
    print("=" * 50)
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {question}")
        result = smart_route_simple(question)
        print(f"结果: {result['complexity']} -> {result['strategy']}")
        print(f"关键词: {result['keywords']}")
        print(f"耗时: {result['timing']['total_time']:.3f}s")

if __name__ == "__main__":
    test_simple_router()