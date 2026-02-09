# Provider Research Skill - LLM Enhanced

## Overview

A comprehensive healthcare provider research system with intelligent LLM layers for:
- **Prompt interpretation** - Understands natural language queries, resolves references
- **Semantic matching** - Finds providers beyond simple string matching
- **Data extraction** - Extracts structured data from unstructured web content
- **Smart deduplication** - Handles edge cases in duplicate detection
- **NPI matching** - Intelligently matches providers to NPI registry records

## When to Use This Skill
- User requests: "Find all [Provider] locations in [State]"
- Building provider databases or contact lists
- Researching franchise or branch networks
- Comparing provider coverage across regions
- Any task involving counting or cataloging multiple locations

---

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

---

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

**Deduplication Logic: Phone OR Address**

Locations are duplicates if they have:
- **Same phone number**, OR
- **Same address** (normalized)

**NOT:** Require both to match (that's too strict)

```python
def normalize_phone(phone):
    """Normalize phone to digits only for comparison"""
    if not phone:
        return ""
    return ''.join(filter(str.isdigit, phone))

def normalize_address(address):
    """Normalize address for comparison - strip suite/floor, lowercase, remove punctuation"""
    if not address:
        return ""
    addr = address.lower().replace('suite', 'ste').replace('floor', 'fl')
    addr = addr.replace('apartment', 'apt').replace('.', '').replace(',', '')
    addr = ' '.join(addr.split())
    # Extract street address only (ignore suite/floor numbers)
    parts = addr.split()
    street_parts = []
    for part in parts:
        if part in ['ste', 'suite', 'fl', 'floor', 'apt', 'unit', '#']:
            break
        street_parts.append(part)
    return ' '.join(street_parts)

def deduplicate_locations(locations):
    """Remove duplicates based on EITHER phone OR address match"""
    unique = []
    seen_phones = set()
    seen_addresses = set()
    duplicates = []

    sorted_locs = sorted(
        locations,
        key=lambda x: (bool(x.get('phone')), bool(x.get('address'))),
        reverse=True
    )

    for loc in sorted_locs:
        phone = normalize_phone(loc.get('phone', ''))
        address = normalize_address(loc.get('address', ''))
        is_duplicate = False
        dup_reason = []

        if phone and phone in seen_phones:
            is_duplicate = True
            dup_reason.append('phone')
        if address and address in seen_addresses:
            is_duplicate = True
            dup_reason.append('address')

        if is_duplicate:
            duplicates.append({'location': loc, 'reason': ' & '.join(dup_reason)})
        else:
            unique.append(loc)
            if phone: seen_phones.add(phone)
            if address: seen_addresses.add(address)

    return unique, {
        'total_input': len(locations),
        'total_unique': len(unique),
        'total_duplicates': len(duplicates),
        'details': duplicates
    }
```

**Edge Cases:**
| Scenario | Result |
|----------|--------|
| Same phone, missing address | DUPLICATE (phone match) |
| Same address, different suite | DUPLICATE (same street after normalization) |
| Similar but different addresses (19 vs 21 Merrick Ave) | UNIQUE |
| Missing both phone and address | UNIQUE (can't match empty data, flag incomplete) |

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

**Per-Location Costs (detailed research):**

| Task | Tokens | Notes |
|------|--------|-------|
| NPI lookup (individual) | ~1,500 | Search by name + credentials validation |
| NPI lookup (organization) | ~800 | Simpler, just business name |
| Data enrichment | ~1,300 | Address formatting, phone validation, etc. |
| **Total per location** | **~2,800** | Average across mix of individual/org |

**Full Project Estimates:**
- 10 locations: ~28,000 tokens
- 21 locations: ~58,800 tokens
- 50 locations: ~140,000 tokens
- 100 locations: ~280,000 tokens

---

## The 4-Phase Research Workflow

### Critical Rule: NEVER Start Research Without Verified Count

**STOP and verify count BEFORE beginning detailed research on individual locations.**

### Phase 1: Initial Count Verification (MANDATORY)

1. **Extract claimed count from provider website**
   - Search: `"[Provider]" "[State]" "showing * locations"`
   - Look for: "showing X locations", "X offices in [State]"

2. **Find and verify location directory page**
   - Search: `"[Provider]" "[State]" locations directory`
   - If web_search returns fewer than claimed → use web_fetch for complete HTML

3. **Quality Gate:** Do NOT proceed until target count is established.

### Phase 2: Structured Data Extraction

Extract with code (LLM-enhanced), not manual parsing:
```python
prompt = f"""Extract all {provider_name} locations from this HTML:
{html_content}
Return JSON with: franchise_id, name, phone, address"""
```

**Quality Gate:** Extracted count must match claimed count (±10%).

### Phase 3: Cross-Validation

1. Compare extracted vs claimed count
2. Regional verification for major cities
3. Cross-reference with third-party sources (caring.com, etc.)
4. Apply deduplication before user confirmation

**Quality Gate:** Final unique count within 10% of claimed.

### Phase 4: User Confirmation

Present summary for approval before proceeding:

```
RESEARCH SUMMARY: Home Instead - New York
Claimed count (from website): 21
Extracted count (raw):        23
Unique count (after dedup):   21
Duplicates removed:           2
  ✗ Nassau County (#236 & #379) - Duplicate by phone
  ✗ Manhattan (#368 & #515) - Duplicate by phone
Count variance: 0 (0.0%) - ACCEPTABLE
Estimated tokens for 21 locations: ~58,800
Ready to proceed?
```

**Quality Gate:** User must explicitly approve before detailed research.

---

## Search Strategy

### Multi-Source Approach
```python
# Search 1: Get target count
web_search('"Home Instead" "New York" "showing * locations"')

# Search 2: Get complete location list
web_search('"Home Instead" "New York" locations directory')

# Search 3: Regional fill (if gaps found)
web_search('"Home Instead" "Manhattan" location phone')

# Search 4: Third-party validation
web_search('site:caring.com "Home Instead" "New York"')
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

## Quality Gates Summary

| Phase | Gate | Criteria | Action if Failed |
|-------|------|----------|------------------|
| 1 | Count verification | Target count identified from website | Search more, use web_fetch |
| 2 | Extraction completeness | Extracted ≥ 90% of claimed count | Review HTML structure, adjust code |
| 3 | Cross-validation | Unique count within 10% of claimed | Regional searches, third-party sources |
| 4 | User approval | User confirms dataset and token cost | Revise, investigate gaps |

---

## Common Pitfalls & Solutions

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Fragmented search data | web_search returns 3-5 locations, missing full list | Always web_fetch the main directory page |
| Manual counting errors | "I see 14" when there are 21 | Use code to count, never manual |
| Starting research too early | Spend 40K tokens on 14 locations, then find 7 more | Complete all 4 phases first |
| Over-aggressive dedup | Same address, different suite treated as unique | Normalize by stripping suite numbers |
| Under-aggressive dedup | Require phone AND address match | Deduplicate on phone OR address |

---

## Best Practices

1. **Always start with Layer 0** - Even clear queries benefit from structured interpretation
2. **Let Layer 1 handle most queries** - Rule-based is fast and free
3. **Use Layer 2 for fuzzy cases** - Only invoke when string matching <70%
4. **Cache extraction results** - Web content rarely changes, save tokens
5. **Batch NPI lookups** - One LLM call can match multiple providers
6. **Verify counts before researching** - Prevents costly restarts

---

## Files

```
provider-research-skill/
├── SKILL.md                        # This documentation
├── ORCHESTRATION.md                # Workflow orchestration
├── provider_research_llm.py        # LLM-enhanced module
├── provider_database_postgres.py   # PostgreSQL database
├── provider_database_sqlite.py     # SQLite alternative (lightweight)
├── provider_search.py              # Rule-based fuzzy search
├── README.md                       # General documentation
└── requirements.txt                # Dependencies
```

---

## Tools Required

1. **Python 3.10+** with BeautifulSoup for HTML parsing
2. **PostgreSQL 16** (primary) or **SQLite** (lightweight alternative)
3. **web_search** - Multi-source discovery
4. **web_fetch** - Complete page retrieval
5. **NPI Registry** - Provider credential lookup (public API)

---

## Future Enhancements

- [ ] Fine-tuned embedding model for Layer 2 (faster semantic matching)
- [ ] Cached prompt templates (reduce interpretation tokens)
- [ ] Streaming extraction for large pages
- [ ] Multi-provider comparison in single LLM call
- [ ] Learning from user corrections