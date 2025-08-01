#!/usr/bin/env python3
"""
Features package for Findly AI Search.

Contains AI-powered features:
- Price intent detection
- Enhanced benchmarking
- Conversational refinements
- Transfer learning
- Store profiling
- Adaptive filters
- Knowledge base building
- Continuous benchmarking
"""

from .price_intent import get_price_range, clean_query_from_price_intent, format_price_message
from .refinement_agent import ConversationalRefinementAgent
from .transfer_learning import TransferLearningEngine
from .store_profile import StoreProfileGenerator
from .adaptive_filters import AdaptiveFilterEngine
from .knowledge_base_builder import KnowledgeBaseBuilder
from .enhanced_benchmark_search import EnhancedSearchBenchmarker
from .continuous_benchmark import ContinuousBenchmarker

__all__ = [
    'get_price_range',
    'clean_query_from_price_intent', 
    'format_price_message',
    'ConversationalRefinementAgent',
    'TransferLearningEngine',
    'StoreProfileGenerator',
    'AdaptiveFilterEngine',
    'KnowledgeBaseBuilder',
    'EnhancedSearchBenchmarker',
    'ContinuousBenchmarker'
] 