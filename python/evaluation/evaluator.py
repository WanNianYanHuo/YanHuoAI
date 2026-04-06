# evaluation/evaluator.py

"""
评估器模块
实现批量评估功能
"""

import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
import json
import os

from evaluation.evaluation_dataset import EvaluationDataset, EvaluationSample
from evaluation.metrics import calculate_all_metrics, calculate_average_metrics
from storage.document_store import get_document_store
from storage.retriever import get_retriever
from rag.qa_pipeline import qa_ask


@dataclass
class EvaluationResult:
    """
    单个样本的评估结果
    """
    question: str
    ground_truth: str
    predicted: str
    metrics: Dict[str, float]
    retrieval_docs_count: int  # 检索到的文档数量
    response_time: float  # 响应时间（秒）
    error: Optional[str] = None  # 错误信息（如果有）
    refs: Optional[List[Dict]] = None  # 引用文档
    reasoning_chain: Optional[Dict] = None  # 推理链信息（如果启用CoT）
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class Evaluator:
    """
    评估器类
    用于批量评估RAG系统性能
    """
    
    def __init__(self, retriever=None, use_cot=None):
        """
        初始化评估器
        
        Args:
            retriever: 检索器对象（如果为None，则自动初始化）
            use_cot: 是否使用推理链（None时使用配置文件的设置）
        """
        if retriever is None:
            store = get_document_store()
            self.retriever = get_retriever(store)
        else:
            self.retriever = retriever
        self.use_cot = use_cot
    
    def evaluate_sample(
        self, 
        sample: EvaluationSample,
        verbose: bool = False
    ) -> EvaluationResult:
        """
        评估单个样本
        
        Args:
            sample: 评估样本
            verbose: 是否打印详细信息
            
        Returns:
            EvaluationResult: 评估结果
        """
        start_time = time.time()
        error = None
        predicted = ""
        refs = []
        retrieval_docs_count = 0
        reasoning_chain = None
        
        try:
            if verbose:
                print(f"\n【问题】{sample.question}")
            
            # 调用RAG系统获取答案（支持推理链）
            result_tuple = qa_ask(
                sample.question, 
                self.retriever,
                use_cot=self.use_cot,
                return_reasoning=True  # 评估时记录推理过程
            )
            
            # 处理返回结果（可能是2元组或3元组）
            if len(result_tuple) == 3:
                predicted, refs, reasoning_chain = result_tuple
            else:
                predicted, refs = result_tuple
            
            retrieval_docs_count = len(refs) if refs else 0
            
            if verbose:
                print(f"【预测答案】{predicted[:100]}...")
                print(f"【标准答案】{sample.ground_truth[:100]}...")
                if reasoning_chain:
                    print(f"【推理步骤数】{len(reasoning_chain.reasoning_steps) if hasattr(reasoning_chain, 'reasoning_steps') else 0}")
            
        except Exception as e:
            error = str(e)
            if verbose:
                print(f"【错误】{error}")
        
        response_time = time.time() - start_time
        
        # 计算评估指标
        if predicted and not error:
            metrics = calculate_all_metrics(predicted, sample.ground_truth)
        else:
            metrics = {
                "exact_match": 0.0,
                "f1": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "bleu": 0.0,
                "rouge_l": 0.0,
                "semantic_similarity": 0.0
            }
        
        # 将推理链转换为字典（如果存在）
        reasoning_dict = None
        if reasoning_chain:
            reasoning_dict = reasoning_chain.to_dict()
        
        result = EvaluationResult(
            question=sample.question,
            ground_truth=sample.ground_truth,
            predicted=predicted,
            metrics=metrics,
            retrieval_docs_count=retrieval_docs_count,
            response_time=response_time,
            error=error,
            refs=refs,
            reasoning_chain=reasoning_dict
        )
        
        return result
    
    def evaluate_dataset(
        self,
        dataset: EvaluationDataset,
        verbose: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> List[EvaluationResult]:
        """
        批量评估数据集
        
        Args:
            dataset: 评估数据集
            verbose: 是否打印详细信息
            progress_callback: 进度回调函数（接受当前索引和总数）
            
        Returns:
            List[EvaluationResult]: 所有样本的评估结果
        """
        results = []
        total = len(dataset)
        
        if verbose:
            print(f"开始评估，共 {total} 个样本...")
        
        for i, sample in enumerate(dataset.samples):
            if verbose:
                print(f"\n[{i+1}/{total}] 评估中...")
            
            result = self.evaluate_sample(sample, verbose=verbose)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        if verbose:
            print(f"\n评估完成！共处理 {total} 个样本")
        
        return results
    
    def save_results(
        self,
        results: List[EvaluationResult],
        filepath: str,
        format: str = "jsonl"
    ):
        """
        保存评估结果到文件
        
        Args:
            results: 评估结果列表
            filepath: 保存路径
            format: 文件格式（jsonl 或 json）
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        if format == "jsonl":
            with open(filepath, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result.to_dict(), ensure_ascii=False) + '\n')
        elif format == "json":
            data = [result.to_dict() for result in results]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    @staticmethod
    def load_results(filepath: str, format: str = "jsonl") -> List[EvaluationResult]:
        """
        从文件加载评估结果
        
        Args:
            filepath: 文件路径
            format: 文件格式
            
        Returns:
            List[EvaluationResult]: 评估结果列表
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        results = []
        
        if format == "jsonl":
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    results.append(EvaluationResult(**data))
        elif format == "json":
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    results.append(EvaluationResult(**item))
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        return results
    
    @staticmethod
    def calculate_summary(results: List[EvaluationResult]) -> Dict:
        """
        计算评估结果摘要统计
        
        Args:
            results: 评估结果列表
            
        Returns:
            Dict: 摘要统计信息
        """
        if not results:
            return {}
        
        # 收集所有指标
        all_metrics = []
        total_time = 0.0
        total_errors = 0
        total_retrieval_docs = 0
        
        for result in results:
            all_metrics.append(result.metrics)
            total_time += result.response_time
            if result.error:
                total_errors += 1
            total_retrieval_docs += result.retrieval_docs_count
        
        # 计算平均指标
        avg_metrics = calculate_average_metrics(all_metrics)
        
        summary = {
            "total_samples": len(results),
            "average_metrics": avg_metrics,
            "average_response_time": total_time / len(results) if results else 0.0,
            "total_errors": total_errors,
            "error_rate": total_errors / len(results) if results else 0.0,
            "average_retrieval_docs": total_retrieval_docs / len(results) if results else 0.0,
            "total_time": total_time
        }
        
        return summary
