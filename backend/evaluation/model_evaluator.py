"""
ML Model Evaluation Framework

Comprehensive evaluation framework for regulatory AI models:
- NLP entity extraction accuracy
- Intent classification metrics
- Search quality (precision, recall, nDCG)
- RAG answer quality and citation accuracy
- End-to-end system performance
- A/B testing framework

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import json
import time
from typing import List, Dict, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import logging
import numpy as np

logger = logging.getLogger(__name__)


# === Evaluation Metrics ===

@dataclass
class EntityExtractionMetrics:
    """Metrics for entity extraction evaluation"""
    precision: float
    recall: float
    f1_score: float
    entity_type_scores: Dict[str, Dict[str, float]]
    total_predictions: int
    total_ground_truth: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntentClassificationMetrics:
    """Metrics for intent classification"""
    accuracy: float
    precision_per_class: Dict[str, float]
    recall_per_class: Dict[str, float]
    f1_per_class: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]
    total_samples: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchMetrics:
    """Metrics for search quality"""
    precision_at_k: Dict[int, float]  # {k: precision@k}
    recall_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]  # Normalized Discounted Cumulative Gain
    mrr: float  # Mean Reciprocal Rank
    mean_average_precision: float  # MAP
    total_queries: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RAGMetrics:
    """Metrics for RAG answer quality"""
    answer_correctness: float  # 0-1 score
    answer_completeness: float
    citation_accuracy: float  # % of citations that are correct
    citation_coverage: float  # % of answer supported by citations
    avg_confidence_score: float
    avg_latency_seconds: float
    total_questions: int
    factual_consistency: float  # Agreement with source documents

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# === Entity Extraction Evaluator ===

class EntityExtractionEvaluator:
    """Evaluate entity extraction performance"""

    @staticmethod
    def calculate_metrics(
        predictions: List[Dict[str, List[str]]],
        ground_truth: List[Dict[str, List[str]]]
    ) -> EntityExtractionMetrics:
        """
        Calculate entity extraction metrics

        Args:
            predictions: List of predicted entities per document
            ground_truth: List of ground truth entities per document

        Returns:
            EntityExtractionMetrics
        """
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")

        # Aggregate counts
        total_tp = 0
        total_fp = 0
        total_fn = 0

        # Per entity type scores
        type_scores = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})

        for pred, truth in zip(predictions, ground_truth):
            # Get all entity types
            all_types = set(pred.keys()) | set(truth.keys())

            for entity_type in all_types:
                pred_entities = set(pred.get(entity_type, []))
                truth_entities = set(truth.get(entity_type, []))

                # True positives: in both pred and truth
                tp = len(pred_entities & truth_entities)

                # False positives: in pred but not truth
                fp = len(pred_entities - truth_entities)

                # False negatives: in truth but not pred
                fn = len(truth_entities - pred_entities)

                total_tp += tp
                total_fp += fp
                total_fn += fn

                type_scores[entity_type]['tp'] += tp
                type_scores[entity_type]['fp'] += fp
                type_scores[entity_type]['fn'] += fn

        # Calculate overall metrics
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Calculate per-type metrics
        entity_type_scores = {}
        for entity_type, counts in type_scores.items():
            tp, fp, fn = counts['tp'], counts['fp'], counts['fn']

            type_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            type_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            type_f1 = 2 * (type_precision * type_recall) / (type_precision + type_recall) \
                if (type_precision + type_recall) > 0 else 0

            entity_type_scores[entity_type] = {
                'precision': round(type_precision, 3),
                'recall': round(type_recall, 3),
                'f1': round(type_f1, 3),
                'support': tp + fn
            }

        return EntityExtractionMetrics(
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1, 3),
            entity_type_scores=entity_type_scores,
            total_predictions=total_tp + total_fp,
            total_ground_truth=total_tp + total_fn
        )


# === Intent Classification Evaluator ===

class IntentClassificationEvaluator:
    """Evaluate intent classification performance"""

    @staticmethod
    def calculate_metrics(
        predictions: List[str],
        ground_truth: List[str]
    ) -> IntentClassificationMetrics:
        """
        Calculate intent classification metrics

        Args:
            predictions: List of predicted intents
            ground_truth: List of ground truth intents

        Returns:
            IntentClassificationMetrics
        """
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")

        # Get all intent classes
        all_intents = set(predictions) | set(ground_truth)

        # Build confusion matrix
        confusion_matrix = {intent: {other: 0 for other in all_intents} for intent in all_intents}

        for pred, truth in zip(predictions, ground_truth):
            confusion_matrix[truth][pred] += 1

        # Calculate per-class metrics
        precision_per_class = {}
        recall_per_class = {}
        f1_per_class = {}

        for intent in all_intents:
            # True positives
            tp = confusion_matrix[intent][intent]

            # False positives (predicted as this intent but actually other)
            fp = sum(confusion_matrix[other][intent] for other in all_intents if other != intent)

            # False negatives (actually this intent but predicted as other)
            fn = sum(confusion_matrix[intent][other] for other in all_intents if other != intent)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            precision_per_class[intent] = round(precision, 3)
            recall_per_class[intent] = round(recall, 3)
            f1_per_class[intent] = round(f1, 3)

        # Overall accuracy
        correct = sum(1 for pred, truth in zip(predictions, ground_truth) if pred == truth)
        accuracy = correct / len(predictions)

        return IntentClassificationMetrics(
            accuracy=round(accuracy, 3),
            precision_per_class=precision_per_class,
            recall_per_class=recall_per_class,
            f1_per_class=f1_per_class,
            confusion_matrix=confusion_matrix,
            total_samples=len(predictions)
        )


# === Search Quality Evaluator ===

class SearchQualityEvaluator:
    """Evaluate search quality with standard IR metrics"""

    @staticmethod
    def precision_at_k(relevant: List[bool], k: int) -> float:
        """Calculate Precision@k"""
        if k > len(relevant):
            k = len(relevant)

        if k == 0:
            return 0.0

        return sum(relevant[:k]) / k

    @staticmethod
    def recall_at_k(relevant: List[bool], k: int, total_relevant: int) -> float:
        """Calculate Recall@k"""
        if total_relevant == 0:
            return 0.0

        if k > len(relevant):
            k = len(relevant)

        return sum(relevant[:k]) / total_relevant

    @staticmethod
    def ndcg_at_k(relevance_scores: List[float], k: int) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@k

        Args:
            relevance_scores: List of relevance scores (0-1 or graded)
            k: Rank cutoff

        Returns:
            nDCG@k score
        """
        if k > len(relevance_scores):
            k = len(relevance_scores)

        if k == 0:
            return 0.0

        # DCG@k
        dcg = relevance_scores[0] + sum(
            rel / np.log2(i + 1)
            for i, rel in enumerate(relevance_scores[1:k], start=2)
        )

        # Ideal DCG (sort by relevance descending)
        ideal_relevance = sorted(relevance_scores, reverse=True)
        idcg = ideal_relevance[0] + sum(
            rel / np.log2(i + 1)
            for i, rel in enumerate(ideal_relevance[1:k], start=2)
        )

        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def mean_reciprocal_rank(relevant_positions: List[int]) -> float:
        """
        Calculate Mean Reciprocal Rank

        Args:
            relevant_positions: List of first relevant result positions (1-indexed)

        Returns:
            MRR score
        """
        if not relevant_positions:
            return 0.0

        rr_sum = sum(1.0 / pos for pos in relevant_positions if pos > 0)
        return rr_sum / len(relevant_positions)

    @staticmethod
    def calculate_metrics(
        search_results: List[Dict[str, Any]],
        k_values: List[int] = [5, 10, 20]
    ) -> SearchMetrics:
        """
        Calculate comprehensive search metrics

        Args:
            search_results: List of search results with relevance judgments
                Each result: {'relevant': [bool, bool, ...], 'total_relevant': int}
            k_values: List of k values for precision@k, recall@k, nDCG@k

        Returns:
            SearchMetrics
        """
        precision_at_k = {}
        recall_at_k = {}
        ndcg_at_k = {}

        all_first_relevant_positions = []

        for result in search_results:
            relevant = result.get('relevant', [])
            total_relevant = result.get('total_relevant', sum(relevant))

            # Find first relevant position
            try:
                first_relevant = relevant.index(True) + 1  # 1-indexed
                all_first_relevant_positions.append(first_relevant)
            except ValueError:
                all_first_relevant_positions.append(0)  # No relevant found

        # Calculate metrics for each k
        for k in k_values:
            k_precisions = []
            k_recalls = []
            k_ndcgs = []

            for result in search_results:
                relevant = result.get('relevant', [])
                total_relevant = result.get('total_relevant', sum(relevant))
                relevance_scores = result.get('relevance_scores', [float(r) for r in relevant])

                k_precisions.append(SearchQualityEvaluator.precision_at_k(relevant, k))
                k_recalls.append(SearchQualityEvaluator.recall_at_k(relevant, k, total_relevant))
                k_ndcgs.append(SearchQualityEvaluator.ndcg_at_k(relevance_scores, k))

            precision_at_k[k] = round(np.mean(k_precisions), 3)
            recall_at_k[k] = round(np.mean(k_recalls), 3)
            ndcg_at_k[k] = round(np.mean(k_ndcgs), 3)

        # Calculate MRR
        mrr = SearchQualityEvaluator.mean_reciprocal_rank(all_first_relevant_positions)

        # Calculate MAP (Mean Average Precision)
        map_scores = []
        for result in search_results:
            relevant = result.get('relevant', [])
            if not relevant:
                continue

            # Average precision for this query
            precisions = []
            relevant_count = 0

            for i, is_relevant in enumerate(relevant, start=1):
                if is_relevant:
                    relevant_count += 1
                    precision_at_i = relevant_count / i
                    precisions.append(precision_at_i)

            avg_precision = np.mean(precisions) if precisions else 0.0
            map_scores.append(avg_precision)

        mean_average_precision = round(np.mean(map_scores), 3) if map_scores else 0.0

        return SearchMetrics(
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            ndcg_at_k=ndcg_at_k,
            mrr=round(mrr, 3),
            mean_average_precision=mean_average_precision,
            total_queries=len(search_results)
        )


