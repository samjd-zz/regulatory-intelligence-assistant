"""
Configuration Validation

Validates model configurations to ensure correctness and completeness
before deployment.

Features:
- Schema validation
- Constraint checking
- Dependency verification
- Security validation
- Performance warnings

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import re

from config.model_config import (
    ModelConfiguration,
    NLPModelConfig,
    GeminiConfig,
    ElasticsearchConfig,
    SearchConfig,
    RAGConfig,
    FeatureFlags,
    Environment
)

logger = logging.getLogger(__name__)


# === Validation Results ===

@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # error, warning, info
    category: str  # schema, security, performance, dependency
    message: str
    field: str = ""
    suggestion: str = ""

    def __str__(self) -> str:
        parts = [f"[{self.severity.upper()}]", self.message]
        if self.field:
            parts.insert(1, f"({self.field})")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Results of configuration validation"""
    valid: bool
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]
    info: List[ValidationIssue]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def total_issues(self) -> int:
        return len(self.errors) + len(self.warnings) + len(self.info)

    def print_summary(self):
        """Print validation summary"""
        print("=" * 80)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 80)
        print(f"Status: {'✓ VALID' if self.valid else '✗ INVALID'}")
        print(f"Errors: {self.error_count}")
        print(f"Warnings: {self.warning_count}")
        print(f"Info: {len(self.info)}")
        print()

        if self.errors:
            print("ERRORS:")
            for issue in self.errors:
                print(f"  ✗ {issue}")
            print()

        if self.warnings:
            print("WARNINGS:")
            for issue in self.warnings:
                print(f"  ⚠ {issue}")
            print()

        if self.info:
            print("INFO:")
            for issue in self.info:
                print(f"  ℹ {issue}")

        print("=" * 80)


# === Configuration Validator ===

