# evaluation/metrics.py

"""
评估指标模块
实现多种评估指标用于RAG系统性能评估
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import Counter


def exact_match(predicted: str, ground_truth: str) -> bool:
    """
    精确匹配：预测答案与标准答案是否完全一致
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        bool: 是否完全匹配
    """
    # 去除空白字符并转换为小写进行比较
    pred_clean = re.sub(r'\s+', ' ', predicted.strip().lower())
    gt_clean = re.sub(r'\s+', ' ', ground_truth.strip().lower())
    return pred_clean == gt_clean


def f1_score(predicted: str, ground_truth: str) -> float:
    """
    计算F1分数（基于词级别的重叠）
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        float: F1分数 (0-1)
    """
    # 中文分词：简单按字符分割（实际可以使用jieba等）
    pred_tokens = set(predicted.replace(' ', ''))
    gt_tokens = set(ground_truth.replace(' ', ''))
    
    if len(gt_tokens) == 0:
        return 1.0 if len(pred_tokens) == 0 else 0.0
    
    if len(pred_tokens) == 0:
        return 0.0
    
    # 计算交集
    common = pred_tokens & gt_tokens
    
    if len(common) == 0:
        return 0.0
    
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def precision_score(predicted: str, ground_truth: str) -> float:
    """
    计算精确率（Precision）
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        float: 精确率 (0-1)
    """
    pred_tokens = set(predicted.replace(' ', ''))
    gt_tokens = set(ground_truth.replace(' ', ''))
    
    if len(pred_tokens) == 0:
        return 0.0
    
    common = pred_tokens & gt_tokens
    return len(common) / len(pred_tokens)


def recall_score(predicted: str, ground_truth: str) -> float:
    """
    计算召回率（Recall）
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        float: 召回率 (0-1)
    """
    pred_tokens = set(predicted.replace(' ', ''))
    gt_tokens = set(ground_truth.replace(' ', ''))
    
    if len(gt_tokens) == 0:
        return 1.0 if len(pred_tokens) == 0 else 0.0
    
    common = pred_tokens & gt_tokens
    return len(common) / len(gt_tokens)


def bleu_score(predicted: str, ground_truth: str, n_gram: int = 4) -> float:
    """
    计算BLEU分数（简化版，基于n-gram重叠）
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        n_gram: n-gram的最大长度（默认4）
        
    Returns:
        float: BLEU分数 (0-1)
    """
    def get_ngrams(text: str, n: int) -> List[Tuple]:
        """获取n-gram"""
        tokens = list(text.replace(' ', ''))
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i+n]))
        return ngrams
    
    # 计算各阶n-gram的精确率
    precisions = []
    
    for n in range(1, n_gram + 1):
        pred_ngrams = Counter(get_ngrams(predicted, n))
        gt_ngrams = Counter(get_ngrams(ground_truth, n))
        
        if len(pred_ngrams) == 0:
            precisions.append(0.0)
            continue
        
        # 计算匹配的n-gram数量（取最小值，避免过度计数）
        matches = sum(min(pred_ngrams[ng], gt_ngrams[ng]) for ng in pred_ngrams)
        precision = matches / len(pred_ngrams) if len(pred_ngrams) > 0 else 0.0
        precisions.append(precision)
    
    # 几何平均
    if any(p == 0 for p in precisions):
        return 0.0
    
    bleu = (precisions[0] * precisions[1] * precisions[2] * precisions[3]) ** (1/4)
    
    # 简短惩罚（BP）
    pred_len = len(predicted.replace(' ', ''))
    gt_len = len(ground_truth.replace(' ', ''))
    
    if pred_len < gt_len:
        bp = pred_len / gt_len
    else:
        bp = 1.0
    
    return bleu * bp


def rouge_l_score(predicted: str, ground_truth: str) -> float:
    """
    计算ROUGE-L分数（基于最长公共子序列）
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        float: ROUGE-L分数 (0-1)
    """
    def lcs_length(s1: str, s2: str) -> int:
        """计算最长公共子序列长度"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    pred_clean = predicted.replace(' ', '')
    gt_clean = ground_truth.replace(' ', '')
    
    if len(gt_clean) == 0:
        return 1.0 if len(pred_clean) == 0 else 0.0
    
    if len(pred_clean) == 0:
        return 0.0
    
    lcs = lcs_length(pred_clean, gt_clean)
    
    precision = lcs / len(pred_clean) if len(pred_clean) > 0 else 0.0
    recall = lcs / len(gt_clean) if len(gt_clean) > 0 else 0.0
    
    if precision + recall == 0:
        return 0.0
    
    rouge_l = 2 * (precision * recall) / (precision + recall)
    return rouge_l


def semantic_similarity_score(predicted: str, ground_truth: str) -> float:
    """
    语义相似度分数（基于字符重叠的简化版本）
    实际应用中可以使用embedding模型计算真正的语义相似度
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        float: 相似度分数 (0-1)
    """
    # 简化版本：使用Jaccard相似度
    pred_chars = set(predicted.replace(' ', ''))
    gt_chars = set(ground_truth.replace(' ', ''))
    
    if len(pred_chars) == 0 and len(gt_chars) == 0:
        return 1.0
    
    if len(pred_chars) == 0 or len(gt_chars) == 0:
        return 0.0
    
    intersection = len(pred_chars & gt_chars)
    union = len(pred_chars | gt_chars)
    
    return intersection / union if union > 0 else 0.0


def calculate_all_metrics(predicted: str, ground_truth: str) -> Dict[str, float]:
    """
    计算所有评估指标
    
    Args:
        predicted: 模型预测的答案
        ground_truth: 标准答案
        
    Returns:
        Dict[str, float]: 包含所有指标的字典
    """
    return {
        "exact_match": 1.0 if exact_match(predicted, ground_truth) else 0.0,
        "f1": f1_score(predicted, ground_truth),
        "precision": precision_score(predicted, ground_truth),
        "recall": recall_score(predicted, ground_truth),
        "bleu": bleu_score(predicted, ground_truth),
        "rouge_l": rouge_l_score(predicted, ground_truth),
        "semantic_similarity": semantic_similarity_score(predicted, ground_truth)
    }


def calculate_average_metrics(results: List[Dict[str, float]]) -> Dict[str, float]:
    """
    计算平均评估指标
    
    Args:
        results: 所有样本的评估结果列表
        
    Returns:
        Dict[str, float]: 平均指标字典
    """
    if not results:
        return {}
    
    # 收集所有指标名称
    all_metrics = set()
    for result in results:
        all_metrics.update(result.keys())
    
    # 计算平均值
    averages = {}
    for metric in all_metrics:
        values = [r.get(metric, 0.0) for r in results if metric in r]
        if values:
            averages[metric] = sum(values) / len(values)
        else:
            averages[metric] = 0.0
    
    return averages
