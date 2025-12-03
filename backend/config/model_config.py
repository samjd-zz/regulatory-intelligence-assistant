"""
Model Configuration Management

Centralized configuration for all AI models and services including:
- NLP model settings and parameters
- Gemini API configuration
- Elasticsearch settings
- Search and ranking parameters
- Feature flags and toggles
- Environment-specific overrides

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# === Environment Configuration ===

class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


def get_environment() -> Environment:
    """Get current environment from env var"""
    env = os.getenv("APP_ENV", "development").lower()
    try:
        return Environment(env)
    except ValueError:
        logger.warning(f"Unknown environment '{env}', defaulting to development")
        return Environment.DEVELOPMENT


# === NLP Model Configuration ===

@dataclass
class NLPModelConfig:
    """Configuration for NLP models"""

    # Entity extraction settings
    entity_extraction_enabled: bool = True
    entity_confidence_threshold: float = 0.5
    max_entities_per_type: int = 10

    # Supported entity types
    entity_types: List[str] = field(default_factory=lambda: [
        "person_type", "jurisdiction", "program",
        "document_type", "legal_term", "date",
        "monetary_amount", "authority"
    ])

    # Query parsing settings
    query_parsing_enabled: bool = True
    intent_confidence_threshold: float = 0.6
    max_filters: int = 20

    # Intent types
    intent_types: List[str] = field(default_factory=lambda: [
        "search", "compliance_check", "interpretation",
        "comparison", "eligibility", "process",
        "definition", "amendment"
    ])

    # Performance settings
    max_query_length: int = 500
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600

    # Pattern matching
    case_sensitive: bool = False
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'NLPModelConfig':
        """Create from dictionary"""
        return cls(**config)


# === Gemini API Configuration ===

@dataclass
class GeminiConfig:
    """Configuration for Gemini API"""

    # API settings
    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = "gemini-1.5-flash"
    api_endpoint: str = "https://generativelanguage.googleapis.com"

    # Generation parameters
    temperature: float = 0.1  # Low for consistency in legal domain
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048

    # Safety settings
    safety_level: str = "BLOCK_MEDIUM_AND_ABOVE"
    enable_safety_filtering: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 1500
    enable_rate_limiting: bool = True

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0

    # Timeout settings
    request_timeout_seconds: int = 30

    # Caching
    enable_response_cache: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    max_cache_size_mb: int = 500

    # File upload settings
    max_file_size_mb: int = 20
    supported_file_types: List[str] = field(default_factory=lambda: [
        "application/pdf",
        "text/plain",
        "text/html"
    ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding API key)"""
        data = asdict(self)
        data.pop('api_key', None)  # Don't expose API key
        return data

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and len(self.api_key) > 0)


# === Elasticsearch Configuration ===

