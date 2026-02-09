# Provider Research Skill - Quick Reference

## 🚀 QUICK START FOR NEW CHAT

Upload these files to continue:
1. `provider-research-skill.zip` - Complete project
2. `PROJECT_CONTEXT.md` - Full context (this or the one in zip)

Then say: "Extract the zip and let's continue working on the provider research skill"

---

## 📁 PROJECT STRUCTURE

```
provider-research-skill/
├── Core Code
│   ├── provider_research_llm.py      # Main module (32KB)
│   ├── provider_database_postgres.py # Database (23KB)
│   ├── provider_search.py            # Fuzzy search (5.5KB)
│   └── test_provider_research_llm.py # Tests (45KB)
│
├── Documentation
│   ├── README.md                     # GitHub docs
│   ├── ARCHITECTURE.md               # Full architecture
│   ├── PROJECT_CONTEXT.md            # This context file
│   └── docs/architecture-diagram.html # Visual diagram
│
└── Config
    ├── requirements.txt
    ├── setup.py
    └── scripts/init_database.sh
```

---

## 🏗️ ARCHITECTURE AT A GLANCE

```
User Query
    ↓
[Layer 0] Interpretation    ~800 tokens   ← Always runs
    ↓
[Layer 1] Database Search   0 tokens      ← Can STOP here ✓
    ↓
[Layer 2] Semantic Match    ~500 tokens   ← Can STOP here ✓
    ↓
[Layer 3] Web Research      ~3000 tokens
    ↓
[Layer 4] Deduplication     ~1000 tokens
    ↓
[Layer 5] NPI Validation    ~500 tokens
    ↓
Results
```

---

## ✅ TEST STATUS

**22/22 Tests Passing**

| Category | Tests | Status |
|----------|-------|--------|
| Prompt Interpretation | 8 | ✅ |
| Semantic Matching | 3 | ✅ |
| Data Extraction | 2 | ✅ |
| Deduplication | 3 | ✅ |
| NPI Matching | 3 | ✅ |
| End-to-End | 3 | ✅ |

---

## 🔑 KEY CAPABILITIES

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
