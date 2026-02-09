# Provider Research Skill - Complete Project Context

## PURPOSE OF THIS FILE
This file contains all context needed to continue development in a new chat session.
Upload this file along with the project zip to resume work seamlessly.

---

## PROJECT OVERVIEW

**Name:** Provider Research Skill
**Version:** 1.0.0
**Status:** ✅ Complete - Ready for GitHub
**Tests:** 22/22 Passing

### What It Does
An LLM-enhanced healthcare provider research system for Claude AI that:
- Interprets natural language queries with pronoun resolution
- Searches databases with rule-based and semantic matching
- Extracts structured data from unstructured web content
- Deduplicates with intelligent edge case handling
- Validates against NPI registry

---

## ARCHITECTURE SUMMARY

```
Layer 0: Prompt Interpretation    (~800 tokens)   - Always runs
Layer 1: Database Search          (0 tokens)      - Rule-based, can short-circuit
Layer 2: Semantic Matching        (~500 tokens)   - LLM, can short-circuit  
Layer 3: Web Research             (~2-5K tokens)  - LLM extraction
Layer 4: Deduplication            (~1K tokens)    - Rule + LLM edge cases
Layer 5: NPI Validation           (~500 tokens)   - Registry + LLM matching
```

### Token Costs by Path
- Path 1 (Found in DB): ~800 tokens
- Path 2 (Semantic Match): ~1,300 tokens
- Path 3 (Full Research): ~5,800 tokens

---

## FILE INVENTORY

### Core Python Modules
| File | Size | Purpose |
|------|------|---------|
| `provider_research_llm.py` | 32KB | Main LLM-enhanced module with 6 layers |
| `provider_database_postgres.py` | 23KB | PostgreSQL database operations |
| `provider_database_sqlite.py` | 16KB | SQLite alternative (lightweight) |
| `provider_search.py` | 5.5KB | Rule-based fuzzy search |
| `test_provider_research_llm.py` | 45KB | Comprehensive test suite |

### Documentation
| File | Size | Purpose |
|------|------|---------|
| `README.md` | 12KB | GitHub-ready documentation |
| `ARCHITECTURE.md` | 18KB | Complete architecture specification |
| `SKILL.md` | 16KB | Claude skill instructions (LLM-enhanced) |
| `ORCHESTRATION.md` | 29KB | Workflow orchestration guide |
| `TEST_CASES.md` | 19KB | Detailed test specifications |

### Configuration
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `setup.py` | Package installer |
| `__init__.py` | Package exports |
| `.gitignore` | Git exclusions |
| `LICENSE` | MIT License |
| `scripts/init_database.sh` | Database setup script |

### Diagrams
| File | Purpose |
|------|---------|
| `docs/architecture-diagram.html` | Interactive visual diagram |
| `docs/architecture-diagram.mermaid` | Mermaid flowchart |

---

## DATABASE STATE

### Current Test Data (8 providers)
```
1. Home Instead - Metrowest (Wellesley, MA)
2. Home Instead Senior Care of Boston (Boston, MA)
3. Comfort Keepers of Oakland County (Troy, MI)
4. CK Franchising Inc (Troy, MI)
5. Visiting Angels of Boston (Boston, MA)
6. Visiting Angels of Detroit (Detroit, MI)
7. BrightStar Care of Macomb (Sterling Heights, MI)
8. GCP REIT IV (Chicago, IL) - from earlier session
```

### Database Schema (PostgreSQL)
```sql
-- Main tables
providers (id, npi, legal_name, dba_names, address_*, phone, parent_organization, ...)
search_history (id, provider_id, search_query, match_found, match_method, ...)
research_sessions (id, provider_name, state, status, token_cost, ...)
```

---

## TEST RESULTS (All Passing)

### Category 1: Prompt Interpretation (8 tests)
- ✅ 1.1: Simple direct query
- ✅ 1.2: Pronoun resolution ("their")
- ✅ 1.3: "Near me" resolution
- ✅ 1.4: "That" reference resolution
- ✅ 1.5: Comparison query
- ✅ 1.6: Ambiguous query (needs clarification)
- ✅ 1.7: Multi-step complex query
- ✅ 1.8: Address reference from context

### Category 2: Semantic Matching (3 tests)
- ✅ 2.1: Abbreviation expansion (CK → Comfort Keepers)
- ✅ 2.2: Parent/subsidiary match
- ✅ 2.3: No false positives

### Category 3: Data Extraction (2 tests)
- ✅ 3.1: Clean HTML extraction
- ✅ 3.2: Messy/unstructured content

### Category 4: Deduplication (3 tests)
- ✅ 4.1: Same phone = duplicate
- ✅ 4.2: Same address, different suite = duplicate
- ✅ 4.3: Franchise vs corporate = NOT duplicate