@dataclass
class ElasticsearchConfig:
    """Configuration for Elasticsearch"""

    # Connection settings
    url: str = field(default_factory=lambda: os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"))
    username: Optional[str] = field(default_factory=lambda: os.getenv("ELASTICSEARCH_USER"))
    password: Optional[str] = field(default_factory=lambda: os.getenv("ELASTICSEARCH_PASSWORD"))

    # Index settings
    index_name: str = "regulatory_documents"
    number_of_shards: int = 1
    number_of_replicas: int = 0  # 0 for dev, 1+ for prod

    # Vector search settings
    vector_dimension: int = 384  # For all-MiniLM-L6-v2
    vector_similarity_metric: str = "cosine"
    enable_approximate_search: bool = True

    # Search settings
    default_search_size: int = 10
    max_search_size: int = 100
    search_timeout_seconds: int = 30

    # BM25 parameters
    bm25_k1: float = 1.2
    bm25_b: float = 0.75

    # Hybrid search weights
    default_keyword_weight: float = 0.5
    default_vector_weight: float = 0.5

    # Performance settings
    enable_query_cache: bool = True
    enable_request_cache: bool = True
    refresh_interval: str = "1s"

    # Bulk indexing
    bulk_chunk_size: int = 500
    bulk_timeout_seconds: int = 60
    max_concurrent_requests: int = 4

    # Connection pooling
    max_connections: int = 10
    connection_timeout_seconds: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding credentials)"""
        data = asdict(self)
        data.pop('password', None)
        data.pop('username', None)
        return data

    @property
    def is_configured(self) -> bool:
        """Check if Elasticsearch is configured"""
        return bool(self.url)


# === Search and Ranking Configuration ===

@dataclass
class SearchConfig:
    """Configuration for search and ranking"""

    # Relevance scoring
    min_relevance_score: float = 0.1
    boost_exact_match: float = 2.0
    boost_title_match: float = 1.5
    boost_recent_docs: bool = True
    recency_decay_days: int = 365

    # Result filtering
    enable_jurisdiction_filter: bool = True
    enable_date_filter: bool = True
    enable_document_type_filter: bool = True

    # Faceted search
    enable_facets: bool = True
    max_facet_values: int = 20
    facet_fields: List[str] = field(default_factory=lambda: [
        "jurisdiction", "document_type",
        "authority", "program", "tags"
    ])

    # Search features
    enable_autocomplete: bool = True
    enable_spell_check: bool = True
    enable_suggestions: bool = True
    max_suggestions: int = 5

    # Highlight settings
    enable_highlighting: bool = True
    highlight_pre_tag: str = "<mark>"
    highlight_post_tag: str = "</mark>"
    highlight_fragment_size: int = 150
    highlight_max_fragments: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# === RAG Configuration ===

@dataclass
class RAGConfig:
    """Configuration for RAG (Retrieval-Augmented Generation)"""

    # Retrieval settings
    num_context_documents: int = 5
    min_context_relevance: float = 0.3
    max_context_length: int = 4000
    context_window_tokens: int = 8000

    # Citation extraction
    enable_citation_extraction: bool = True
    citation_patterns: List[str] = field(default_factory=lambda: [
        r"S\.C\.\s+\d{4}[^.]+",  # Statutes of Canada
        r"R\.S\.C\.\s+\d{4}[^.]+"  # Revised Statutes
    ])
    min_citations: int = 1
    max_citations: int = 5

    # Confidence scoring
    enable_confidence_scoring: bool = True
    min_confidence_threshold: float = 0.4
    confidence_factors: List[str] = field(default_factory=lambda: [
        "citation_count", "context_relevance",
        "answer_length", "specificity"
    ])

    # Answer generation
    max_answer_length: int = 500
    enable_plain_language: bool = True
    enable_source_attribution: bool = True

    # Caching
    enable_answer_cache: bool = True
    cache_ttl_seconds: int = 3600
    cache_similar_threshold: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# === Feature Flags ===

@dataclass
class FeatureFlags:
    """Feature toggles for experimental features"""

    # Experimental features
    enable_graph_search: bool = False
    enable_multi_hop_reasoning: bool = False
    enable_query_rewriting: bool = False
    enable_answer_validation: bool = False

    # Beta features
    enable_autocomplete: bool = True
    enable_query_suggestions: bool = True
    enable_similar_documents: bool = True

    # Performance features
    enable_async_indexing: bool = True
    enable_bulk_operations: bool = True
    enable_result_streaming: bool = False

    # Analytics
    enable_usage_tracking: bool = True
    enable_performance_monitoring: bool = True
    enable_error_reporting: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# === Master Configuration ===

@dataclass
class ModelConfiguration:
    """Master configuration for all models and services"""

    environment: Environment = field(default_factory=get_environment)
    nlp: NLPModelConfig = field(default_factory=NLPModelConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    elasticsearch: ElasticsearchConfig = field(default_factory=ElasticsearchConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    # Version tracking
    config_version: str = "1.0.0"
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'environment': self.environment.value,
            'nlp': self.nlp.to_dict(),
            'gemini': self.gemini.to_dict(),
            'elasticsearch': self.elasticsearch.to_dict(),
            'search': self.search.to_dict(),
            'rag': self.rag.to_dict(),
            'features': self.features.to_dict(),
            'config_version': self.config_version,
            'last_updated': self.last_updated
        }

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'ModelConfiguration':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls(
            environment=Environment(data.get('environment', 'development')),
            nlp=NLPModelConfig.from_dict(data.get('nlp', {})),
            gemini=GeminiConfig(**data.get('gemini', {})),
            elasticsearch=ElasticsearchConfig(**data.get('elasticsearch', {})),
            search=SearchConfig(**data.get('search', {})),
            rag=RAGConfig(**data.get('rag', {})),
            features=FeatureFlags(**data.get('features', {})),
            config_version=data.get('config_version', '1.0.0'),
            last_updated=data.get('last_updated')
        )

    def apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        if self.environment == Environment.PRODUCTION:
            # Production optimizations
            self.elasticsearch.number_of_replicas = 2
            self.elasticsearch.refresh_interval = "5s"
            self.gemini.temperature = 0.05  # More conservative
            self.features.enable_error_reporting = True
            self.nlp.enable_caching = True

        elif self.environment == Environment.STAGING:
            # Staging settings
            self.elasticsearch.number_of_replicas = 1
            self.features.enable_performance_monitoring = True

        elif self.environment == Environment.DEVELOPMENT:
            # Development settings
            self.elasticsearch.number_of_replicas = 0
            self.features.enable_usage_tracking = False

        elif self.environment == Environment.TEST:
            # Test settings
            self.elasticsearch.number_of_replicas = 0
            self.nlp.enable_caching = False
            self.rag.enable_answer_cache = False
            self.gemini.enable_response_cache = False

        logger.info(f"Applied {self.environment.value} environment overrides")


# === Configuration Manager ===

class ConfigurationManager:
    """Singleton configuration manager"""

    _instance = None
    _config: Optional[ModelConfiguration] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.reload()

    def reload(self):
        """Reload configuration from environment and files"""
        config_file = os.getenv("MODEL_CONFIG_FILE")

        if config_file and Path(config_file).exists():
            logger.info(f"Loading configuration from {config_file}")
            self._config = ModelConfiguration.load_from_file(config_file)
        else:
            logger.info("Using default configuration")
            self._config = ModelConfiguration()

        # Apply environment overrides
        self._config.apply_environment_overrides()

        logger.info(f"Configuration loaded for {self._config.environment.value} environment")

    @property
    def config(self) -> ModelConfiguration:
        """Get current configuration"""
        if self._config is None:
            self.reload()
        return self._config

    def get_nlp_config(self) -> NLPModelConfig:
        """Get NLP configuration"""
        return self.config.nlp

    def get_gemini_config(self) -> GeminiConfig:
        """Get Gemini configuration"""
        return self.config.gemini

    def get_elasticsearch_config(self) -> ElasticsearchConfig:
        """Get Elasticsearch configuration"""
        return self.config.elasticsearch

    def get_search_config(self) -> SearchConfig:
        """Get search configuration"""
        return self.config.search

    def get_rag_config(self) -> RAGConfig:
        """Get RAG configuration"""
        return self.config.rag

    def get_feature_flags(self) -> FeatureFlags:
        """Get feature flags"""
        return self.config.features

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.config.features, feature_name, False)


# Global configuration instance
config_manager = ConfigurationManager()


# === Helper Functions ===

def get_config() -> ModelConfiguration:
    """Get global configuration"""
    return config_manager.config


def get_nlp_config() -> NLPModelConfig:
    """Get NLP configuration"""
    return config_manager.get_nlp_config()


def get_gemini_config() -> GeminiConfig:
    """Get Gemini configuration"""
    return config_manager.get_gemini_config()


def get_elasticsearch_config() -> ElasticsearchConfig:
    """Get Elasticsearch configuration"""
    return config_manager.get_elasticsearch_config()


def get_search_config() -> SearchConfig:
    """Get search configuration"""
    return config_manager.get_search_config()


def get_rag_config() -> RAGConfig:
    """Get RAG configuration"""
    return config_manager.get_rag_config()


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return config_manager.is_feature_enabled(feature_name)


# === Example Usage ===

if __name__ == "__main__":
    # Get configuration
    config = get_config()
    print(f"Environment: {config.environment.value}")
    print(f"Gemini configured: {config.gemini.is_configured}")
    print(f"Elasticsearch URL: {config.elasticsearch.url}")

    # Check feature flags
    print(f"Graph search enabled: {is_feature_enabled('enable_graph_search')}")
    print(f"Query suggestions enabled: {is_feature_enabled('enable_query_suggestions')}")

    # Save configuration
    config.save_to_file("model_config.json")

    # Load configuration
    loaded = ModelConfiguration.load_from_file("model_config.json")
    print(f"Loaded config version: {loaded.config_version}")