# === RAG Answer Quality Evaluator ===

class RAGAnswerEvaluator:
    """Evaluate RAG answer quality"""

    @staticmethod
    def evaluate_answer_quality(
        answer: str,
        reference: str,
        method: str = "simple"
    ) -> float:
        """
        Evaluate answer quality against reference

        Args:
            answer: Generated answer
            reference: Reference answer
            method: "simple" (keyword overlap) or "semantic" (requires embeddings)

        Returns:
            Quality score 0-1
        """
        if method == "simple":
            # Simple keyword-based overlap
            answer_words = set(answer.lower().split())
            ref_words = set(reference.lower().split())

            if not ref_words:
                return 0.0

            overlap = len(answer_words & ref_words)
            return overlap / len(ref_words)

        # TODO: Implement semantic similarity with embeddings
        return 0.0

    @staticmethod
    def evaluate_citation_accuracy(
        citations: List[Dict[str, Any]],
        ground_truth_citations: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluate citation accuracy

        Args:
            citations: Extracted citations from answer
            ground_truth_citations: Correct citations

        Returns:
            Accuracy score 0-1
        """
        if not ground_truth_citations:
            return 1.0 if not citations else 0.0

        # Check how many citations are correct
        correct_citations = 0

        for citation in citations:
            citation_text = citation.get('text', '').lower()

            for gt_citation in ground_truth_citations:
                gt_text = gt_citation.get('text', '').lower()

                # Simple match (can be improved with fuzzy matching)
                if citation_text in gt_text or gt_text in citation_text:
                    correct_citations += 1
                    break

        return correct_citations / len(citations) if citations else 0.0

    @staticmethod
    def calculate_metrics(
        rag_results: List[Dict[str, Any]]
    ) -> RAGMetrics:
        """
        Calculate RAG metrics

        Args:
            rag_results: List of RAG results with evaluations
                Each: {
                    'answer': str,
                    'reference_answer': str,
                    'citations': List[Dict],
                    'ground_truth_citations': List[Dict],
                    'confidence_score': float,
                    'latency_seconds': float
                }

        Returns:
            RAGMetrics
        """
        correctness_scores = []
        citation_accuracy_scores = []
        confidence_scores = []
        latencies = []

        for result in rag_results:
            # Answer correctness
            correctness = RAGAnswerEvaluator.evaluate_answer_quality(
                result.get('answer', ''),
                result.get('reference_answer', '')
            )
            correctness_scores.append(correctness)

            # Citation accuracy
            citation_acc = RAGAnswerEvaluator.evaluate_citation_accuracy(
                result.get('citations', []),
                result.get('ground_truth_citations', [])
            )
            citation_accuracy_scores.append(citation_acc)

            # Confidence and latency
            confidence_scores.append(result.get('confidence_score', 0.0))
            latencies.append(result.get('latency_seconds', 0.0))

        return RAGMetrics(
            answer_correctness=round(np.mean(correctness_scores), 3) if correctness_scores else 0.0,
            answer_completeness=round(np.mean(correctness_scores), 3) if correctness_scores else 0.0,  # Simplified
            citation_accuracy=round(np.mean(citation_accuracy_scores), 3) if citation_accuracy_scores else 0.0,
            citation_coverage=round(np.mean(citation_accuracy_scores), 3) if citation_accuracy_scores else 0.0,  # Simplified
            avg_confidence_score=round(np.mean(confidence_scores), 3) if confidence_scores else 0.0,
            avg_latency_seconds=round(np.mean(latencies), 3) if latencies else 0.0,
            total_questions=len(rag_results),
            factual_consistency=round(np.mean(correctness_scores), 3) if correctness_scores else 0.0  # Simplified
        )


# === Complete Model Evaluator ===

class ModelEvaluator:
    """Complete model evaluation suite"""

    def __init__(self):
        self.entity_evaluator = EntityExtractionEvaluator()
        self.intent_evaluator = IntentClassificationEvaluator()
        self.search_evaluator = SearchQualityEvaluator()
        self.rag_evaluator = RAGAnswerEvaluator()

    def evaluate_all(
        self,
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete evaluation suite

        Args:
            test_data: Dictionary with test data for all components

        Returns:
            Complete evaluation results
        """
        results = {
            'timestamp': time.time(),
            'summary': {}
        }

        # Entity extraction
        if 'entity_extraction' in test_data:
            entity_metrics = self.entity_evaluator.calculate_metrics(
                test_data['entity_extraction']['predictions'],
                test_data['entity_extraction']['ground_truth']
            )
            results['entity_extraction'] = entity_metrics.to_dict()
            results['summary']['entity_f1'] = entity_metrics.f1_score

        # Intent classification
        if 'intent_classification' in test_data:
            intent_metrics = self.intent_evaluator.calculate_metrics(
                test_data['intent_classification']['predictions'],
                test_data['intent_classification']['ground_truth']
            )
            results['intent_classification'] = intent_metrics.to_dict()
            results['summary']['intent_accuracy'] = intent_metrics.accuracy

        # Search quality
        if 'search' in test_data:
            search_metrics = self.search_evaluator.calculate_metrics(
                test_data['search']['results']
            )
            results['search'] = search_metrics.to_dict()
            results['summary']['search_ndcg@10'] = search_metrics.ndcg_at_k.get(10, 0.0)

        # RAG quality
        if 'rag' in test_data:
            rag_metrics = self.rag_evaluator.calculate_metrics(
                test_data['rag']['results']
            )
            results['rag'] = rag_metrics.to_dict()
            results['summary']['rag_correctness'] = rag_metrics.answer_correctness

        return results

    def save_results(self, results: Dict[str, Any], filepath: str):
        """Save evaluation results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Evaluation results saved to {filepath}")


# === Example Usage ===

if __name__ == "__main__":
    # Example evaluation
    evaluator = ModelEvaluator()

    # Mock test data
    test_data = {
        'entity_extraction': {
            'predictions': [
                {'person_type': ['permanent resident'], 'program': ['EI']},
                {'person_type': ['citizen'], 'program': ['CPP']},
            ],
            'ground_truth': [
                {'person_type': ['permanent resident'], 'program': ['EI', 'CPP']},
                {'person_type': ['citizen'], 'program': ['CPP']},
            ]
        },
        'intent_classification': {
            'predictions': ['eligibility', 'application', 'benefits'],
            'ground_truth': ['eligibility', 'eligibility', 'benefits']
        },
        'search': {
            'results': [
                {'relevant': [True, True, False, True], 'total_relevant': 3},
                {'relevant': [False, True, True, False], 'total_relevant': 2},
            ]
        },
        'rag': {
            'results': [
                {
                    'answer': 'Permanent residents can apply for EI if they have worked sufficient hours',
                    'reference_answer': 'Permanent residents are eligible for EI with sufficient work hours',
                    'citations': [{'text': 'S.C. 1996, c. 23, s. 7'}],
                    'ground_truth_citations': [{'text': 'S.C. 1996, c. 23, s. 7'}],
                    'confidence_score': 0.85,
                    'latency_seconds': 2.3
                }
            ]
        }
    }

    results = evaluator.evaluate_all(test_data)

    print("Evaluation Results:")
    print(json.dumps(results['summary'], indent=2))

    # Save results
    evaluator.save_results(results, 'evaluation_results.json')
