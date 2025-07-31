#!/usr/bin/env python3
"""
Search Quality Benchmark Script

This script automatically tests search quality by:
1. Reading test queries from benchmark_queries.csv
2. Executing searches against the FastAPI /api/ai-search endpoint
3. Scoring results using GPT-4o-mini for relevance assessment
4. Generating benchmark_results.csv with detailed metrics
5. Providing console output with performance summary

Usage:
    python benchmark_search.py [--headless] [--endpoint /api/ai-search]
"""

import asyncio
import csv
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import argparse
import aiohttp
import openai
from pathlib import Path
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result with metadata."""
    title: str
    price: float
    similarity: float
    tags: List[str]
    
    def __str__(self) -> str:
        return f"{self.title} (€{self.price:.2f}, sim: {self.similarity:.3f})"

@dataclass
class BenchmarkResult:
    """Represents benchmark result for a single query."""
    query: str
    score: float
    avg_price_top5: float
    titles_top5: str
    response_time: float
    result_count: int
    price_filter_applied: bool
    fallback_used: bool
    gpt_reasoning: str

class SearchBenchmarker:
    """Main benchmark class for testing search quality."""
    
    def __init__(self, base_url: str = "http://localhost:8000", headless: bool = False):
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize OpenAI client
        try:
            openai.api_key = self._get_openai_key()
            self.openai_client = openai.AsyncOpenAI()
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            raise
    
    def _get_openai_key(self) -> str:
        """Get OpenAI API key from environment or config."""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Try to read from config file
            config_file = Path('ai_shopify_search/config.py')
            if config_file.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_file)
                config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config)
                api_key = getattr(config, 'OPENAI_API_KEY', None)
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or config")
        
        return api_key
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def execute_search(self, query: str, endpoint: str = "/api/ai-search", limit: int = 25) -> Dict[str, Any]:
        """
        Execute a single search query.
        
        Args:
            query: Search query string
            endpoint: API endpoint to test
            limit: Number of results to request
            
        Returns:
            Dictionary with search response data
        """
        url = f"{self.base_url}{endpoint}"
        params = {
            "query": query,
            "limit": limit,
            "page": 1
        }
        
        start_time = time.time()
        
        try:
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                
                if response.status != 200:
                    logger.error(f"❌ Search failed for query '{query}': HTTP {response.status}")
                    return {
                        "error": f"HTTP {response.status}",
                        "response_time": response_time,
                        "results": []
                    }
                
                data = await response.json()
                
                if not self.headless:
                    logger.info(f"🔍 Query: '{query}' → {len(data.get('results', []))} results in {response_time:.3f}s")
                
                return {
                    "response_time": response_time,
                    "results": data.get('results', []),
                    "price_filter": data.get('price_filter', {}),
                    "search_suggestions": data.get('search_suggestions'),
                    "facets": data.get('facets', {}),
                    "count": data.get('count', 0)
                }
                
        except Exception as e:
            logger.error(f"❌ Search error for query '{query}': {e}")
            return {
                "error": str(e),
                "response_time": time.time() - start_time,
                "results": []
            }
    
    def parse_search_results(self, results: List[Dict[str, Any]]) -> List[SearchResult]:
        """
        Parse search results into SearchResult objects.
        
        Args:
            results: Raw search results from API
            
        Returns:
            List of SearchResult objects
        """
        parsed_results = []
        
        for result in results:
            try:
                parsed_results.append(SearchResult(
                    title=result.get('title', 'Unknown'),
                    price=float(result.get('price', 0)),
                    similarity=float(result.get('similarity', 0)),
                    tags=result.get('tags', [])
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Failed to parse result: {e}")
                continue
        
        return parsed_results
    
    async def score_relevance_with_gpt(self, query: str, top_results: List[SearchResult]) -> Tuple[float, str]:
        """
        Score search relevance using GPT-4o-mini.
        
        Args:
            query: Original search query
            top_results: Top 5 search results
            
        Returns:
            Tuple of (score, reasoning)
        """
        if not top_results:
            return 0.0, "No results to score"
        
        # Prepare results for GPT
        results_text = "\n".join([
            f"{i+1}. {result.title} (€{result.price:.2f}, similarity: {result.similarity:.3f})"
            for i, result in enumerate(top_results[:5])
        ])
        
        prompt = f"""
