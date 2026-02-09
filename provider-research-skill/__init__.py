"""
Provider Research Skill
=======================

LLM-enhanced healthcare provider research system for Claude AI.

Features:
- Prompt interpretation with pronoun resolution
- Multi-layer search (database → semantic → web)
- Intelligent data extraction from unstructured content
- Smart deduplication with edge case handling
- NPI registry matching

Usage:
    from provider_research_skill import ProviderResearchLLM, ProviderDatabasePostgres
    
    db = ProviderDatabasePostgres()
    research = ProviderResearchLLM(db=db)
    
    result = research.process_query(
        user_query="Find Home Instead in Boston, MA",
        user_context={"location": "New York, NY"}
    )
"""

from .provider_research_llm import (
    ProviderResearchLLM,
    ParsedQuery,
    Intent,
    MatchResult,
    ExtractionResult,
)

from .provider_database_postgres import ProviderDatabasePostgres
from .provider_database_sqlite import ProviderDatabase as ProviderDatabaseSQLite
from .provider_search import fuzzy_search, search_providers, display_results

__version__ = "1.0.0"
__author__ = "Your Name"

__all__ = [
    # Main classes
    "ProviderResearchLLM",
    "ProviderDatabasePostgres",
    "ProviderDatabaseSQLite",
    
    # Data classes
    "ParsedQuery",
    "Intent",
    "MatchResult",
    "ExtractionResult",
    
    # Functions
    "fuzzy_search",
    "search_providers",
    "display_results",
]
