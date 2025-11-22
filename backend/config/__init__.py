"""
Configuration Package

Centralized configuration management for the Regulatory Intelligence Assistant.

Exports:
- ModelConfiguration: Main configuration class
- ConfigurationManager: Singleton configuration manager
- ConfigurationValidator: Configuration validation
- get_config(): Get current configuration
- is_feature_enabled(): Check feature flags
"""

from config.model_config import (
    ModelConfiguration,
    NLPModelConfig,
    GeminiConfig,
    ElasticsearchConfig,
    SearchConfig,
    RAGConfig,
    FeatureFlags,
    Environment,
    ConfigurationManager,
    config_manager,
    get_config,
    get_nlp_config,
    get_gemini_config,
    get_elasticsearch_config,
    get_search_config,
    get_rag_config,
    is_feature_enabled
)

from config.config_validator import (
    ConfigurationValidator,
    ValidationResult,
    ValidationIssue
)

__all__ = [
    # Main configuration
    'ModelConfiguration',
    'NLPModelConfig',
    'GeminiConfig',
    'ElasticsearchConfig',
    'SearchConfig',
    'RAGConfig',
    'FeatureFlags',
    'Environment',

    # Configuration manager
    'ConfigurationManager',
    'config_manager',

    # Helper functions
    'get_config',
    'get_nlp_config',
    'get_gemini_config',
    'get_elasticsearch_config',
    'get_search_config',
    'get_rag_config',
    'is_feature_enabled',

    # Validation
    'ConfigurationValidator',
    'ValidationResult',
    'ValidationIssue'
]
