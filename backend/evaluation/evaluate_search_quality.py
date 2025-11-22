"""
Search Quality Evaluation Script

This script evaluates the quality of the search and RAG systems using
a curated test query set. It measures precision, recall, and answer quality.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import statistics

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.search_service import SearchService
from services.rag_service import RAGService
from services.query_parser import LegalQueryParser


class SearchQualityEvaluator:
    """Evaluates search and RAG quality using test query set"""

    def __init__(self):
        """Initialize evaluator with services"""
        self.search_service = SearchService()
        self.rag_service = RAGService()
        self.query_parser = LegalQueryParser()

        # Load test queries
        test_file = Path(__file__).parent / "BAITMAN_test_queries.json"
        with open(test_file, 'r') as f:
            data = json.load(f)
            self.test_queries = data['test_queries']

    def evaluate_search_precision_recall(self, k: int = 10) -> Dict:
        """
        Evaluate search precision and recall @ k

        Args:
            k: Number of results to consider (default: 10)

        Returns:
            Dict with precision, recall, and per-query results
        """
        results = []

        for test_case in self.test_queries:
            query = test_case['query']
            expected_doc_ids = [doc['id'] for doc in test_case.get('expected_documents', [])]

            if not expected_doc_ids:
                continue  # Skip queries without expected documents

            try:
                # Perform hybrid search
                search_result = self.search_service.hybrid_search(
                    query=query,
                    size=k
                )

                # Extract returned document IDs
                returned_doc_ids = [
                    hit['id'] for hit in search_result.get('hits', [])
                ][:k]

                # Calculate precision and recall
                relevant_retrieved = set(expected_doc_ids) & set(returned_doc_ids)

                precision = len(relevant_retrieved) / k if k > 0 else 0
                recall = len(relevant_retrieved) / len(expected_doc_ids) if expected_doc_ids else 0

                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'precision': precision,
                    'recall': recall,
                    'expected_docs': expected_doc_ids,
                    'returned_docs': returned_doc_ids,
                    'relevant_retrieved': list(relevant_retrieved)
                })

            except Exception as e:
                print(f"Error evaluating query {test_case['id']}: {e}")
                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'error': str(e)
                })

        # Calculate aggregate metrics
        precisions = [r['precision'] for r in results if 'precision' in r]
        recalls = [r['recall'] for r in results if 'recall' in r]

        return {
            'k': k,
            'num_queries': len(results),
            'avg_precision': statistics.mean(precisions) if precisions else 0,
            'avg_recall': statistics.mean(recalls) if recalls else 0,
            'median_precision': statistics.median(precisions) if precisions else 0,
            'median_recall': statistics.median(recalls) if recalls else 0,
            'per_query_results': results
        }

    def evaluate_entity_extraction_accuracy(self) -> Dict:
        """
        Evaluate NLP entity extraction accuracy

        Returns:
            Dict with accuracy metrics
        """
        results = []

        for test_case in self.test_queries:
            query = test_case['query']
            expected_entities = test_case.get('expected_entities', {})

            if not expected_entities:
                continue

            try:
                # Parse query and extract entities
                parsed = self.query_parser.parse_query(query)

                # Check each expected entity type
                correct = 0
                total = 0

                for entity_type, expected_values in expected_entities.items():
                    total += len(expected_values)

                    # Get extracted entities of this type
                    extracted_entities = [
                        e for e in parsed.entities
                        if e.entity_type.value == entity_type
                    ]

                    extracted_values = [e.normalized for e in extracted_entities]

                    # Count matches
                    for expected_val in expected_values:
                        if expected_val in extracted_values:
                            correct += 1

                accuracy = correct / total if total > 0 else 0

                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'accuracy': accuracy,
                    'correct': correct,
                    'total': total,
                    'expected_entities': expected_entities,
                    'extracted_entities': [e.to_dict() for e in parsed.entities]
                })

            except Exception as e:
                print(f"Error extracting entities for {test_case['id']}: {e}")
                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'error': str(e)
                })

        # Calculate aggregate metrics
        accuracies = [r['accuracy'] for r in results if 'accuracy' in r]

        return {
            'num_queries': len(results),
            'avg_accuracy': statistics.mean(accuracies) if accuracies else 0,
            'median_accuracy': statistics.median(accuracies) if accuracies else 0,
            'per_query_results': results
        }

    def evaluate_intent_classification_accuracy(self) -> Dict:
        """
        Evaluate intent classification accuracy

        Returns:
            Dict with accuracy metrics
        """
        results = []

        for test_case in self.test_queries:
            query = test_case['query']
            expected_intent = test_case.get('expected_intent')

            if not expected_intent:
                continue

            try:
                # Parse query and classify intent
                parsed = self.query_parser.parse_query(query)
                predicted_intent = parsed.intent.value

                # Check if correct
                correct = (predicted_intent == expected_intent)

                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'expected_intent': expected_intent,
                    'predicted_intent': predicted_intent,
                    'correct': correct,
                    'confidence': parsed.intent_confidence
                })

            except Exception as e:
                print(f"Error classifying intent for {test_case['id']}: {e}")
                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'error': str(e)
                })

        # Calculate aggregate metrics
        correct_count = sum(1 for r in results if r.get('correct'))
        total_count = len([r for r in results if 'correct' in r])

        return {
            'num_queries': total_count,
            'accuracy': correct_count / total_count if total_count > 0 else 0,
            'correct': correct_count,
            'total': total_count,
            'per_query_results': results
        }

    def evaluate_rag_answer_quality(self, num_samples: int = 10) -> Dict:
        """
        Evaluate RAG answer quality

        Args:
            num_samples: Number of queries to sample for RAG evaluation

        Returns:
            Dict with answer quality metrics
        """
        results = []

        # Sample queries for RAG evaluation (can be expensive)
        sample_queries = self.test_queries[:num_samples]

        for test_case in sample_queries:
            query = test_case['query']
            expected_contains = test_case.get('expected_answer_contains', [])

            try:
                # Generate answer using RAG
                answer = self.rag_service.answer_question(
                    question=query,
                    num_context_docs=5,
                    use_cache=False  # Don't use cache for evaluation
                )

                # Check if expected phrases are in answer
                contains_count = 0
                for phrase in expected_contains:
                    if phrase.lower() in answer.answer.lower():
                        contains_count += 1

                coverage = contains_count / len(expected_contains) if expected_contains else 0

                # Check citation quality
                has_citations = len(answer.citations) > 0

                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'answer': answer.answer,
                    'coverage': coverage,
                    'expected_phrases': expected_contains,
                    'found_phrases': contains_count,
                    'has_citations': has_citations,
                    'num_citations': len(answer.citations),
                    'confidence_score': answer.confidence_score,
                    'processing_time_ms': answer.processing_time_ms
                })

            except Exception as e:
                print(f"Error generating answer for {test_case['id']}: {e}")
                results.append({
                    'query_id': test_case['id'],
                    'query': query,
                    'error': str(e)
                })

        # Calculate aggregate metrics
        coverages = [r['coverage'] for r in results if 'coverage' in r]
        confidences = [r['confidence_score'] for r in results if 'confidence_score' in r]
        processing_times = [r['processing_time_ms'] for r in results if 'processing_time_ms' in r]
        citation_counts = [r['num_citations'] for r in results if 'num_citations' in r]

        return {
            'num_queries': len(results),
            'avg_coverage': statistics.mean(coverages) if coverages else 0,
            'avg_confidence': statistics.mean(confidences) if confidences else 0,
            'avg_processing_time_ms': statistics.mean(processing_times) if processing_times else 0,
            'avg_citations': statistics.mean(citation_counts) if citation_counts else 0,
            'per_query_results': results
        }

    def run_full_evaluation(self, save_results: bool = True) -> Dict:
        """
        Run full evaluation suite

        Args:
            save_results: Whether to save results to file

        Returns:
            Dict with all evaluation results
        """
        print("=" * 80)
        print("SEARCH AND RAG QUALITY EVALUATION")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"Total test queries: {len(self.test_queries)}")
        print()

        # Run evaluations
        print("1. Evaluating search precision and recall...")
        search_results = self.evaluate_search_precision_recall(k=10)
        print(f"   Precision@10: {search_results['avg_precision']:.2%}")
        print(f"   Recall@10: {search_results['avg_recall']:.2%}")
        print()

        print("2. Evaluating entity extraction accuracy...")
        entity_results = self.evaluate_entity_extraction_accuracy()
        print(f"   Accuracy: {entity_results['avg_accuracy']:.2%}")
        print()

        print("3. Evaluating intent classification accuracy...")
        intent_results = self.evaluate_intent_classification_accuracy()
        print(f"   Accuracy: {intent_results['accuracy']:.2%}")
        print()

        print("4. Evaluating RAG answer quality (10 samples)...")
        rag_results = self.evaluate_rag_answer_quality(num_samples=10)
        print(f"   Average coverage: {rag_results['avg_coverage']:.2%}")
        print(f"   Average confidence: {rag_results['avg_confidence']:.2f}")
        print(f"   Average citations: {rag_results['avg_citations']:.1f}")
        print(f"   Average time: {rag_results['avg_processing_time_ms']:.0f}ms")
        print()

        # Compile full results
        full_results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'num_test_queries': len(self.test_queries)
            },
            'search_precision_recall': search_results,
            'entity_extraction': entity_results,
            'intent_classification': intent_results,
            'rag_answer_quality': rag_results
        }

        # Save results
        if save_results:
            output_file = Path(__file__).parent / f"BAITMAN_evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(full_results, f, indent=2)
            print(f"Results saved to: {output_file}")

        print("=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)

        return full_results


def main():
    """Run evaluation"""
    try:
        evaluator = SearchQualityEvaluator()
        results = evaluator.run_full_evaluation(save_results=True)

        # Print summary
        print("\nSUMMARY:")
        print(f"  Search Precision@10: {results['search_precision_recall']['avg_precision']:.2%}")
        print(f"  Search Recall@10: {results['search_precision_recall']['avg_recall']:.2%}")
        print(f"  Entity Extraction: {results['entity_extraction']['avg_accuracy']:.2%}")
        print(f"  Intent Classification: {results['intent_classification']['accuracy']:.2%}")
        print(f"  RAG Answer Coverage: {results['rag_answer_quality']['avg_coverage']:.2%}")
        print(f"  RAG Confidence: {results['rag_answer_quality']['avg_confidence']:.2f}")

    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