### Category 5: NPI Matching (3 tests)
- ✅ 5.1: Exact business name match
- ✅ 5.2: Fuzzy business name match
- ✅ 5.3: No good match (doesn't force)

### Category 6: End-to-End (3 tests)
- ✅ 6.1: Full pipeline - found in database
- ✅ 6.2: Full pipeline - uses semantic matching
- ✅ 6.3: Suggests web research when not found

---

## KEY FEATURES IMPLEMENTED

### Layer 0: Prompt Interpretation
```python
# Handles queries like:
"Find Home Instead near me"           → resolves to user's location
"What about their other locations?"   → resolves "their" from context
"Add that to the database"            → resolves "that" to last result
"Compare CK vs Visiting Angels"       → extracts both providers
```

### Layer 2: Semantic Matching
```python
# Expands abbreviations:
"CK" → "Comfort Keepers"
"HI" → "Home Instead"
"VA" → "Visiting Angels" (in healthcare context)

# Matches parent/subsidiary:
"Home Instead" → finds "Home Instead - Metrowest"
```

### Layer 4: Deduplication Logic
```python
# DUPLICATE cases:
- Same phone number, different address
- Same address, different suite/unit number

# NOT DUPLICATE cases:
- Franchise location vs Corporate HQ
- Different physical locations of same org
```

---

## USAGE EXAMPLES

### Basic Search
```python
from provider_research_llm import ProviderResearchLLM
from provider_database_postgres import ProviderDatabasePostgres

db = ProviderDatabasePostgres()
research = ProviderResearchLLM(db=db)

result = research.process_query(
    user_query="Find Home Instead in Boston, MA",
    user_context={"location": "New York, NY"}
)
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

### Individual Layer Access
```python
# Layer 0 only
parsed = research.interpret_query("Find CK near me", user_context={"location": "Detroit, MI"})

# Layer 2 only
matches = research.semantic_match("Comfort Keepers", {"state": "MI"})

# Layer 4 only
unique, report = research.deduplicate_locations(raw_locations)
```

---

## CONFIGURATION

### Database Connection
```python
config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}
```

### Environment Variables
```bash
DATABASE_URL=postgresql://provider_admin:provider123@localhost:5432/providers
ANTHROPIC_API_KEY=sk-ant-...  # For production LLM calls
FUZZY_MATCH_THRESHOLD=0.8
SEMANTIC_MATCH_THRESHOLD=0.7
```

---

## NEXT STEPS / TODO

### Completed ✅
- [x] Core LLM-enhanced module
- [x] PostgreSQL database layer
- [x] All 6 processing layers
- [x] Test suite (22 tests)
- [x] Architecture documentation
- [x] Interactive diagram
- [x] GitHub-ready package

### Future Enhancements
- [ ] Fine-tuned embedding model for Layer 2
- [ ] Cached prompt templates
- [ ] Streaming extraction for large pages
- [ ] Learning from user corrections
- [ ] Rate limiting for NPI API
- [ ] Batch processing for multiple providers

---

## HOW TO CONTINUE DEVELOPMENT

### Option 1: Upload Files
1. Upload `provider-research-skill.zip`
2. Upload this `PROJECT_CONTEXT.md` file
3. Ask Claude to extract and continue

### Option 2: Quick Start Commands
```bash
# Extract project
unzip provider-research-skill.zip
cd provider-research-skill

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL
sudo service postgresql start

# Run tests
python3 test_provider_research_llm.py

# Initialize database (if needed)
bash scripts/init_database.sh
```

### Option 3: Key Code Locations
- Main entry point: `provider_research_llm.py` → `ProviderResearchLLM.process_query()`
- LLM prompts: `provider_research_llm.py` → `INTERPRETATION_PROMPT`, `SEMANTIC_MATCH_PROMPT`, etc.
- Database operations: `provider_database_postgres.py` → `ProviderDatabasePostgres`
- Tests: `test_provider_research_llm.py` → `run_tests()`

---

## CONVERSATION HISTORY SUMMARY

### Session Accomplishments
1. **Discussed** provider research requirements and architecture
2. **Created** LLM-enhanced module with 6 processing layers
3. **Implemented** prompt interpretation with pronoun resolution
4. **Built** semantic matching for abbreviations and parent/child relationships
5. **Developed** smart deduplication with edge case handling
6. **Added** NPI registry integration with fuzzy matching
7. **Created** comprehensive test suite (22 tests, all passing)
8. **Documented** architecture with interactive diagrams
9. **Packaged** for GitHub with README, LICENSE, setup.py

### Key Design Decisions
1. **Layer 0 always runs** - interpretation is cheap and essential
2. **Layer 1 is rule-based** - 0 tokens for most queries
3. **Short-circuit design** - stop as soon as good match found
4. **Simulated LLM for tests** - allows testing without API calls
5. **PostgreSQL primary** - SQLite available as lightweight alternative

---

## CONTACT / ATTRIBUTION

Created for healthcare provider research automation.
MIT License - Free to use and modify.

Last Updated: February 2025