class ConfigurationValidator:
    """Validates model configurations"""

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def _add_error(self, message: str, field: str = "", category: str = "schema", suggestion: str = ""):
        """Add validation error"""
        self.issues.append(ValidationIssue(
            severity="error",
            category=category,
            message=message,
            field=field,
            suggestion=suggestion
        ))

    def _add_warning(self, message: str, field: str = "", category: str = "performance", suggestion: str = ""):
        """Add validation warning"""
        self.issues.append(ValidationIssue(
            severity="warning",
            category=category,
            message=message,
            field=field,
            suggestion=suggestion
        ))

    def _add_info(self, message: str, field: str = "", category: str = "info"):
        """Add validation info"""
        self.issues.append(ValidationIssue(
            severity="info",
            category=category,
            message=message,
            field=field
        ))

    def validate_nlp_config(self, config: NLPModelConfig):
        """Validate NLP configuration"""

        # Check confidence thresholds
        if not 0.0 <= config.entity_confidence_threshold <= 1.0:
            self._add_error(
                "Entity confidence threshold must be between 0.0 and 1.0",
                field="entity_confidence_threshold",
                suggestion="Set value between 0.5-0.8 for optimal results"
            )

        if not 0.0 <= config.intent_confidence_threshold <= 1.0:
            self._add_error(
                "Intent confidence threshold must be between 0.0 and 1.0",
                field="intent_confidence_threshold"
            )

        # Check limits
        if config.max_query_length < 100:
            self._add_warning(
                "Max query length is very low, may truncate valid queries",
                field="max_query_length",
                suggestion="Consider increasing to at least 500 characters"
            )

        if config.max_query_length > 5000:
            self._add_warning(
                "Max query length is very high, may impact performance",
                field="max_query_length",
                category="performance"
            )

        # Check entity types
        if len(config.entity_types) == 0:
            self._add_error(
                "No entity types configured",
                field="entity_types",
                suggestion="Add at least: person_type, jurisdiction, program"
            )

        # Check cache settings
        if config.enable_caching and config.cache_ttl_seconds < 60:
            self._add_warning(
                "Cache TTL is very low, may not provide performance benefits",
                field="cache_ttl_seconds",
                suggestion="Consider increasing to at least 3600 seconds (1 hour)"
            )

    def validate_gemini_config(self, config: GeminiConfig):
        """Validate Gemini configuration"""

        # Check API key
        if not config.api_key:
            self._add_error(
                "Gemini API key not configured",
                field="api_key",
                category="security",
                suggestion="Set GEMINI_API_KEY environment variable"
            )

        # Check temperature
        if not 0.0 <= config.temperature <= 2.0:
            self._add_error(
                "Temperature must be between 0.0 and 2.0",
                field="temperature"
            )

        if config.temperature > 0.3:
            self._add_warning(
                "High temperature may reduce consistency in legal domain",
                field="temperature",
                suggestion="Use temperature 0.1-0.2 for legal Q&A"
            )

        # Check token limits
        if config.max_output_tokens < 100:
            self._add_error(
                "Max output tokens too low",
                field="max_output_tokens",
                suggestion="Minimum 500 tokens for legal answers"
            )

        if config.max_output_tokens > 8192:
            self._add_warning(
                "Very high max output tokens may increase latency",
                field="max_output_tokens",
                category="performance"
            )

        # Check rate limits
        if config.rate_limit_per_minute > 60:
            self._add_warning(
                "Rate limit may exceed API quota",
                field="rate_limit_per_minute",
                suggestion="Check your Gemini API plan limits"
            )

        # Check retry settings
        if config.max_retries > 5:
            self._add_warning(
                "High retry count may cause long delays on failures",
                field="max_retries",
                category="performance"
            )

    def validate_elasticsearch_config(self, config: ElasticsearchConfig):
        """Validate Elasticsearch configuration"""

        # Check URL
        if not config.url:
            self._add_error(
                "Elasticsearch URL not configured",
                field="url",
                suggestion="Set ELASTICSEARCH_URL environment variable"
            )

        # Validate URL format
        if config.url and not re.match(r'https?://', config.url):
            self._add_error(
                "Invalid Elasticsearch URL format",
                field="url",
                suggestion="URL should start with http:// or https://"
            )

        # Check index settings
        if config.number_of_shards < 1:
            self._add_error(
                "Number of shards must be at least 1",
                field="number_of_shards"
            )

        if config.number_of_shards > 10:
            self._add_warning(
                "High number of shards may impact performance",
                field="number_of_shards",
                suggestion="Use 1-5 shards for most use cases"
            )

        # Check vector settings
        if config.vector_dimension not in [128, 256, 384, 512, 768, 1024]:
            self._add_warning(
                "Non-standard vector dimension",
                field="vector_dimension",
                suggestion="Common values: 384 (MiniLM), 768 (BERT)"
            )

        # Check search limits
        if config.max_search_size > 10000:
            self._add_warning(
                "Very high max search size may impact performance",
                field="max_search_size",
                category="performance"
            )

        # Check bulk settings
        if config.bulk_chunk_size > 10000:
            self._add_warning(
                "Very large bulk chunk size may cause memory issues",
                field="bulk_chunk_size",
                suggestion="Use 500-5000 for optimal performance"
            )

    def validate_search_config(self, config: SearchConfig):
        """Validate search configuration"""

        # Check relevance scores
        if not 0.0 <= config.min_relevance_score <= 1.0:
            self._add_error(
                "Min relevance score must be between 0.0 and 1.0",
                field="min_relevance_score"
            )

        # Check boost values
        if config.boost_exact_match < 1.0:
            self._add_warning(
                "Exact match boost should be >= 1.0 to prioritize exact matches",
                field="boost_exact_match"
            )

        # Check facet settings
        if config.enable_facets and config.max_facet_values < 5:
            self._add_warning(
                "Low max facet values may not show enough options",
                field="max_facet_values",
                suggestion="Use at least 10-20 facet values"
            )

        # Check suggestions
        if config.enable_suggestions and config.max_suggestions < 3:
            self._add_info(
                "Consider showing at least 3-5 suggestions",
                field="max_suggestions"
            )

    def validate_rag_config(self, config: RAGConfig):
        """Validate RAG configuration"""

        # Check context settings
        if config.num_context_documents < 1:
            self._add_error(
                "Must retrieve at least 1 context document",
                field="num_context_documents"
            )

        if config.num_context_documents > 10:
            self._add_warning(
                "Many context documents may increase latency and cost",
                field="num_context_documents",
                suggestion="Use 3-7 documents for optimal balance"
            )

        # Check relevance threshold
        if not 0.0 <= config.min_context_relevance <= 1.0:
            self._add_error(
                "Min context relevance must be between 0.0 and 1.0",
                field="min_context_relevance"
            )

        # Check confidence threshold
        if not 0.0 <= config.min_confidence_threshold <= 1.0:
            self._add_error(
                "Min confidence threshold must be between 0.0 and 1.0",
                field="min_confidence_threshold"
            )

        # Check citation settings
        if config.enable_citation_extraction and not config.citation_patterns:
            self._add_warning(
                "Citation extraction enabled but no patterns defined",
                field="citation_patterns",
                suggestion="Add regex patterns for legal citations"
            )

        # Check answer length
        if config.max_answer_length < 100:
            self._add_warning(
                "Max answer length may be too short for legal explanations",
                field="max_answer_length",
                suggestion="Use at least 300-500 characters"
            )

    def validate_feature_flags(self, flags: FeatureFlags, env: Environment):
        """Validate feature flags"""

        # Production checks
        if env == Environment.PRODUCTION:
            if flags.enable_multi_hop_reasoning:
                self._add_warning(
                    "Experimental feature enabled in production",
                    field="enable_multi_hop_reasoning",
                    category="security"
                )

            if not flags.enable_error_reporting:
                self._add_warning(
                    "Error reporting disabled in production",
                    field="enable_error_reporting",
                    suggestion="Enable for better monitoring"
                )

        # Performance checks
        if flags.enable_result_streaming and flags.enable_bulk_operations:
            self._add_info(
                "Both streaming and bulk operations enabled, ensure compatibility",
                field="enable_result_streaming"
            )

    def validate_environment_consistency(self, config: ModelConfiguration):
        """Validate environment-specific settings"""

        env = config.environment

        if env == Environment.PRODUCTION:
            # Production requirements
            if config.elasticsearch.number_of_replicas < 1:
                self._add_error(
                    "Production requires at least 1 Elasticsearch replica",
                    field="elasticsearch.number_of_replicas",
                    category="dependency"
                )

            if not config.features.enable_error_reporting:
                self._add_warning(
                    "Error reporting should be enabled in production",
                    category="dependency"
                )

            if config.gemini.temperature > 0.2:
                self._add_info(
                    "Consider lower temperature for production consistency"
                )

        elif env == Environment.TEST:
            # Test requirements
            if config.nlp.enable_caching:
                self._add_warning(
                    "Caching should be disabled in test environment for accuracy",
                    category="dependency"
                )

    def validate(self, config: ModelConfiguration) -> ValidationResult:
        """
        Validate complete configuration

        Args:
            config: Configuration to validate

        Returns:
            ValidationResult with all issues
        """
        self.issues = []

        # Validate each component
        self.validate_nlp_config(config.nlp)
        self.validate_gemini_config(config.gemini)
        self.validate_elasticsearch_config(config.elasticsearch)
        self.validate_search_config(config.search)
        self.validate_rag_config(config.rag)
        self.validate_feature_flags(config.features, config.environment)
        self.validate_environment_consistency(config)

        # Categorize issues
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]

        return ValidationResult(
            valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            info=info
        )


# === Example Usage ===

if __name__ == "__main__":
    from config.model_config import ModelConfiguration

    # Load configuration
    config = ModelConfiguration()

    # Validate
    validator = ConfigurationValidator()
    result = validator.validate(config)

    # Print report
    result.print_summary()

    # Exit with error code if invalid
    if not result.valid:
        exit(1)
