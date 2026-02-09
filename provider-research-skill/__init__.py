"""
Provider Research Skill Package
================================

ARCHITECTURE v2.0.0: Multi-Skill with Central Orchestrator
-----------------------------------------------------------

Skills:
1. Provider Query Interpreter - Natural language understanding
2. Provider Database Manager - Fast rule-based search & CRUD
3. Provider Semantic Matcher - Intelligent matching beyond strings  
4. Provider Web Researcher - Deep research with data extraction

Orchestrator:
- Routes queries through appropriate skills
- Manages state and conversation context
- Optimizes token usage via short-circuiting
- Provides unified interface

RECOMMENDED USAGE (v2.0.0):
--------------------------
    from provider_research_skill import ProviderOrchestrator
    
    orchestrator = ProviderOrchestrator(db_config, llm_client)
    result = orchestrator.process_query(
        user_query="Find Home Instead near me",
        user_context={"location": "Boston, MA"}
    )

LEGACY USAGE (v1.0.0 - Still Supported):
----------------------------------------
    from provider_research_skill import ProviderResearchLLM, ProviderDatabasePostgres
    
    db = ProviderDatabasePostgres()
    research = ProviderResearchLLM(db=db)
    
    result = research.process_query(
        user_query="Find Home Instead in Boston, MA",
        user_context={"location": "New York, NY"}
    )
"""

# MAIN ORCHESTRATOR (v2.0.0 - Recommended)
from .provider_orchestrator import (
    ProviderOrchestrator,
    OrchestrationResult,
    ExecutionPath
)

# INDIVIDUAL SKILLS (for direct access)
from .provider_query_interpreter import (
    ProviderQueryInterpreter,
    Intent,
)
from .provider_database_manager import (
    ProviderDatabaseManager,
    SearchResult as DatabaseSearchResult,
)
from .provider_semantic_matcher import (
    ProviderSemanticMatcher,
    SemanticMatch,
)
from .provider_web_researcher import (
    ProviderWebResearcher,
    ResearchResult,
    DeduplicationResult,
)

# LEGACY MODULES (v1.0.0 - Backward Compatibility)
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

__version__ = "2.0.0"  # Multi-skill architecture
__author__ = "Your Name"

__all__ = [
    # Main Orchestrator (v2.0.0)
    "ProviderOrchestrator",
    "OrchestrationResult",
    "ExecutionPath",
    
    # Individual Skills
    "ProviderQueryInterpreter",
    "ProviderDatabaseManager",
    "ProviderSemanticMatcher",
    "ProviderWebResearcher",
    
    # Skill Data Classes
    "DatabaseSearchResult",
    "SemanticMatch",
    "ResearchResult",
    "DeduplicationResult",
    
    # Legacy Main Classes (v1.0.0)
    "ProviderResearchLLM",
    "ProviderDatabasePostgres",
    "ProviderDatabaseSQLite",
    
    # Legacy Data Classes
    "ParsedQuery",
    "Intent",
    "MatchResult",
    "ExtractionResult",
    
    # Functions
    "fuzzy_search",
    "search_providers",
    "display_results",
]
