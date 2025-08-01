#!/usr/bin/env python3
"""
Continuous Benchmarking System

This script runs benchmarks continuously and detects performance regressions.
It can be run manually or via cronjob for automated monitoring.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import sqlite3
import statistics

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .enhanced_benchmark_search import EnhancedSearchBenchmarker
from .knowledge_base_builder import KnowledgeBaseBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousBenchmarker:
    """Continuous benchmarking system with regression detection."""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 store_id: Optional[str] = None,
                 db_path: str = "search_knowledge_base.db",
                 regression_threshold: float = 0.1):  # 10% threshold
        self.base_url = base_url
        self.store_id = store_id
        self.db_path = db_path
        self.regression_threshold = regression_threshold
        self.knowledge_builder = KnowledgeBaseBuilder(db_path)
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
    
    async def run_daily_benchmark(self, 
                                 queries_file: str = "benchmark_queries.csv",
                                 results_file: Optional[str] = None) -> Dict[str, any]:
        """Run daily benchmark and detect regressions."""
        timestamp = datetime.now()
        
        # Generate results filename with timestamp
        if not results_file:
            results_file = f"benchmark_results_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
        
        logger.info(f"🚀 Starting daily benchmark for store {self.store_id}")
        
        # Run benchmark
        async with EnhancedSearchBenchmarker(
            base_url=self.base_url,
            headless=True,  # Run in headless mode for automation
            store_id=self.store_id
        ) as benchmarker:
            results = await benchmarker.run_enhanced_benchmark(
                queries_file=queries_file,
                results_file=results_file
            )
        
        # Process results and detect regressions
        regression_report = self._detect_regressions(results, timestamp)
        
        # Save to knowledge base
        if results:
            self.knowledge_builder.process_benchmark_results(results_file, self.store_id)
        
        # Log results
        self._log_benchmark_results(results, regression_report, timestamp)
        
        return {
            "timestamp": timestamp.isoformat(),
            "results_file": results_file,
            "total_queries": len(results),
            "regression_report": regression_report,
            "success": True
        }
    
    def _detect_regressions(self, results: List, timestamp: datetime) -> Dict[str, any]:
        """Detect performance regressions compared to baseline."""
        if not results:
            return {"regressions_detected": 0, "details": []}
        
        # Calculate current metrics
        current_metrics = self._calculate_current_metrics(results)
        
        # Get baseline from knowledge base
        baseline = self._get_baseline_metrics()
        
        if not baseline:
            logger.warning("⚠️ No baseline found, creating new baseline")
            self._create_baseline(current_metrics, timestamp)
            return {"regressions_detected": 0, "details": [], "baseline_created": True}
        
        # Detect regressions
        regressions = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name in baseline:
                baseline_value = baseline[metric_name]
                
                if baseline_value > 0:
                    change_percentage = ((current_value - baseline_value) / baseline_value) * 100
                    
                    # Check for regression (negative change above threshold)
                    if change_percentage < -self.regression_threshold * 100:
                        regressions.append({
                            "metric": metric_name,
                            "baseline": baseline_value,
                            "current": current_value,
                            "change_percentage": change_percentage,
                            "severity": "high" if abs(change_percentage) > 20 else "medium"
                        })
        
        return {
            "regressions_detected": len(regressions),
            "details": regressions,
            "current_metrics": current_metrics,
            "baseline_metrics": baseline
        }
    
    def _calculate_current_metrics(self, results: List) -> Dict[str, float]:
        """Calculate current performance metrics from benchmark results."""
        if not results:
            return {}
        
        scores = [r.score for r in results]
        response_times = [r.response_time for r in results]
        price_coherence = [r.price_coherence for r in results]
        diversity_scores = [r.diversity_score for r in results]
        
        return {
            "avg_relevance_score": statistics.mean(scores),
            "avg_response_time": statistics.mean(response_times),
            "avg_price_coherence": statistics.mean(price_coherence),
            "avg_diversity_score": statistics.mean(diversity_scores),
            "price_filter_usage_rate": sum(1 for r in results if r.price_filter_applied) / len(results),
            "fallback_usage_rate": sum(1 for r in results if r.fallback_used) / len(results),
            "cache_hit_rate": sum(1 for r in results if r.cache_hit) / len(results)
        }
    
    def _get_baseline_metrics(self) -> Optional[Dict[str, float]]:
        """Get baseline metrics from knowledge base."""
        if not self.store_id:
            return None
        
        store_profile = self.knowledge_builder.get_store_profile(self.store_id)
        if not store_profile:
            return None
        
        return {
            "avg_relevance_score": store_profile.avg_relevance_score_baseline,
            "avg_response_time": store_profile.avg_response_time_baseline,
            "price_filter_usage_rate": store_profile.price_filter_usage_rate,
            "fallback_usage_rate": store_profile.fallback_usage_rate,
            "cache_hit_rate": store_profile.cache_hit_rate,
            "avg_price_coherence": store_profile.avg_price_coherence,
            "avg_diversity_score": store_profile.avg_diversity_score
        }
    
    def _create_baseline(self, current_metrics: Dict[str, float], timestamp: datetime):
        """Create new baseline from current metrics."""
        logger.info("📊 Creating new baseline from current metrics")
        
        # This will be handled by the knowledge base builder
        # when we process the benchmark results
        pass
    
    def _log_benchmark_results(self, results: List, regression_report: Dict, timestamp: datetime):
        """Log benchmark results and any regressions."""
        log_file = f"logs/benchmark_{timestamp.strftime('%Y%m%d')}.log"
        
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"BENCHMARK RUN: {timestamp.isoformat()}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Total queries: {len(results)}\n")
            
            if results:
                current_metrics = self._calculate_current_metrics(results)
                f.write(f"Current metrics:\n")
                for metric, value in current_metrics.items():
                    f.write(f"  {metric}: {value:.3f}\n")
            
            f.write(f"\nRegression report:\n")
            f.write(f"Regressions detected: {regression_report['regressions_detected']}\n")
            
            for regression in regression_report.get('details', []):
                f.write(f"  {regression['metric']}: {regression['change_percentage']:.1f}% "
                       f"({regression['severity']} severity)\n")
            
            f.write(f"\n")
        
        # If regressions detected, create alert
        if regression_report['regressions_detected'] > 0:
            self._create_regression_alert(regression_report, timestamp)
    
    def _create_regression_alert(self, regression_report: Dict, timestamp: datetime):
        """Create regression alert file."""
        alert_file = f"logs/regression_alert_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        alert_data = {
            "timestamp": timestamp.isoformat(),
            "store_id": self.store_id,
            "regressions_detected": regression_report['regressions_detected'],
            "details": regression_report['details'],
            "current_metrics": regression_report.get('current_metrics', {}),
            "baseline_metrics": regression_report.get('baseline_metrics', {}),
            "severity": "high" if any(r['severity'] == 'high' for r in regression_report['details']) else "medium"
        }
        
        with open(alert_file, 'w') as f:
            json.dump(alert_data, f, indent=2)
        
        logger.error(f"🚨 REGRESSION ALERT: {regression_report['regressions_detected']} regressions detected!")
        logger.error(f"Alert saved to: {alert_file}")
    
    def get_benchmark_history(self, days: int = 7) -> List[Dict]:
        """Get benchmark history for the last N days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as query_count,
                    AVG(score) as avg_score,
                    AVG(response_time) as avg_response_time,
                    AVG(price_coherence) as avg_price_coherence
                FROM benchmark_history 
                WHERE store_id = ? 
                AND timestamp >= DATE('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """.format(days), (self.store_id,))
            
            return [
                {
                    "date": row[0],
                    "query_count": row[1],
                    "avg_score": row[2],
                    "avg_response_time": row[3],
                    "avg_price_coherence": row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def generate_performance_report(self, days: int = 7) -> Dict[str, any]:
        """Generate comprehensive performance report."""
        history = self.get_benchmark_history(days)
        
        if not history:
            return {"message": "No benchmark history found"}
        
        # Calculate trends
        scores = [h['avg_score'] for h in history]
        response_times = [h['avg_response_time'] for h in history]
        
        score_trend = "improving" if scores[0] > scores[-1] else "declining" if scores[0] < scores[-1] else "stable"
        response_trend = "improving" if response_times[0] < response_times[-1] else "declining" if response_times[0] > response_times[-1] else "stable"
        
        return {
            "period_days": days,
            "total_benchmarks": len(history),
            "total_queries": sum(h['query_count'] for h in history),
            "current_avg_score": scores[0] if scores else 0,
            "current_avg_response_time": response_times[0] if response_times else 0,
            "score_trend": score_trend,
            "response_time_trend": response_trend,
            "history": history
        }

async def main():
    """Main function for continuous benchmarking."""
    parser = argparse.ArgumentParser(description="Continuous Benchmarking System")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--store-id", help="Store ID for tracking")
    parser.add_argument("--queries", default="benchmark_queries.csv", help="CSV file with test queries")
    parser.add_argument("--results", help="CSV file to save results")
    parser.add_argument("--regression-threshold", type=float, default=0.1, help="Regression threshold (default: 0.1 = 10%)")
    parser.add_argument("--report", action="store_true", help="Generate performance report")
    parser.add_argument("--days", type=int, default=7, help="Days for performance report")
    
    args = parser.parse_args()
    
    # Initialize continuous benchmarker
    benchmarker = ContinuousBenchmarker(
        base_url=args.base_url,
        store_id=args.store_id,
        regression_threshold=args.regression_threshold
    )
    
    if args.report:
        # Generate performance report
        report = benchmarker.generate_performance_report(args.days)
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"Period: Last {args.days} days")
        
        if "message" in report:
            print(f"Status: {report['message']}")
        else:
            print(f"Total benchmarks: {report.get('total_benchmarks', 0)}")
            print(f"Total queries: {report.get('total_queries', 0)}")
            print(f"Current avg score: {report.get('current_avg_score', 0):.3f}")
            print(f"Current avg response time: {report.get('current_avg_response_time', 0):.3f}s")
            print(f"Score trend: {report.get('score_trend', 'unknown')}")
            print(f"Response time trend: {report.get('response_time_trend', 'unknown')}")
            
            if report.get('history'):
                print(f"\n📈 HISTORY:")
                for entry in report['history'][:5]:  # Show last 5 days
                    print(f"  {entry['date']}: Score={entry['avg_score']:.3f}, "
                          f"Response={entry['avg_response_time']:.3f}s, "
                          f"Queries={entry['query_count']}")
        
        print("\n" + "="*60)
    else:
        # Run daily benchmark
        result = await benchmarker.run_daily_benchmark(
            queries_file=args.queries,
            results_file=args.results
        )
        
        print("\n" + "="*60)
        print("🚀 CONTINUOUS BENCHMARK COMPLETE")
        print("="*60)
        print(f"Timestamp: {result['timestamp']}")
        print(f"Total queries: {result['total_queries']}")
        print(f"Results file: {result['results_file']}")
        print(f"Regressions detected: {result['regression_report']['regressions_detected']}")
        
        if result['regression_report']['regressions_detected'] > 0:
            print(f"\n🚨 REGRESSIONS DETECTED:")
            for regression in result['regression_report']['details']:
                print(f"  {regression['metric']}: {regression['change_percentage']:.1f}% "
                      f"({regression['severity']} severity)")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main()) 