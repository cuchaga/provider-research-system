# Provider Research Skill

A comprehensive healthcare provider research system with LLM-enhanced intelligence for Claude AI.

[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview

This skill enables Claude to research, validate, and manage healthcare provider data with intelligent capabilities:

- **🧠 LLM-Powered Interpretation** - Understands natural language queries, resolves pronouns, handles "near me" requests
- **🔍 Multi-Layer Search** - Database → Semantic Matching → Web Research fallback
- **📊 Smart Data Extraction** - Extracts structured data from unstructured web content
- **🔄 Intelligent Deduplication** - Handles edge cases like same address/different suite
- **🏥 NPI Registry Integration** - Matches providers to official NPI records
- **📜 Historical Tracking** - Previous owners, name changes, acquisition history ⭐ NEW
- **🏢 Franchise Research** - Batch research and import for franchise locations ⭐ NEW
- **⚡ Standalone Tools** - CLI utilities for data enrichment, database setup, and search (no LLM required)

## Two Ways to Use

### 1. LLM-Integrated (Conversational)
Use with Claude AI for natural language provider research with intelligent query interpretation and multi-step reasoning.

### 2. Standalone Pipeline (Batch Processing)
Command-line tools for:
- Bulk data enrichment via web scraping
- PostgreSQL database setup and management  
- Provider data import and validation
- Fast CLI-based search with full-text capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
│         "Find healthcare providers near me"                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 0: LLM PROMPT INTERPRETATION (~800 tokens)                │
│  • Understands intent (search, add, compare, list)              │
│  • Resolves pronouns: "this", "that", "they" → entities         │
│  • Handles "near me" → user's location                          │
│  • Creates multi-step plans for complex queries                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATABASE SEARCH (0 tokens - rule-based)                │
│  • Exact match, fuzzy match, full-text search                   │
│  • Returns immediately if high-confidence match found           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Found?   │
               ┌─────────────┼─────────────┐
               │ YES         │             │ NO
               ▼             │             ▼
          [RETURN]           │    ┌───────────────────────────────┐
                             │    │  LAYER 2: SEMANTIC MATCHING   │
                             │    │  (~500 tokens)                │
                             │    │  • Abbreviations (CK→Comfort  │
                             │    │    Keepers)                   │
                             │    │  • Parent/subsidiary matching │
                             │    │  • DBA name resolution        │
                             │    └───────────────┬───────────────┘
                             │                    │
                             │           Found?   │
                             │      ┌─────────────┼─────────────┐
                             │      │ YES         │             │ NO
                             │      ▼             │             ▼
                             │  [RETURN]          │    ┌─────────────────┐
                             │                    │    │ LAYER 3: WEB    │
                             │                    │    │ RESEARCH        │
                             │                    │    │ (~5,000+ tokens)│
                             │                    │    └─────────────────┘
                             │                    │
                             └────────────────────┘
```

## Features

### Layer 0: Prompt Interpretation

| User Says | System Understands |
|-----------|-------------------|
| "Find Home Instead near me" | Search "Home Instead" in user's location |
| "What about their other locations?" | "their" = last discussed provider |
| "Add that to the database" | "that" = last research result |
| "Compare CK vs Visiting Angels" | Compare Comfort Keepers and Visiting Angels |

### Layer 2: Semantic Matching

| Search Query | Matches | Why |
|--------------|---------|-----|
| "CK" | Comfort Keepers | Abbreviation expansion |
| "Home Instead" | Home Instead - Metrowest | Parent/subsidiary |
| "VA Healthcare" | Visiting Angels | Context-aware abbreviation |

### Layer 4: Smart Deduplication

| Scenario | Result |
|----------|--------|
| Same phone, different address | Duplicate |
| Same address, different suite | Duplicate |
| Franchise vs Corporate HQ | NOT duplicate |

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 16+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/cuchaga/provider-research-system.git
cd provider-research-system/provider-research-skill

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database (automated)
chmod +x scripts/setup_postgres.sh
./scripts/setup_postgres.sh

# Or manual PostgreSQL setup
createdb providers
createuser provider_admin -P  # Enter password: provider123
psql -d providers -c "GRANT ALL PRIVILEGES ON DATABASE providers TO provider_admin;"

# Initialize database schema
python3 setup_postgres_schema.py

# (Optional) Import sample data
python3 import_to_postgres.py
```

## Usage

### Option 1: LLM-Integrated Research (Conversational)

```python
from provider_research import ProviderResearchLLM, ProviderDatabasePostgres
# or
from provider_research.core import ProviderResearchLLM
from provider_research.database import ProviderDatabasePostgres

db = ProviderDatabasePostgres()
research = ProviderResearchLLM(db=db)

result = research.process_query(
    user_query="Find Home Instead in Boston, MA",
    user_context={"location": "New York, NY"}
)

print(result['results'])
```

### With Conversation Context

```python
result = research.process_query(
    user_query="What about their other locations?",
    conversation_history=[
        {"role": "user", "content": "Find Home Instead in Boston"},
        {"role": "assistant", "content": "Found Home Instead - Metrowest..."}
    ]
)
```

### Individual Layers

```python
# Layer 0: Interpretation only
parsed = research.interpret_query("Find CK near me", user_context={"location": "Detroit, MI"})

# Layer 2: Semantic matching only
matches = research.semantic_match("Comfort Keepers", {"state": "MI"})

# Layer 3: Data extraction only
locations = research.extract_locations(html_content, "Home Instead", state="MA")

# Layer 4: Deduplication only
unique, report = research.deduplicate_locations(raw_locations)

# Layer 5: NPI matching only
npi_match = research.match_to_npi(provider_info, npi_search_results)
```

---

### Option 2: Standalone Tools (Data Pipeline)

#### 1. Enrich & Deduplicate Provider Data

Process provider data through web research and smart deduplication:

```bash
python3 -m tools.enrich_and_deduplicate
# or from tools directory:
cd tools && python3 enrich_and_deduplicate.py
```

**Features:**
- Classifies healthcare providers vs real estate companies
- Web scrapes for missing information (NPI, addresses, phones, websites)
- Smart deduplication using phone and address matching
- Detects relationships (parent companies, DBAs, franchises)
- Outputs cleaned data to `data/db_state_cleaned.json`

**Configuration:**
```python
# Edit tools/enrich_and_deduplicate.py to enable real web scraping
researcher = ProviderWebResearcher(use_real_scraping=True)  # Line 36
```

#### 2. Setup PostgreSQL Database

Automated setup (macOS with Homebrew):

```bash
chmod +x scripts/setup_postgres.sh
./scripts/setup_postgres.sh
```

Create optimized schema with full-text search:

```bash
python3 -m tools.setup_postgres_schema
# or
cd tools && python3 setup_postgres_schema.py
```

**Creates:**
- `providers` table (31 columns, 8 indexes)
- `search_history` table (query tracking)
- `provider_history` table (change tracking)
- Full-text search with auto-updating tsvector
- Optimized indexes for name, NPI, phone, location searches

#### 3. Import Provider Data

Import cleaned JSON data into PostgreSQL:

```bash
python3 -m tools.import_to_postgres
# or
cd tools && python3 import_to_postgres.py
```

**Handles:**
- Data validation and sanitization
- NPI placeholder filtering
- JSONB serialization for complex fields
- Duplicate detection

#### 4. Search Providers (CLI)

Interactive search:

```bash
python3 -m tools.search_postgres
# or
cd tools && python3 search_postgres.py
```

Search with query:

```bash
# Basic search
python3 -m tools.search_postgres "Home Instead"

# Search in specific state
python3 -m tools.search_postgres "Comfort Keepers" MI

# Full-text search across all fields
python3 -m tools.search_postgres "senior care" --fulltext
```

**Search Features:**
- Full-text search with relevance ranking
- Pattern matching (ILIKE)
- State and city filtering
- Shows: legal name, DBAs, address, phone, parent org, franchise ID

**Example Output:**
```
Found 2 providers matching "Home Instead":

1. Home Instead - Metrowest
   DBAs: Home Instead Senior Care
   Address: 89 Linden St, Suite 200, Wellesley, MA 02482
   Phone: (781) 555-0123
   Website: https://homeinstead.com/metrowest
   Parent: Home Instead, Inc.
   
2. Home Instead Senior Care of Boston
   Address: 120 Beacon St, Boston, MA 02116
   Phone: (617) 555-0456
   ...
```

---

## Database Schema

### providers

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| npi | VARCHAR(10) | National Provider Identifier |
| legal_name | TEXT | Official business name |
| dba_names | JSONB | "Doing Business As" names |
| address_* | TEXT/VARCHAR | Location fields |
| phone | VARCHAR(20) | Contact number |
| parent_organization | TEXT | Parent company |
| raw_search_data | JSONB | Original search results |

### search_history

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| provider_id | UUID | FK to providers |
| search_query | TEXT | User's search term |
| match_found | BOOLEAN | Whether match was found |
| match_method | TEXT | exact/fuzzy/semantic |

### research_sessions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| provider_name | TEXT | Provider being researched |
| state | VARCHAR(2) | Target state |
| status | TEXT | in_progress/completed |

## Testing

```bash
# Run all tests
python3 test_provider_research_llm.py

# Expected output:
# Total:   22
# Passed:  22
# Failed:  0
```

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Prompt Interpretation | 8 | Query parsing, pronoun resolution |
| Semantic Matching | 3 | Abbreviations, parent/child matching |
| Data Extraction | 2 | HTML and unstructured text |
| Deduplication | 3 | Phone, address, franchise logic |
| NPI Matching | 3 | Exact, fuzzy, no-match cases |
| End-to-End | 3 | Full pipeline flows |

## File Structure

```
provider-research-skill/
├── README.md                        # This file
├── docs/                            # Documentation
│   ├── architecture/                # Architecture docs
│   ├── guides/                      # Setup and usage guides
│   └── getting-started.md           # Quick start
├── requirements.txt                 # Python dependencies
├── provider_research/               # Main package
├── provider_database_sqlite.py      # SQLite alternative (lightweight)
├── provider_search.py               # Rule-based fuzzy search
└── test_provider_research_llm.py    # Comprehensive test suite
```

## Token Economics

| Scenario | Tokens Used |
|----------|-------------|
| Found in database | ~800 (interpretation only) |
| Needs semantic matching | ~1,300 |
| Full web research | ~5,000-10,000 |
| Query needs clarification | ~800 |

## Configuration

### Database Connection

```python
# Default config
config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}

db = ProviderDatabasePostgres(config)
```

### With Anthropic API (Production)

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")
research = ProviderResearchLLM(db=db, llm_client=client)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python3 test_provider_research_llm.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for use with [Claude AI](https://anthropic.com/claude)
- Uses [CMS NPI Registry](https://npiregistry.cms.hhs.gov/) for provider validation
- PostgreSQL for robust data storage
