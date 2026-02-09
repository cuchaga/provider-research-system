# Provider Research Skill - LLM Enhanced

## Overview

A comprehensive healthcare provider research system with intelligent LLM layers for:
- **Prompt interpretation** - Understands natural language queries, resolves references
- **Semantic matching** - Finds providers beyond simple string matching
- **Data extraction** - Extracts structured data from unstructured web content
- **Smart deduplication** - Handles edge cases in duplicate detection
- **NPI matching** - Intelligently matches providers to NPI registry records

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY                                         │
│         "Find healthcare providers at the GCP REIT properties"               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 0: LLM PROMPT INTERPRETATION (~800 tokens)                            │
│                                                                              │
│  • Understands user intent (search, add, compare, list, research)           │
│  • Resolves pronouns: "this", "that", "they" → actual entities              │
│  • Extracts entities: provider names, locations, addresses                  │
│  • Creates multi-step execution plan for complex queries                    │
│  • Asks for clarification when query is ambiguous                           │
│                                                                              │
│  Example transformations:                                                    │
│  • "Find them near me" → "Find [last provider] in [user location]"          │
│  • "Add that to the database" → "Add [last result] to database"             │
│  • "What about New York?" → "Search [same provider] in NY"                  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATABASE SEARCH (0 tokens - rule-based)                            │
│                                                                              │
│  • Exact SQL match on name, NPI, phone                                      │
│  • Levenshtein fuzzy match > 80%                                            │
│  • Full-text search on PostgreSQL                                           │
│  • Returns immediately if high-confidence match found                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                      Found?     │
                 ┌───────────────┼───────────────┐
                 │ YES           │               │ NO / LOW CONFIDENCE
                 ▼               │               ▼
            ┌────────┐           │    ┌──────────────────────────────────────┐
            │ RETURN │           │    │  LAYER 2: SEMANTIC MATCHING          │
            │ RESULT │           │    │  (~500 tokens)                       │
            └────────┘           │    │                                      │
                                 │    │  • Abbreviation expansion            │
                                 │    │    (CK → Comfort Keepers)            │
                                 │    │  • Parent/subsidiary matching        │
                                 │    │  • DBA name resolution               │
                                 │    │  • Regional variation handling       │
                                 │    └─────────────┬────────────────────────┘
                                 │                  │
                                 │       Found?     │
                                 │    ┌─────────────┼─────────────┐
                                 │    │ YES         │             │ NO
                                 │    ▼             │             ▼
                                 │ ┌────────┐       │    ┌────────────────────┐
                                 │ │ RETURN │       │    │  LAYER 3: WEB      │
                                 │ │ RESULT │       │    │  RESEARCH          │
                                 │ └────────┘       │    │  (~5,000+ tokens)  │
                                 │                  │    │                    │
                                 │                  │    │  • Web search      │
                                 │                  │    │  • LLM extraction  │
                                 │                  │    │  • Deduplication   │
                                 │                  │    │  • NPI matching    │
                                 │                  │    └────────────────────┘
                                 │                  │
                                 └──────────────────┘
