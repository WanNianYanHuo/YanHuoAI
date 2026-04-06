# evaluation/__init__.py

"""
评估系统模块
提供RAG系统性能评估功能
"""

from evaluation.metrics import (
    exact_match,
    f1_score,
    precision_score,
    recall_score,
    bleu_score,
    rouge_l_score,
    semantic_similarity_score,
    calculate_all_metrics,
    calculate_average_metrics
)

from evaluation.evaluation_dataset import (
    EvaluationSample,
    EvaluationDataset,
    create_sample_dataset
)

from evaluation.visualizer import (
    EvaluationVisualizer
)

# 延迟导入需要知识库的模块
# 这些模块在导入时会尝试连接知识库，可能导致错误
# 使用延迟导入，只在需要时才导入
def _lazy_import_evaluator():
    """延迟导入评估器模块"""
    from evaluation.evaluator import EvaluationResult, Evaluator
    return EvaluationResult, Evaluator

# 为了保持向后兼容，尝试导入（如果失败则提供占位符）
try:
    from evaluation.evaluator import (
        EvaluationResult,
        Evaluator
    )
except ImportError:
    # 如果导入失败（例如缺少依赖），提供占位符
    EvaluationResult = None
    Evaluator = None

__all__ = [
    # Metrics
    "exact_match",
    "f1_score",
    "precision_score",
    "recall_score",
    "bleu_score",
    "rouge_l_score",
    "semantic_similarity_score",
    "calculate_all_metrics",
    "calculate_average_metrics",
    # Dataset
    "EvaluationSample",
    "EvaluationDataset",
    "create_sample_dataset",
    # Evaluator (可能为None，如果导入失败)
    "EvaluationResult",
    "Evaluator",
    # Visualizer
    "EvaluationVisualizer",
    # Helper
    "_lazy_import_evaluator"
]
