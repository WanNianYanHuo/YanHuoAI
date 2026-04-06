# -*- coding: utf-8 -*-
"""
智能路由模块：自动判断问题复杂度并选择合适的处理策略
"""
import time
from typing import Optional, Tuple, Dict, Any
from llm.ollama_client import call_llm
from prompts.templates import (
    COMPLEXITY_JUDGE_PROMPT,
    QUESTION_REWRITE_PROMPT,
    KEYWORD_EXTRACTION_PROMPT,
)


def judge_complexity(question: str, llm_backend: Optional[str] = None) -> Tuple[str, float]:
    """
    判断问题复杂度
    
    Args:
        question: 用户问题
        llm_backend: LLM 后端（ollama/zhipu）
        
    Returns:
        (complexity, time): complexity 为 "simple" 或 "complex"，time 为判断耗时
    """
    start = time.time()
    
    prompt = COMPLEXITY_JUDGE_PROMPT.format(question=question)
    
    try:
        response = call_llm(prompt, backend=llm_backend, stream_callback=None)
        response = response.strip().lower()
        
        # 判断响应
        if "简单" in response or "simple" in response:
            complexity = "simple"
        elif "复杂" in response or "complex" in response:
            complexity = "complex"
        else:
            # 默认为简单问题
            print(f"[ROUTER] 无法判断复杂度，响应: {response}，默认为简单问题")
            complexity = "simple"
            
    except Exception as e:
        print(f"[ROUTER] 复杂度判断失败: {e}，默认为简单问题")
        complexity = "simple"
    
    elapsed = time.time() - start
    print(f"[ROUTER] 问题复杂度: {complexity}, 耗时: {elapsed:.2f}s")
    
    return complexity, elapsed



def rewrite_question(question: str, llm_backend: Optional[str] = None) -> Tuple[str, float]:
    """
    重写问题，使其更适合检索
    
    Args:
        question: 原始问题
        llm_backend: LLM 后端
        
    Returns:
        (rewritten_question, time): 重写后的问题和耗时
    """
    start = time.time()
    
    prompt = QUESTION_REWRITE_PROMPT.format(question=question)
    
    try:
        rewritten = call_llm(prompt, backend=llm_backend, stream_callback=None)
        rewritten = rewritten.strip()
        
        if not rewritten or len(rewritten) < 3:
            print(f"[ROUTER] 问题重写失败，使用原问题")
            rewritten = question
            
    except Exception as e:
        print(f"[ROUTER] 问题重写失败: {e}，使用原问题")
        rewritten = question
    
    elapsed = time.time() - start
    print(f"[ROUTER] 问题重写: {question} -> {rewritten}, 耗时: {elapsed:.2f}s")
    
    return rewritten, elapsed


def extract_keywords(question: str, llm_backend: Optional[str] = None) -> Tuple[str, float]:
    """
    提取关键词
    
    Args:
        question: 问题
        llm_backend: LLM 后端
        
    Returns:
        (keywords, time): 关键词字符串和耗时
    """
    start = time.time()
    
    prompt = KEYWORD_EXTRACTION_PROMPT.format(question=question)
    
    try:
        keywords = call_llm(prompt, backend=llm_backend, stream_callback=None)
        keywords = keywords.strip()
        
        if not keywords:
            print(f"[ROUTER] 关键词提取失败")
            keywords = ""
            
    except Exception as e:
        print(f"[ROUTER] 关键词提取失败: {e}")
        keywords = ""
    
    elapsed = time.time() - start
    print(f"[ROUTER] 关键词提取: {keywords}, 耗时: {elapsed:.2f}s")
    
    return keywords, elapsed



def smart_route(
    question: str,
    llm_backend: Optional[str] = None,
    force_complexity: Optional[str] = None
) -> Dict[str, Any]:
    """
    智能路由：判断问题复杂度并返回处理策略
    
    Args:
        question: 用户问题
        llm_backend: LLM 后端
        force_complexity: 强制指定复杂度（"simple"/"complex"），用于测试
        
    Returns:
        {
            "complexity": "simple" | "complex",
            "strategy": "simple_rag" | "cot_rag",
            "rewritten_question": str,  # 重写后的问题（仅复杂问题）
            "keywords": str,  # 关键词（仅复杂问题）
            "timing": {
                "judge_time": float,
                "rewrite_time": float,
                "keyword_time": float,
                "total_time": float
            }
        }
    """
    start_total = time.time()
    timing = {
        "judge_time": 0.0,
        "rewrite_time": 0.0,
        "keyword_time": 0.0,
        "total_time": 0.0
    }
    
    # 1. 判断复杂度
    if force_complexity:
        complexity = force_complexity
        timing["judge_time"] = 0.0
        print(f"[ROUTER] 强制指定复杂度: {complexity}")
    else:
        complexity, judge_time = judge_complexity(question, llm_backend)
        timing["judge_time"] = judge_time
    
    result = {
        "complexity": complexity,
        "strategy": "cot_rag" if complexity == "complex" else "simple_rag",
        "rewritten_question": question,
        "keywords": "",
        "timing": timing
    }
    
    # 2. 如果是复杂问题，进行问题重写和关键词提取
    if complexity == "complex":
        # 问题重写
        rewritten, rewrite_time = rewrite_question(question, llm_backend)
        result["rewritten_question"] = rewritten
        timing["rewrite_time"] = rewrite_time
        
        # 关键词提取
        keywords, keyword_time = extract_keywords(rewritten, llm_backend)
        result["keywords"] = keywords
        timing["keyword_time"] = keyword_time
    
    timing["total_time"] = time.time() - start_total
    
    print(f"[ROUTER] 路由结果: {result['strategy']}, 总耗时: {timing['total_time']:.2f}s")
    
    return result
