# evaluation/visualizer.py

"""
结果可视化模块
生成评估结果的图表和报告
"""

import os
import json
from typing import List, Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from evaluation.evaluator import EvaluationResult
else:
    # 延迟导入，避免循环依赖
    try:
        from evaluation.evaluator import EvaluationResult
    except (ImportError, ModuleNotFoundError):
        # 如果导入失败，定义一个占位符类
        class EvaluationResult:
            pass


class EvaluationVisualizer:
    """
    评估结果可视化类
    """
    
    def __init__(self, results: List[EvaluationResult]):
        """
        初始化可视化器
        
        Args:
            results: 评估结果列表
        """
        self.results = results
    
    def generate_text_report(self) -> str:
        """
        生成文本格式的评估报告
        
        Returns:
            str: 报告文本
        """
        from evaluation.evaluator import Evaluator
        summary = Evaluator.calculate_summary(self.results)
        
        report = []
        report.append("=" * 80)
        report.append("RAG系统评估报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 总体统计
        report.append("【总体统计】")
        report.append(f"  总样本数: {summary['total_samples']}")
        report.append(f"  错误数量: {summary['total_errors']}")
        report.append(f"  错误率: {summary['error_rate']:.2%}")
        report.append(f"  平均响应时间: {summary['average_response_time']:.2f}秒")
        report.append(f"  平均检索文档数: {summary['average_retrieval_docs']:.2f}")
        report.append("")
        
        # 平均指标
        report.append("【平均评估指标】")
        avg_metrics = summary['average_metrics']
        for metric, value in avg_metrics.items():
            report.append(f"  {metric}: {value:.4f} ({value*100:.2f}%)")
        report.append("")
        
        # 详细结果（前10个）
        report.append("【详细结果（前10个样本）】")
        for i, result in enumerate(self.results[:10], 1):
            report.append(f"\n样本 {i}:")
            report.append(f"  问题: {result.question[:50]}...")
            report.append(f"  标准答案: {result.ground_truth[:50]}...")
            report.append(f"  预测答案: {result.predicted[:50]}...")
            report.append(f"  F1分数: {result.metrics.get('f1', 0):.4f}")
            report.append(f"  响应时间: {result.response_time:.2f}秒")
            if result.error:
                report.append(f"  错误: {result.error}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_text_report(self, filepath: str):
        """
        保存文本报告到文件
        
        Args:
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        report = self.generate_text_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def generate_json_report(self) -> Dict:
        """
        生成JSON格式的评估报告
        
        Returns:
            Dict: 报告数据
        """
        from evaluation.evaluator import Evaluator
        summary = Evaluator.calculate_summary(self.results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "detailed_results": [result.to_dict() for result in self.results]
        }
        
        return report
    
    def save_json_report(self, filepath: str):
        """
        保存JSON报告到文件
        
        Args:
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        report = self.generate_json_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def generate_markdown_report(self) -> str:
        """
        生成Markdown格式的评估报告
        
        Returns:
            str: Markdown报告
        """
        from evaluation.evaluator import Evaluator
        summary = Evaluator.calculate_summary(self.results)
        
        md = []
        md.append("# RAG系统评估报告\n")
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append("")
        
        # 总体统计
        md.append("## 总体统计\n")
        md.append("| 指标 | 值 |")
        md.append("|------|-----|")
        md.append(f"| 总样本数 | {summary['total_samples']} |")
        md.append(f"| 错误数量 | {summary['total_errors']} |")
        md.append(f"| 错误率 | {summary['error_rate']:.2%} |")
        md.append(f"| 平均响应时间 | {summary['average_response_time']:.2f}秒 |")
        md.append(f"| 平均检索文档数 | {summary['average_retrieval_docs']:.2f} |")
        md.append("")
        
        # 平均指标
        md.append("## 平均评估指标\n")
        md.append("| 指标 | 分数 | 百分比 |")
        md.append("|------|------|--------|")
        avg_metrics = summary['average_metrics']
        for metric, value in avg_metrics.items():
            md.append(f"| {metric} | {value:.4f} | {value*100:.2f}% |")
        md.append("")
        
        # 详细结果表格
        md.append("## 详细结果（前10个样本）\n")
        md.append("| # | 问题 | F1分数 | 响应时间(秒) | 错误 |")
        md.append("|--|------|--------|--------------|------|")
        for i, result in enumerate(self.results[:10], 1):
            question_short = result.question[:30] + "..." if len(result.question) > 30 else result.question
            error_str = "是" if result.error else "否"
            md.append(f"| {i} | {question_short} | {result.metrics.get('f1', 0):.4f} | {result.response_time:.2f} | {error_str} |")
        md.append("")
        
        return "\n".join(md)
    
    def save_markdown_report(self, filepath: str):
        """
        保存Markdown报告到文件
        
        Args:
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        report = self.generate_markdown_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def print_summary(self):
        """
        打印评估摘要到控制台
        """
        from evaluation.evaluator import Evaluator
        summary = Evaluator.calculate_summary(self.results)
        
        print("\n" + "=" * 80)
        print("评估结果摘要")
        print("=" * 80)
        print(f"总样本数: {summary['total_samples']}")
        print(f"错误数量: {summary['total_errors']} ({summary['error_rate']:.2%})")
        print(f"平均响应时间: {summary['average_response_time']:.2f}秒")
        print(f"平均检索文档数: {summary['average_retrieval_docs']:.2f}")
        print("\n平均评估指标:")
        avg_metrics = summary['average_metrics']
        for metric, value in avg_metrics.items():
            print(f"  {metric}: {value:.4f} ({value*100:.2f}%)")
        print("=" * 80)
