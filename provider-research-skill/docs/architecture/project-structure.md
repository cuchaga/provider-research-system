# Project Structure

## Overview

The Provider Research Skill is organized into a modular structure separating core LLM components, database layer, search functionality, and standalone tools.

## Directory Structure

```
provider-research-skill/
├── provider_research/              # Main package (LLM-integrated)
│   ├── __init__.py                 # Package exports and imports
│   ├── core/                       # Core LLM-powered components
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Main orchestration layer
│   │   ├── research_llm.py         # Legacy LLM research module
│   │   ├── query_interpreter.py    # Natural language understanding
│   │   └── semantic_matcher.py     # Intelligent semantic matching
│   ├── database/                   # Database layer
│   │   ├── __init__.py
│   │   ├── manager.py              # Database abstraction layer
│   │   ├── postgres.py             # PostgreSQL implementation
│   │   └── sqlite.py               # SQLite implementation
│   └── search/                     # Search and research
│       ├── __init__.py
│       ├── provider_search.py      # Rule-based fuzzy search
│       └── web_researcher.py       # Web scraping and extraction
├── tools/                          # Standalone CLI tools (no LLM)
│   ├── __init__.py
│   ├── enrich_and_deduplicate.py   # Data enrichment pipeline
│   ├── setup_postgres_schema.py    # Database schema setup
│   ├── import_to_postgres.py       # JSON to PostgreSQL importer
│   └── search_postgres.py          # CLI search interface
├── scripts/                        # Shell scripts
│   └── setup_postgres.sh           # PostgreSQL installation
├── docs/                           # Documentation
│   ├── architecture-diagram.html   # Interactive architecture
│   ├── architecture-diagram.mermaid # LLM workflow diagram
│   └── architecture-complete.mermaid # Complete workflows
├── data/                           # Data files (gitignored)
├── setup.py                        # Package installation
├── requirements.txt                # Python dependencies
├── README.md                       # Main documentation
├── ARCHITECTURE.md                 # (moved to docs/architecture/overview.md)
├── POSTGRES_SETUP.md              # PostgreSQL setup guide
└── LICENSE                         # MIT License
```

## Module Organization

### Core Package (`provider_research/`)

The main package for LLM-integrated conversational provider research.

#### `core/` - LLM-Powered Intelligence

- **orchestrator.py** - Multi-skill orchestrator that routes queries through appropriate processing layers
- **research_llm.py** - Legacy 6-layer LLM research system (v1.0.0, still supported)
- **query_interpreter.py** - Parses natural language into structured queries, resolves pronouns
- **semantic_matcher.py** - Matches providers using semantic understanding (abbreviations, DBAs, parent companies)

#### `database/` - Data Persistence

- **manager.py** - Abstract database interface with common operations
- **postgres.py** - PostgreSQL implementation with full-text search, JSONB support
- **sqlite.py** - SQLite implementation for development/testing

#### `search/` - Search Functionality

- **provider_search.py** - Rule-based fuzzy search algorithms (Levenshtein distance)
- **web_researcher.py** - Web scraping, data extraction, deduplication logic

### Standalone Tools (`tools/`)

Command-line utilities that work independently of the LLM system.

- **enrich_and_deduplicate.py** - Data pipeline: classify providers, web research, smart deduplication
- **setup_postgres_schema.py** - Creates PostgreSQL tables, indexes, triggers, full-text search
- **import_to_postgres.py** - Imports cleaned JSON provider data into PostgreSQL
- **search_postgres.py** - CLI for searching providers with full-text and pattern matching

## Usage Patterns

### LLM-Integrated (Conversational)

Use the main package for natural language queries:

```python
from provider_research import ProviderOrchestrator

orchestrator = ProviderOrchestrator(db_config, llm_client)
result = orchestrator.process_query(
    user_query="Find Home Instead near me",
    user_context={"location": "Boston, MA"}
)
```

### Standalone Tools (Batch)

Run tools directly from command line:

```bash
# Enrich data
python -m tools.enrich_and_deduplicate

# Setup database
python -m tools.setup_postgres_schema

# Import data
python -m tools.import_to_postgres

# Search providers
python -m tools.search_postgres "Home Instead" MA
```

## Import Paths

### From Main Package

```python
# Recommended (v2.0.0)
from provider_research import ProviderOrchestrator

# Individual components
from provider_research.core import ProviderQueryInterpreter, ProviderSemanticMatcher
from provider_research.database import ProviderDatabasePostgres
from provider_research.search import ProviderWebResearcher

# Legacy (v1.0.0 - still supported)
from provider_research import ProviderResearchLLM
```

### Direct Module Access

```python
# Direct access to specific modules
from provider_research.core.orchestrator import ProviderOrchestrator
from provider_research.database.postgres import ProviderDatabasePostgres
from provider_research.search.web_researcher import ProviderWebResearcher
```

## Migration from Old Structure

Old flat structure has been reorganized:

| Old Path | New Path |
|----------|----------|
| `provider_orchestrator.py` | `provider_research/core/orchestrator.py` |
| `provider_research_llm.py` | `provider_research/core/research_llm.py` |
| `provider_query_interpreter.py` | `provider_research/core/query_interpreter.py` |
| `provider_semantic_matcher.py` | `provider_research/core/semantic_matcher.py` |
| `provider_database_manager.py` | `provider_research/database/manager.py` |
| `provider_database_postgres.py` | `provider_research/database/postgres.py` |
| `provider_database_sqlite.py` | `provider_research/database/sqlite.py` |
| `provider_search.py` | `provider_research/search/provider_search.py` |
| `provider_web_researcher.py` | `provider_research/search/web_researcher.py` |
| `enrich_and_deduplicate.py` | `tools/data/enrich_and_deduplicate.py` |
| `setup_postgres_schema.py` | `tools/database/setup_postgres_schema.py` |
| `import_to_postgres.py` | `tools/database/import_to_postgres.py` |
| `search_postgres.py` | `tools/database/search_postgres.py` |

**Note:** The main `provider_research/__init__.py` maintains backward compatibility, so existing imports should continue to work.

## Benefits of New Structure

1. **Clearer Organization** - Related modules grouped together
2. **Better Separation of Concerns** - Core LLM logic separated from utilities
3. **Easier Navigation** - Find modules by purpose (core, database, search, tools)
4. **Scalability** - Easy to add new modules in appropriate categories
5. **Tool Independence** - Standalone tools clearly separated from LLM system
6. **Backward Compatibility** - Existing code continues to work via __init__.py exports
