"""Custom exceptions for provider_research package."""


class ProviderResearchError(Exception):
    """Base exception for provider research system."""
    pass


class DatabaseError(ProviderResearchError):
    """Database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Failed to connect to database."""
    pass


class SearchError(ProviderResearchError):
    """Search operation errors."""
    pass


class ValidationError(ProviderResearchError):
    """Data validation errors."""
    pass


class ConfigurationError(ProviderResearchError):
    """Configuration-related errors."""
    pass


class LLMError(ProviderResearchError):
    """LLM API errors."""
    pass


class WebScrapingError(ProviderResearchError):
    """Web scraping errors."""
    pass


class NPIRegistryError(ProviderResearchError):
    """NPI registry lookup errors."""
    pass