```

## Layer Details

### Layer 0: Prompt Interpretation

**Purpose:** Transform natural language into structured execution plan.

**Handles:**
| User Says | Interpretation |
|-----------|---------------|
| "Find GCP REIT at that Michigan address" | {provider: "GCP REIT IV", address: "4200 W Utica Rd, MI 48317"} |
| "What about their other locations?" | {provider: [last_provider], intent: "list_all_locations"} |
| "Home Instead near me" | {provider: "Home Instead", location: [user_location]} |
| "Add that to the database" | {intent: "add", data: [last_result]} |
| "Compare Comfort Keepers vs Visiting Angels" | {intent: "compare", providers: ["Comfort Keepers", "Visiting Angels"]} |

**Output Structure:**
```python
{
    "intent": "search|add|compare|list|research|clarify",
    "providers": [{"name": "...", "location": "...", "address": "..."}],
    "filters": {"state": "MI", "city": "Detroit", "type": "Home Health"},
    "references_resolved": {"this": "GCP REIT IV", "they": "Pine Ridge"},
    "multi_step_plan": ["Find GCP properties", "Search for SNFs at addresses"],
    "clarification_needed": null,
    "confidence": 0.95
}
```

**Token Cost:** ~800 tokens per query

---

### Layer 1: Database Search (Rule-Based)

**Purpose:** Fast lookup with zero LLM tokens.

**Methods:**
1. Exact NPI match
2. Exact name match (case-insensitive)
3. SQL LIKE pattern match
4. PostgreSQL full-text search
5. Levenshtein distance > 80%

**Token Cost:** 0 tokens

---

### Layer 2: Semantic Matching

**Purpose:** Find matches that rule-based search misses.

**Handles:**
| Search Query | Database Record | Rule-Based | LLM Semantic |
|--------------|-----------------|------------|--------------|
| "Comfort Keepers" | "CK Home Care LLC" | ❌ 15% | ✅ "CK = Comfort Keepers" |
| "Home Instead" | "Home Instead Senior Care of Boston" | ❌ 65% | ✅ "Same organization" |
| "Visiting Angels" | "VA Healthcare Services" | ❌ 20% | ✅ "VA = Visiting Angels in context" |
| "BrightStar Care" | "BRIGHTSTAR CARE OF MACOMB" | ✅ 75% | ✅ "Exact match, different case" |

**Token Cost:** ~500 tokens (only when Layer 1 fails)

---

### Layer 3: Web Research + LLM Extraction

**Purpose:** Extract structured data from unstructured web content.

**Traditional Approach (BeautifulSoup):**
```python
# Breaks when HTML structure changes
soup.find_all('div', class_='location-card')
```

**LLM-Enhanced Approach:**
```python
prompt = f"""
Extract all {provider_name} locations from this HTML:
{html_content}

Return JSON with: name, address, city, state, zip, phone
"""
# Works regardless of HTML structure
```

**Benefits:**
- Handles varied website structures
- Extracts from poorly formatted pages
- Understands context ("Call us at..." vs "Fax:")
- No custom parsers needed per website

**Token Cost:** ~2,000 tokens per page

---

### Layer 4: Smart Deduplication

**Purpose:** Identify duplicates that rules miss.

**Rule-Based (Fast):**
- Same phone number → Duplicate
- Same normalized address → Duplicate

**LLM-Enhanced (Edge Cases):**
| Scenario | Rule-Based | LLM |
|----------|------------|-----|
| "Suite 201" vs "Suite 305" same building | ❓ Depends | ✅ "Same building = duplicate" |
| Similar names, same city, no phone | ❌ Miss | ✅ "Likely same organization" |
| Franchise vs Corporate | ❌ Miss | ✅ "Different entities" |

**Token Cost:** ~1,000 tokens (only for ambiguous cases)

---

### Layer 5: NPI Matching Intelligence

**Purpose:** Match provider to NPI registry when names don't align.

**Problem:** Business names often differ from NPI registered names.

**Example:**
- Searching for: "Comfort Keepers of Oakland County"
- NPI Registry has: "CK FRANCHISING INC" or "COMFORT KEEPERS #547"

**LLM Matching:**
```python
{
    "best_match": {
        "npi": "1234567890",
        "confidence": 0.95,
        "reasoning": "Franchise number #547 matches Oakland County territory"
    }
}
```

**Token Cost:** ~500 tokens

---

## Token Cost Summary

| Layer | When Used | Tokens |
|-------|-----------|--------|
| 0: Interpretation | Always | ~800 |
| 1: Database | Always | 0 |
| 2: Semantic | When Layer 1 fails | ~500 |
| 3: Extraction | Web research | ~2,000/page |
| 4: Deduplication | Edge cases only | ~1,000 |
| 5: NPI Matching | Fuzzy matches | ~500 |

**Typical Query Costs:**
- Found in database: ~800 tokens (interpretation only)
- Semantic match needed: ~1,300 tokens
- Full web research: ~5,000-10,000 tokens

---

## Usage

### Basic Query
```python
from provider_research_llm import ProviderResearchLLM

research = ProviderResearchLLM(db=db_connection)

result = research.process_query(
    user_query="Find Home Instead in Boston",
    user_context={"location": "Boston, MA"}
)
```

### With Conversation History
```python
result = research.process_query(
    user_query="What about their other locations?",
    conversation_history=[
        {"role": "user", "content": "Find Home Instead in Boston"},
        {"role": "assistant", "content": "Found Home Instead - Metrowest..."}
    ],
    user_context={"location": "Boston, MA"}
)
```

### Individual Layers
```python
# Just interpretation
parsed = research.interpret_query("Find CK near me", user_context={"location": "Detroit, MI"})

# Just semantic matching
matches = research.semantic_match("Comfort Keepers", {"state": "MI"})

# Just extraction
locations = research.extract_locations(html_content, "Home Instead", state="MA")

# Just deduplication
unique, report = research.deduplicate_locations(raw_locations)

# Just NPI matching
npi_match = research.match_to_npi(provider_info, npi_search_results)
```

---

## Files

```
/mnt/skills/user/provider-research/
├── SKILL.md                        # This documentation
├── ORCHESTRATION.md                # Workflow orchestration
├── provider_research_llm.py        # LLM-enhanced module (NEW)
├── provider_database_postgres.py   # PostgreSQL database
├── provider_search.py              # Rule-based fuzzy search
├── README.md                       # General documentation
└── requirements.txt                # Dependencies
```

---

## When to Use Each Layer

| Scenario | Layers Used | Tokens |
|----------|-------------|--------|
| User asks clear question, found in DB | 0 → 1 | ~800 |
| User uses pronouns/references | 0 → 1 | ~800 |
| Query uses abbreviations | 0 → 1 → 2 | ~1,300 |
| Not in database, need web research | 0 → 1 → 2 → 3 | ~5,000+ |
| Complex comparison query | 0 → multi-step execution | ~2,000+ |
| Ambiguous query | 0 → clarification | ~800 |

---

## Best Practices

1. **Always start with Layer 0** - Even clear queries benefit from structured interpretation
2. **Let Layer 1 handle most queries** - Rule-based is fast and free
3. **Use Layer 2 for fuzzy cases** - Only invoke when string matching is <70%
4. **Cache extraction results** - Web content rarely changes, save tokens
5. **Batch NPI lookups** - One LLM call can match multiple providers

---

## Future Enhancements

- [ ] Fine-tuned embedding model for Layer 2 (faster semantic matching)
- [ ] Cached prompt templates (reduce interpretation tokens)
- [ ] Streaming extraction for large pages
- [ ] Multi-provider comparison in single LLM call
- [ ] Learning from user corrections
