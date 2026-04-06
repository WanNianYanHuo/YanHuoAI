# evaluation/evaluation_dataset.py

"""
评估数据集模块
定义评估数据集的格式和加载器
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class EvaluationSample:
    """
    单个评估样本
    """
    question: str  # 问题
    ground_truth: str  # 标准答案
    context: Optional[str] = None  # 可选的上下文信息
    category: Optional[str] = None  # 问题类别（如：诊断、治疗、方剂等）
    difficulty: Optional[str] = None  # 难度等级（easy, medium, hard）
    metadata: Optional[Dict] = None  # 其他元数据
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationSample':
        """从字典创建"""
        return cls(**data)


class EvaluationDataset:
    """
    评估数据集类
    """
    
    def __init__(self, samples: List[EvaluationSample]):
        """
        初始化数据集
        
        Args:
            samples: 评估样本列表
        """
        self.samples = samples
    
    def __len__(self) -> int:
        """返回数据集大小"""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> EvaluationSample:
        """获取指定索引的样本"""
        return self.samples[idx]
    
    def save(self, filepath: str, format: str = "jsonl"):
        """
        保存数据集到文件
        
        Args:
            filepath: 保存路径
            format: 文件格式（jsonl 或 json）
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        if format == "jsonl":
            with open(filepath, 'w', encoding='utf-8') as f:
                for sample in self.samples:
                    f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + '\n')
        elif format == "json":
            data = [sample.to_dict() for sample in self.samples]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    @classmethod
    def load(cls, filepath: str, format: str = "jsonl") -> 'EvaluationDataset':
        """
        从文件加载数据集
        
        Args:
            filepath: 文件路径
            format: 文件格式（jsonl 或 json）
            
        Returns:
            EvaluationDataset: 加载的数据集
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        samples = []
        
        if format == "jsonl":
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    samples.append(EvaluationSample.from_dict(data))
        elif format == "json":
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    samples.append(EvaluationSample.from_dict(item))
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        return cls(samples)
    
    def get_by_category(self, category: str) -> 'EvaluationDataset':
        """
        按类别筛选样本
        
        Args:
            category: 类别名称
            
        Returns:
            EvaluationDataset: 筛选后的数据集
        """
        filtered = [s for s in self.samples if s.category == category]
        return EvaluationDataset(filtered)
    
    def get_by_difficulty(self, difficulty: str) -> 'EvaluationDataset':
        """
        按难度筛选样本
        
        Args:
            difficulty: 难度等级
            
        Returns:
            EvaluationDataset: 筛选后的数据集
        """
        filtered = [s for s in self.samples if s.difficulty == difficulty]
        return EvaluationDataset(filtered)
    
    def get_statistics(self) -> Dict:
        """
        获取数据集统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            "total_samples": len(self.samples),
            "categories": {},
            "difficulties": {}
        }
        
        for sample in self.samples:
            # 统计类别
            cat = sample.category or "unknown"
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
            
            # 统计难度
            diff = sample.difficulty or "unknown"
            stats["difficulties"][diff] = stats["difficulties"].get(diff, 0) + 1
        
        return stats


def create_sample_dataset() -> EvaluationDataset:
    """
    创建示例数据集（用于测试）
    
    Returns:
        EvaluationDataset: 示例数据集
    """
    samples = [
        EvaluationSample(
            question="什么是感冒？",
            ground_truth="感冒是一种常见的上呼吸道感染疾病，主要由病毒引起，症状包括鼻塞、流涕、咳嗽、发热等。",
            category="基础概念",
            difficulty="easy"
        ),
        EvaluationSample(
            question="中医如何治疗失眠？",
            ground_truth="中医治疗失眠主要从心、肝、脾、肾等脏腑入手，常用方法包括中药调理、针灸、推拿等，需要辨证论治。",
            category="治疗方法",
            difficulty="medium"
        ),
        EvaluationSample(
            question="四物汤的组成是什么？",
            ground_truth="四物汤由当归、川芎、白芍、熟地黄四味药组成，是补血调经的经典方剂。",
            category="方剂",
            difficulty="easy"
        ),
    ]
    
    return EvaluationDataset(samples)
