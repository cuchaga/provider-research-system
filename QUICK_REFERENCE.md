# Provider Research Skill - Quick Reference

## 🚀 QUICK START FOR NEW CHAT

**Last Updated:** February 9, 2026 (Evening - Latest)  
**Latest Commit:** 2de6f7e  
**Status:** ✅ All tests passing, documentation fully synchronized

### Upload These Files:
1. **`PROJECT_CONTEXT.md`** - Complete project state & architecture
2. **`SESSION_HANDOFF.md`** - What just happened (recent work)
3. **`QUICK_REFERENCE.md`** - This file (quick commands)

### Then Say:
"Let's continue working on the provider research system. I've uploaded the context files."

**Or if you have the zip:**
1. Upload `provider-research-skill.zip`
2. Say: "Extract the zip and review the latest changes"

---

## 📁 PROJECT STRUCTURE (v2.0.0)

```
provider-research-skill/
├── v2.0.0 Multi-Skill Architecture
│   ├── provider_research/
│   │   ├── core/
│   │   │   ├── orchestrator.py           # Main coordinator (22KB, 618 lines)
│   │   │   ├── query_interpreter.py      # Skill 1: NLU (12KB, 354 lines)
│   │   │   ├── semantic_matcher.py       # Skill 3: Matching (12KB, 327 lines)
│   │   │   └── research_llm.py           # Legacy v1.0 (32KB)
│   │   ├── database/
│   │   │   ├── manager.py                # Skill 2: DB Ops (22KB, 680 lines)
│   │   │   ├── postgres.py               # PostgreSQL backend
│   │   │   └── sqlite.py                 # SQLite backend
│   │   ├── search/
│   │   │   ├── web_researcher.py         # Skill 4: Research (23KB, 710 lines)
│   │   │   └── provider_search.py        # Search utilities
│   │   └── utils/                        # Validators, formatters, logger
│   ├── examples/
│   │   ├── basic_usage.py
│   │   └── advanced_orchestration.py
│   └── tests/
│       ├── test_validation.py
│       └── test_file_and_import_integrity.py
│
├── v1.0.0 Legacy (Still Supported)
│   ├── provider_research_llm.py          # Monolithic (32KB)
│   ├── provider_database_postgres.py     # Database (23KB)
│   ├── provider_search.py                # Search (5.5KB)
│   └── test_provider_research_llm.py     # Tests (45KB)
│
├── Documentation
│   ├── README.md                         # Package documentation
│   ├── docs/architecture/                # Architecture docs
│   │   ├── overview.md                   # Technical architecture
│   │   ├── v2-multi-skill.md             # v2.0.0 multi-skill architecture
│   │   └── project-structure.md          # Directory layout
│   └── docs/getting-started.md           # Quick start guide
│
└── Config
    ├── requirements.txt
    ├── setup.py
    └── scripts/init_database.sh
```

---

## 🏗️ ARCHITECTURE AT A GLANCE (v2.0.0)

```
User Query
    ↓
[ORCHESTRATOR] Coordinates all skills
    ↓
[Skill 1] Query Interpreter    ~800 tokens   ← Always runs
    ↓
[Skill 2] Database Manager      0 tokens      ← Can STOP here ✓
    ↓
[Skill 3] Semantic Matcher      ~500 tokens   ← Can STOP here ✓
    ↓
[Skill 4] Web Researcher        ~5000 tokens
    ↓
Results
```

**Execution Paths:**
1. **DB Hit** (~800 tok, ~50ms) - Found in database
2. **Semantic** (~1,300 tok, ~200ms) - Matched via abbreviation/parent
3. **Web Research** (~5,800 tok, ~3-5s) - Deep research needed
4. **Clarification** (~800 tok, <100ms) - Ambiguous query

--v2.0.0 Multi-Skill Tests: 6/6 Passing**
- ✅ Skill imports
- ✅ Component initialization  
- ✅ Query interpretation
- ✅ Semantic matching
- ✅ Web researcher functions
- ✅ Orchestrator structure

**v1.0.0 Legacy Tests: 22/22

## ✅ TEST STATUS

**22/22 Tests Passing**
 (v2.0.0)

### Orchestrator Benefits
- **Modularity**: 4 independent skills vs monolith
- **Token Optimization**: Short-circuits at each layer
- **State Management**: Conversation context & pronoun resolution
- **Error Handling**: Graceful fallbacks & clarifications
- **Backward Compatible**: v1.0.0 code still works

### Understands Natural Language
- "Find Home Instead near me" → uses user's location
- "What about their locations?" → resolves "their" from context
- "Add that to the database" → knows what "that" refers to

### Smart Matching
- "CK" → Comfort Keepers (abbreviation)
- "Home Instead" → finds all subsidiaries
- Won't force matches that don't exist

### Intelligent Deduplication
- Same phone = duplicate
- Same address, diff suite = duplicate
- Franchise vs HQ = NOT duplicate

---

## 💻 COMMON COMMANDS

### v2.0.0 Usage (Recommended)
```python
# Initialize orchestrator
from provider_research_skill import ProviderOrchestrator

orchestrator = ProviderOrchestrator(db_config)
result = orchestrator.process_query(
    user_query="Find Home Instead near me",
    user_context={"location": "Boston, MA"}
)

print(f"Path: {result.execution_path.value}")
print(f"Tokens: {result.token_usage['total']}")
print(f"Providers: {len(result.providers)}")
```

### v1.0.0 Usage (Still Supported)
```python
from provider_research_skill import ProviderResearchLLM

research = ProviderResearchLLM(db_config)
result = research.process_query(user_query)
```

### Run Tests
```bash
# Quick validation tests (v2.0.0)
pytest tests/test_validation.py -v

# Comprehensive tests
pytest tests/ -v --cov=provider_research

# Examples
python3 examples/basic_usage.py
python3 examples/advanced_orchestration.py
```

### Intelligent Deduplication
- Same phone = duplicate
- Same address, diff suite = duplicate
- Franchise vs HQ = NOT duplicate

---

## 💻 COMMON COMMANDS

```bash
# Run tests
python3 test_provider_research_llm.py

# Start database
sudo service postgresql start

# Initialize database
bash scripts/init_database.sh

# Install dependencies
pip install -r requirements.txt
```

---

## 📊 DATABASE INFO

**Connection:**
```
Host: localhost
Port: 5432
Database: providers
User: provider_admin
Password: provider123
```

**Test Data:** 8 providers (Home Instead, Comfort Keepers, Visiting Angels, BrightStar, GCP REIT)

---

## 🎯 QUICK CODE REFERENCE

### Process a Query
```python
from provider_research_llm import ProviderResearchLLM
from provider_database_postgres import ProviderDatabasePostgres

db = ProviderDatabasePostgres()
research = ProviderResearchLLM(db=db)
result = research.process_query("Find Home Instead in MA")
```

### Just Interpret (Layer 0)
```python
parsed = research.interpret_query("Find CK near me", 
    user_context={"location": "Detroit, MI"})
```

### Just Semantic Match (Layer 2)
```python
matches = research.semantic_match("Comfort Keepers", {"state": "MI"})
```

---

## 🔮 FUTURE IDEAS

- [ ] Embedding model for faster semantic search
- [ ] Batch processing for multiple providers
- [ ] Learning from user corrections
- [ ] Rate limiting for external APIs
- [ ] Caching layer for repeated queries

---

## 📝 NOTES FOR CLAUDE

When continuing this project:
1. The test suite uses simulated LLM responses (no API key needed)
2. Database must be running for tests to pass
3. All 6 layers are implemented and working
4. The project is GitHub-ready with full documentation
