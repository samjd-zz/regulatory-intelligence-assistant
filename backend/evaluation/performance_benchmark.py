"""
Performance Benchmarking Tool

Comprehensive performance testing for all services in the
Regulatory Intelligence Assistant.

Measures and reports:
- NLP processing latency
- Search response times (keyword, vector, hybrid)
- RAG answer generation time
- Cache performance
- Throughput under load

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import sys
import time
import statistics
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.query_parser import LegalQueryParser
from services.search_service import SearchService
from services.rag_service import RAGService


@dataclass
class BenchmarkResult:
    """Result of a single benchmark"""
    name: str
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    target_ms: float
    passed: bool


class PerformanceBenchmark:
    """Performance benchmarking suite"""

    def __init__(self):
        """Initialize benchmark suite"""
        self.query_parser = LegalQueryParser()
        self.search_service = SearchService()
        self.rag_service = RAGService()

        # Test queries for benchmarking
        self.test_queries = [
            "Can permanent residents apply for employment insurance?",
            "What is the Canada Pension Plan?",
            "How do I apply for Old Age Security?",
            "Who is eligible for the Canada Child Benefit?",
            "What are workers compensation regulations in BC?",
            "Federal regulations about employment standards",
            "Citizenship application processing times",
            "Disability benefits eligibility requirements",
            "Social assistance programs for refugees",
            "Difference between CPP and OAS"
        ]

    def measure_latency(self, func, *args, **kwargs) -> float:
        """Measure function latency in milliseconds"""
        start = time.time()
        func(*args, **kwargs)
        return (time.time() - start) * 1000

    def run_benchmark(
        self,
        name: str,
        func,
        iterations: int,
        target_ms: float,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run a benchmark test

        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            target_ms: Target latency in milliseconds
            *args, **kwargs: Arguments to pass to function

        Returns:
            BenchmarkResult with statistics
        """
        print(f"\n{name}")
        print(f"  Running {iterations} iterations...", end="", flush=True)

        latencies = []

        for i in range(iterations):
            latency_ms = self.measure_latency(func, *args, **kwargs)
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                print(".", end="", flush=True)

        print(" Done!")

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        p95_index = int(0.95 * len(latencies_sorted))
        p99_index = int(0.99 * len(latencies_sorted))

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            min_ms=min(latencies),
            max_ms=max(latencies),
            mean_ms=statistics.mean(latencies),
            median_ms=statistics.median(latencies),
            p95_ms=latencies_sorted[p95_index] if p95_index < len(latencies_sorted) else latencies_sorted[-1],
            p99_ms=latencies_sorted[p99_index] if p99_index < len(latencies_sorted) else latencies_sorted[-1],
            std_dev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0,
            target_ms=target_ms,
            passed=(statistics.mean(latencies) < target_ms)
        )

        # Print results
        self.print_result(result)

        return result

    def print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        status = "✅ PASS" if result.passed else "❌ FAIL"

        print(f"  Results:")
        print(f"    Min:        {result.min_ms:8.2f} ms")
        print(f"    Mean:       {result.mean_ms:8.2f} ms")
        print(f"    Median:     {result.median_ms:8.2f} ms")
        print(f"    P95:        {result.p95_ms:8.2f} ms")
        print(f"    P99:        {result.p99_ms:8.2f} ms")
        print(f"    Max:        {result.max_ms:8.2f} ms")
        print(f"    Std Dev:    {result.std_dev_ms:8.2f} ms")
        print(f"    Target:     {result.target_ms:8.2f} ms")
        print(f"    Status:     {status}")

    # NLP Benchmarks

    def benchmark_nlp_query_parsing(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark NLP query parsing"""
        return self.run_benchmark(
            name="NLP - Query Parsing",
            func=self.query_parser.parse_query,
            iterations=iterations,
            target_ms=100.0,  # Target from design.md
            query=self.test_queries[0]
        )

    def benchmark_nlp_entity_extraction(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark entity extraction"""
        from services.legal_nlp import LegalEntityExtractor
        extractor = LegalEntityExtractor()

        return self.run_benchmark(
            name="NLP - Entity Extraction",
            func=extractor.extract_entities,
            iterations=iterations,
            target_ms=50.0,
            text=self.test_queries[0]
        )

    # Search Benchmarks

    def benchmark_search_keyword(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark keyword search"""
        return self.run_benchmark(
            name="Search - Keyword (BM25)",
            func=self.search_service.keyword_search,
            iterations=iterations,
            target_ms=100.0,  # Target from docs
            query="employment insurance eligibility",
            size=10
        )

    def benchmark_search_vector(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark vector search"""
        return self.run_benchmark(
            name="Search - Vector (Semantic)",
            func=self.search_service.vector_search,
            iterations=iterations,
            target_ms=400.0,  # Target from docs
            query="retirement benefits for elderly",
            size=10
        )

    def benchmark_search_hybrid(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark hybrid search"""
        return self.run_benchmark(
            name="Search - Hybrid (BM25 + Vector)",
            func=self.search_service.hybrid_search,
            iterations=iterations,
            target_ms=500.0,  # Target from docs
            query="Canada pension plan eligibility",
            size=10
        )

    # RAG Benchmarks

    def benchmark_rag_answer_generation(self, iterations: int = 10) -> BenchmarkResult:
        """Benchmark RAG answer generation (expensive)"""
        return self.run_benchmark(
            name="RAG - Answer Generation (Gemini API)",
            func=self.rag_service.answer_question,
            iterations=iterations,
            target_ms=5000.0,  # 5 seconds target from prd.md
            question=self.test_queries[0],
            num_context_docs=5,
            use_cache=False
        )

    def benchmark_rag_cached_answer(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark cached answer retrieval"""
        # Prime cache
        question = "What is the guaranteed income supplement?"
        self.rag_service.answer_question(question, use_cache=True)

        return self.run_benchmark(
            name="RAG - Cached Answer Retrieval",
            func=self.rag_service.answer_question,
            iterations=iterations,
            target_ms=100.0,  # Should be very fast
            question=question,
            use_cache=True
        )

    # Throughput Benchmarks

    def benchmark_throughput_nlp(self, duration_seconds: int = 10) -> Dict:
        """Measure NLP throughput (queries/second)"""
        print(f"\nNLP - Throughput Test ({duration_seconds}s)")
        print(f"  Processing queries...", end="", flush=True)

        start_time = time.time()
        query_count = 0

        while (time.time() - start_time) < duration_seconds:
            query = self.test_queries[query_count % len(self.test_queries)]
            self.query_parser.parse_query(query)
            query_count += 1

            if query_count % 100 == 0:
                print(".", end="", flush=True)

        elapsed = time.time() - start_time
        qps = query_count / elapsed

        print(f" Done!")
        print(f"  Total Queries:  {query_count}")
        print(f"  Elapsed Time:   {elapsed:.2f}s")
        print(f"  Throughput:     {qps:.1f} queries/second")

        return {
            'test': 'NLP Throughput',
            'duration_s': elapsed,
            'total_queries': query_count,
            'qps': qps
        }

    def benchmark_throughput_search(self, duration_seconds: int = 10) -> Dict:
        """Measure search throughput (queries/second)"""
        print(f"\nSearch - Throughput Test ({duration_seconds}s)")
        print(f"  Executing searches...", end="", flush=True)

        start_time = time.time()
        query_count = 0

        while (time.time() - start_time) < duration_seconds:
            query = self.test_queries[query_count % len(self.test_queries)]
            self.search_service.hybrid_search(query, size=10)
            query_count += 1

            if query_count % 10 == 0:
                print(".", end="", flush=True)

        elapsed = time.time() - start_time
        qps = query_count / elapsed

        print(f" Done!")
        print(f"  Total Queries:  {query_count}")
        print(f"  Elapsed Time:   {elapsed:.2f}s")
        print(f"  Throughput:     {qps:.1f} queries/second")

        return {
            'test': 'Search Throughput',
            'duration_s': elapsed,
            'total_queries': query_count,
            'qps': qps
        }

    # Full Benchmark Suite

    def run_full_benchmark(self, save_results: bool = True) -> Dict:
        """
        Run complete benchmark suite

        Args:
            save_results: Whether to save results to file

        Returns:
            Dict with all benchmark results
        """
        print("=" * 80)
        print("PERFORMANCE BENCHMARK SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print()

        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'target_metrics': {
                    'nlp_processing': '<100ms',
                    'keyword_search': '<100ms',
                    'vector_search': '<400ms',
                    'hybrid_search': '<500ms',
                    'rag_generation': '<5000ms (p95)',
                    'cached_retrieval': '<100ms'
                }
            },
            'latency_benchmarks': [],
            'throughput_benchmarks': []
        }

        # === LATENCY BENCHMARKS ===
        print("\n" + "=" * 80)
        print("LATENCY BENCHMARKS")
        print("=" * 80)

        # NLP
        results['latency_benchmarks'].append(
            self.benchmark_nlp_query_parsing(iterations=100)
        )
        results['latency_benchmarks'].append(
            self.benchmark_nlp_entity_extraction(iterations=100)
        )

        # Search
        results['latency_benchmarks'].append(
            self.benchmark_search_keyword(iterations=50)
        )
        results['latency_benchmarks'].append(
            self.benchmark_search_vector(iterations=50)
        )
        results['latency_benchmarks'].append(
            self.benchmark_search_hybrid(iterations=50)
        )

        # RAG (if Gemini available)
        if self.rag_service.gemini_client.is_available():
            results['latency_benchmarks'].append(
                self.benchmark_rag_answer_generation(iterations=10)
            )
        else:
            print("\n⚠️  Skipping RAG benchmarks (Gemini API not available)")

        results['latency_benchmarks'].append(
            self.benchmark_rag_cached_answer(iterations=100)
        )

        # === THROUGHPUT BENCHMARKS ===
        print("\n" + "=" * 80)
        print("THROUGHPUT BENCHMARKS")
        print("=" * 80)

        results['throughput_benchmarks'].append(
            self.benchmark_throughput_nlp(duration_seconds=10)
        )
        results['throughput_benchmarks'].append(
            self.benchmark_throughput_search(duration_seconds=10)
        )

        # === SUMMARY ===
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in results['latency_benchmarks'] if r.passed)
        total = len(results['latency_benchmarks'])

        print(f"\nLatency Benchmarks: {passed}/{total} passed")
        print("\nResults:")

        for result in results['latency_benchmarks']:
            status = "✅" if result.passed else "❌"
            print(f"  {status} {result.name:40s} P95: {result.p95_ms:7.1f}ms (target: {result.target_ms:.0f}ms)")

        print("\nThroughput Benchmarks:")
        for result in results['throughput_benchmarks']:
            print(f"  • {result['test']:40s} {result['qps']:6.1f} qps")

        # Save results
        if save_results:
            output_file = Path(__file__).parent / f"BAITMAN_benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Convert dataclasses to dict
            results_serializable = {
                'metadata': results['metadata'],
                'latency_benchmarks': [
                    {
                        'name': r.name,
                        'iterations': r.iterations,
                        'min_ms': r.min_ms,
                        'max_ms': r.max_ms,
                        'mean_ms': r.mean_ms,
                        'median_ms': r.median_ms,
                        'p95_ms': r.p95_ms,
                        'p99_ms': r.p99_ms,
                        'std_dev_ms': r.std_dev_ms,
                        'target_ms': r.target_ms,
                        'passed': r.passed
                    }
                    for r in results['latency_benchmarks']
                ],
                'throughput_benchmarks': results['throughput_benchmarks']
            }

            with open(output_file, 'w') as f:
                json.dump(results_serializable, f, indent=2)

            print(f"\nResults saved to: {output_file}")

        print("\n" + "=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)

        return results


def main():
    """Run benchmark suite"""
    try:
        benchmark = PerformanceBenchmark()
        results = benchmark.run_full_benchmark(save_results=True)

        # Exit with error code if any tests failed
        failed = sum(1 for r in results['latency_benchmarks'] if not r.passed)
        if failed > 0:
            print(f"\n⚠️  {failed} benchmark(s) failed")
            sys.exit(1)

    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