Je bent een expert in e-commerce search kwaliteit. Beoordeel hoe goed de zoekresultaten matchen met de intentie van de gebruiker.

QUERY: "{query}"

TOP 5 RESULTATEN:
{results_text}

BEOORDELING:
- Score van 0.0 tot 1.0 (1.0 = perfecte match)
- Overweeg: relevantie, prijs, product type, kwaliteit van resultaten
- Geef een korte uitleg van je score

Antwoord in JSON formaat:
{{
    "score": 0.85,
    "reasoning": "De resultaten matchen goed met de query. Alle producten zijn schoenen, prijzen zijn redelijk, en de similarity scores zijn hoog."
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(content)
                score = float(result.get('score', 0.0))
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Validate score range
                score = max(0.0, min(1.0, score))
                
                return score, reasoning
                
            except json.JSONDecodeError:
                # Fallback: try to extract score from text
                import re
                score_match = re.search(r'["\']?score["\']?\s*:\s*([0-9]*\.?[0-9]+)', content)
                if score_match:
                    score = float(score_match.group(1))
                    score = max(0.0, min(1.0, score))
                    return score, content
                else:
                    logger.warning(f"⚠️ Could not parse GPT response: {content}")
                    return 0.5, "Failed to parse GPT response"
                    
        except Exception as e:
            logger.error(f"❌ GPT scoring failed: {e}")
            return 0.5, f"GPT error: {e}"
    
    def calculate_metrics(self, results: List[SearchResult]) -> Dict[str, float]:
        """
        Calculate additional metrics for the results.
        
        Args:
            results: List of search results
            
        Returns:
            Dictionary with calculated metrics
        """
        if not results:
            return {
                "avg_price_top5": 0.0,
                "avg_similarity_top5": 0.0,
                "price_range": 0.0
            }
        
        top5 = results[:5]
        prices = [r.price for r in top5]
        similarities = [r.similarity for r in top5]
        
        return {
            "avg_price_top5": statistics.mean(prices),
            "avg_similarity_top5": statistics.mean(similarities),
            "price_range": max(prices) - min(prices) if len(prices) > 1 else 0.0
        }
    
    async def benchmark_query(self, query: str, endpoint: str = "/api/ai-search") -> BenchmarkResult:
        """
        Execute full benchmark for a single query.
        
        Args:
            query: Search query to test
            endpoint: API endpoint to test
            
        Returns:
            BenchmarkResult with all metrics
        """
        # Execute search
        search_response = await self.execute_search(query, endpoint)
        
        if "error" in search_response:
            return BenchmarkResult(
                query=query,
                score=0.0,
                avg_price_top5=0.0,
                titles_top5="",
                response_time=search_response["response_time"],
                result_count=0,
                price_filter_applied=False,
                fallback_used=False,
                gpt_reasoning=f"Search failed: {search_response['error']}"
            )
        
        # Parse results
        results = self.parse_search_results(search_response["results"])
        
        # Score with GPT
        score, reasoning = await self.score_relevance_with_gpt(query, results)
        
        # Calculate metrics
        metrics = self.calculate_metrics(results)
        
        # Prepare titles string
        titles_top5 = " | ".join([r.title for r in results[:5]])
        
        # Extract price filter info
        price_filter = search_response.get("price_filter", {})
        
        return BenchmarkResult(
            query=query,
            score=score,
            avg_price_top5=metrics["avg_price_top5"],
            titles_top5=titles_top5,
            response_time=search_response["response_time"],
            result_count=len(results),
            price_filter_applied=price_filter.get("applied", False),
            fallback_used=price_filter.get("fallback_used", False),
            gpt_reasoning=reasoning
        )
    
    async def run_benchmark(self, queries_file: str = "benchmark_queries.csv", 
                          results_file: str = "benchmark_results.csv",
                          endpoint: str = "/api/ai-search") -> List[BenchmarkResult]:
        """
        Run full benchmark on all queries.
        
        Args:
            queries_file: CSV file with test queries
            results_file: CSV file to save results
            endpoint: API endpoint to test
            
        Returns:
            List of all benchmark results
        """
        # Read queries
        queries = self._read_queries(queries_file)
        if not queries:
            logger.error(f"❌ No queries found in {queries_file}")
            return []
        
        logger.info(f"🚀 Starting benchmark with {len(queries)} queries against {endpoint}")
        
        # Execute benchmarks
        results = []
        for i, query in enumerate(queries, 1):
            if not self.headless:
                logger.info(f"📊 Progress: {i}/{len(queries)} - Testing: '{query}'")
            
            result = await self.benchmark_query(query, endpoint)
            results.append(result)
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)
        
        # Save results
        self._save_results(results, results_file)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _read_queries(self, filename: str) -> List[str]:
        """Read queries from CSV file."""
        queries = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    query = row.get('query', '').strip()
                    if query:
                        queries.append(query)
            
            logger.info(f"📖 Loaded {len(queries)} queries from {filename}")
            
        except FileNotFoundError:
            logger.error(f"❌ Query file not found: {filename}")
        except Exception as e:
            logger.error(f"❌ Error reading queries: {e}")
        
        return queries
    
    def _save_results(self, results: List[BenchmarkResult], filename: str):
        """Save benchmark results to CSV file."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'query', 'score', 'avg_price_top5', 'titles_top5', 
                    'response_time', 'result_count', 'price_filter_applied',
                    'fallback_used', 'gpt_reasoning'
                ])
                
                # Write results
                for result in results:
                    writer.writerow([
                        result.query,
                        f"{result.score:.3f}",
                        f"{result.avg_price_top5:.2f}",
                        result.titles_top5,
                        f"{result.response_time:.3f}",
                        result.result_count,
                        result.price_filter_applied,
                        result.fallback_used,
                        result.gpt_reasoning
                    ])
            
            logger.info(f"💾 Saved {len(results)} results to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
    
    def _print_summary(self, results: List[BenchmarkResult]):
        """Print benchmark summary."""
        if not results:
            return
        
        # Calculate statistics
        scores = [r.score for r in results]
        response_times = [r.response_time for r in results]
        
        avg_score = statistics.mean(scores)
        avg_response_time = statistics.mean(response_times)
        
        # Find worst performing queries
        worst_queries = sorted(results, key=lambda x: x.score)[:5]
        
        # Print summary
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total queries tested: {len(results)}")
        print(f"Average relevance score: {avg_score:.3f}")
        print(f"Average response time: {avg_response_time:.3f}s")
        print(f"Price filter applied: {sum(1 for r in results if r.price_filter_applied)}/{len(results)}")
        print(f"Fallback used: {sum(1 for r in results if r.fallback_used)}/{len(results)}")
        
        print(f"\n🔴 TOP 5 WORST PERFORMING QUERIES:")
        for i, result in enumerate(worst_queries, 1):
            print(f"{i}. '{result.query}' - Score: {result.score:.3f}")
            print(f"   Reasoning: {result.gpt_reasoning[:100]}...")
        
        print("\n" + "="*60)

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Search Quality Benchmark Tool")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no console output)")
    parser.add_argument("--endpoint", default="/api/ai-search", help="API endpoint to test")
    parser.add_argument("--queries", default="benchmark_queries.csv", help="CSV file with test queries")
    parser.add_argument("--results", default="benchmark_results.csv", help="CSV file to save results")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    
    args = parser.parse_args()
    
    # Create benchmarker
    async with SearchBenchmarker(base_url=args.base_url, headless=args.headless) as benchmarker:
        await benchmarker.run_benchmark(
            queries_file=args.queries,
            results_file=args.results,
            endpoint=args.endpoint
        )

if __name__ == "__main__":
    asyncio.run(main()) 