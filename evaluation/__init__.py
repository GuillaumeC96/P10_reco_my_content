"""
Evaluation Module for Recommender Systems
==========================================

This module provides tools for evaluating recommender systems:
- Metrics: HR@N, MRR, Precision, Recall, NDCG, Coverage, Diversity
- Baselines: Random, Popular, Recent, Item-kNN, Content-Based, Collaborative
- Benchmarking: Compare multiple methods
"""

from .metrics import RecommenderMetrics, MetricsAggregator
from .baselines import create_baseline
from .data_split import TrainTestSplitter, EvaluationSampler

__all__ = [
    'RecommenderMetrics',
    'MetricsAggregator',
    'create_baseline',
    'TrainTestSplitter',
    'EvaluationSampler'
]
