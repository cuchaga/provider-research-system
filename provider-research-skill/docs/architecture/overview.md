# Provider Research Skill - Architecture Definition

## 1. SYSTEM OVERVIEW

### Purpose
Research, validate, and manage healthcare provider data using a multi-layer intelligent system that combines rule-based efficiency with LLM-powered understanding.

### Core Principles
- **Efficiency First**: Use cheapest/fastest method that works (rule-based before LLM)
- **Progressive Enhancement**: Each layer adds intelligence when simpler methods fail
- **Token Economy**: Minimize LLM token usage while maximizing accuracy
- **Data Quality**: Validate, deduplicate, and enrich all data

---

## 2. COMPONENTS

### 2.1 Data Stores

| Component | Technology | Purpose | Persistence |
|-----------|------------|---------|-------------|
| **Provider Database** | PostgreSQL 16 | Primary data store for validated providers | Permanent |
| **Search History** | PostgreSQL | Track queries and match success rates | Permanent |
| **Research Sessions** | PostgreSQL | Track multi-step research progress | Permanent |
| **Conversation Context** | In-Memory | Store recent conversation for pronoun resolution | Session |
| **Last Result Cache** | In-Memory | Store last query result for "that/this" references | Session |

### 2.2 External Services

| Service | Purpose | Authentication | Rate Limits |
|---------|---------|----------------|-------------|
| **CMS NPI Registry** | Validate provider NPIs | None (public API) | 20 req/sec |
| **Web Search** | Find provider information | Via Claude tools | N/A |
| **Web Fetch** | Retrieve page content | Via Claude tools | N/A |

### 2.3 Processing Modules

| Module | File | Purpose |
|--------|------|---------|
| **ProviderResearchLLM** | `core/research_llm.py` | Legacy v1.0 orchestrator with LLM layers |
| **ProviderOrchestrator** | `core/orchestrator.py` | v2.0 query routing and coordination |
| **ProviderQueryInterpreter** | `core/query_interpreter.py` | Intent parsing and validation |
| **ProviderSemanticMatcher** | `core/semantic_matcher.py` | Semantic search and matching |
| **ProviderDatabaseManager** | `database/manager.py` | Database operations (v2.0) |
| **ProviderDatabasePostgres** | `database/postgres.py` | PostgreSQL backend (v1.0) |
| **ProviderWebResearcher** | `search/web_researcher.py` | Web scraping and data extraction |
| **FuzzySearch** | `search/provider_search.py` | Rule-based string matching |

### 2.4 Standalone Utilities

| Utility | File | Purpose | Dependencies |
|---------|------|---------|-------------|
| **Data Enrichment Pipeline** | `enrich_and_deduplicate.py` | Enrich provider data via web research, classify healthcare vs real estate, smart deduplication | ProviderWebResearcher, ProviderDatabaseManager |
| **PostgreSQL Schema Setup** | `setup_postgres_schema.py` | Create database tables, indexes, full-text search triggers | psycopg2 |
| **Data Import Tool** | `import_to_postgres.py` | Import JSON provider data to PostgreSQL | psycopg2 |
| **CLI Search Interface** | `search_postgres.py` | Command-line provider search with full-text and fuzzy matching | psycopg2 |
| **PostgreSQL Setup Script** | `scripts/setup_postgres.sh` | Automated PostgreSQL installation and configuration | Homebrew (macOS) |
---

## 3. WORKFLOWS

### Workflow A: LLM-Integrated Research (Interactive)

This is the primary workflow for conversational provider research with Claude AI.

#### Stage 1: Query Reception
```
Input: Raw user query + conversation history + user context
Output: Validated input ready for processing
```

**Components Used:**
- Conversation Context (in-memory)
- User Context (location, preferences)

**Actions:**
1. Receive raw query string
2. Load conversation history (last 5 turns)
3. Load user context (location, previous searches)
4. Package for Layer 0

---

### Stage 2: Layer 0 - Prompt Interpretation
```
Input: Raw query + context
Output: ParsedQuery object with structured intent
Tokens: ~800
```

**Components Used:**
- LLM (Claude API or simulated)
- Conversation Context
- Last Result Cache

**Actions:**
1. Analyze query for intent (search, add, compare, list, research)
2. Extract provider names and locations
3. Resolve pronouns ("this", "that", "they", "their")
4. Resolve "near me" to user's location
5. Extract filters (state, city, type)
6. Create multi-step plan if complex
7. Determine if clarification needed

**Output Structure:**
```python
ParsedQuery(
    intent: Intent,              # search, add, compare, list, research, clarify
    providers: List[Dict],       # [{name, location, address}]
    filters: Dict,               # {state, city, type, parent_org}
    references_resolved: Dict,   # {this: "GCP REIT", they: "Home Instead"}
    multi_step_plan: List[str],  # ["Step 1: ...", "Step 2: ..."]
    clarification_needed: str,   # "Which state?" or None
    confidence: float            # 0.0 - 1.0
)
```

**Decision Points:**
- If `clarification_needed` → Return to user, stop processing
- If `intent == "add"` → Go to Add Flow
- If `intent == "compare"` → Go to Compare Flow
- If `intent == "search"` → Continue to Layer 1

---

### Stage 3: Layer 1 - Database Search
```
Input: ParsedQuery with provider name and filters
Output: List of matching providers or empty
Tokens: 0 (rule-based)
```

**Components Used:**
- PostgreSQL Database
- FuzzySearch module
- Full-text search indexes

**Actions:**
1. Try exact NPI match (if NPI provided)
2. Try exact name match (case-insensitive)
3. Try SQL LIKE pattern match
4. Try PostgreSQL full-text search
5. Try Levenshtein fuzzy match (threshold: 80%)
6. Score and rank results

**Decision Points:**
- If match score ≥ 80% → Return results, STOP
- If match score < 80% → Continue to Layer 2

---

### Stage 4: Layer 2 - Semantic Matching
```
Input: Search query + database records
Output: Semantically matched providers
Tokens: ~500
```

**Components Used:**
- LLM (Claude API)
- Provider Database (read)

**Actions:**
1. Load candidate records from database
2. Send to LLM with semantic matching prompt
3. LLM identifies:
   - Abbreviation matches (CK → Comfort Keepers)
   - Parent/subsidiary relationships
   - DBA name matches
   - Regional variations
4. Return ranked matches with reasoning

**Decision Points:**
- If match score ≥ 0.7 → Return results, STOP
- If no good matches → Continue to Layer 3

---

### Stage 5: Layer 3 - Web Research
```
Input: Provider name + location filters
Output: Raw location data from web
Tokens: ~2,000-5,000 per source
```

**Components Used:**
- Web Search tool
- Web Fetch tool
- LLM (for extraction)

**Sub-stages:**

#### 3a. Web Search
```
Action: Search for "[provider] locations [state]"
Output: List of relevant URLs
```

#### 3b. Content Fetching
```
Action: Fetch HTML content from top URLs
Output: Raw HTML/text content
```

#### 3c. LLM Extraction
```
Action: Send content to LLM with extraction prompt
Output: Structured location data
```

**Extracted Fields:**
- franchise_id
- name
- address, city, state, zip
- phone, fax
- website
- services
- hours

---

### Stage 6: Layer 4 - Deduplication
```
Input: Raw extracted locations
Output: Unique locations + dedup report
Tokens: ~1,000 (for edge cases only)
```

**Components Used:**
- Rule-based dedup (first pass)
- LLM (second pass for edge cases)

**Actions:**

#### Pass 1: Rule-Based (Fast)
1. Normalize phone numbers (remove formatting)
2. Normalize addresses (lowercase, remove suite/unit)
3. Flag duplicates by:
   - Exact phone match
   - Exact normalized address match

#### Pass 2: LLM-Enhanced (Edge Cases)
1. Same building, different suite → DUPLICATE
2. Similar names, same city, no phone → Likely DUPLICATE
3. Franchise vs Corporate HQ → NOT DUPLICATE

**Output:**
```python
{
    "unique_locations": [...],
    "duplicates_removed": 5,
    "duplicate_groups": [
        {"keep": "id1", "remove": ["id2", "id3"], "reason": "Same phone"}
    ]
}
```

---

### Stage 7: Layer 5 - NPI Validation
```
Input: Provider info (name, address, phone)
Output: Matched NPI record with confidence
Tokens: ~500
```

**Components Used:**
- NPI Registry API
- LLM (for fuzzy matching)

**Actions:**
1. Search NPI registry by:
   - Organization name
   - City + State
   - Phone (if available)
2. LLM matches provider to NPI results considering:
   - Business name variations
   - Franchise numbers in NPI names
   - Address proximity
   - Phone correlation

**Output:**
```python
{
    "best_match": {
        "npi": "1234567890",
        "confidence": 0.95,
        "reasoning": "Phone matches, same city"
    },
    "alternative_matches": [...]
}
```

---

### Stage 8: Database Storage
```
Input: Validated, deduplicated, NPI-matched providers
Output: Stored provider records
```

**Components Used:**
- PostgreSQL Database

**Actions:**
1. Check for existing record (by NPI or phone)
2. If exists: Update fields, preserve history
3. If new: Insert with full data
4. Store raw data in JSONB for audit
5. Update search history

---

### Stage 9: Response Generation
```
Input: Processing results from all stages
Output: Formatted response to user
```

**Components Used:**
- Result formatter
- Execution trace

**Actions:**
1. Format results based on intent:
   - Search: List of providers with details
   - Compare: Side-by-side comparison
   - Add: Confirmation of added record
   - List: Table of providers
2. Include execution trace (optional)
3. Add suggestions for next actions

---

### Workflow B: Standalone Data Pipeline (Batch Processing)

This workflow operates independently of the LLM system for bulk data enrichment and database management.

#### Pipeline Stage 1: Data Enrichment
```bash
python3 -m tools.enrich_and_deduplicate
# or: cd tools && python3 enrich_and_deduplicate.py
```

**Purpose:** Enrich existing provider data through web research and classification

**Components Used:**
- `ProviderWebResearcher` - Web scraping
- `ProviderDatabaseManager` - Data access
- JSON data files (`data/db_state.json`)

**Actions:**
1. Load providers from JSON database
2. Classify providers (healthcare vs real estate)
3. For each healthcare provider:
   - Search web for official information
   - Extract: NPI, addresses, phone, website, services
   - Validate and normalize data
4. For real estate companies:
   - Move to `real_estate_companies` field of related providers
5. Smart deduplication:
   - Phone-based matching
   - Address normalization
   - Relationship detection (franchise/parent/DBA)
6. Merge duplicates intelligently:
   - Preserve best business name
   - Consolidate DBAs
   - Link parent organizations
7. Output cleaned data to `data/db_state_cleaned.json`

**Deduplication Logic:**
- Same phone + related → Merge
- Same address, different suite → Keep separate (unless phone matches)
- Franchise relationships → Preserve hierarchy

---

#### Pipeline Stage 2: Database Setup
```bash
./scripts/setup_postgres.sh
python3 -m tools.setup_postgres_schema
```

**Purpose:** Initialize PostgreSQL database with optimized schema

**Components Used:**
- PostgreSQL 16
- `setup_postgres_schema.py` - Schema creator

**Actions:**
1. Install PostgreSQL (if needed)
2. Create database and user
3. Create tables:
   - `providers` - Main provider data (31 columns)
   - `search_history` - Search tracking
   - `provider_history` - Historical changes
4. Create indexes:
   - NPI (unique)
   - Legal name (B-tree)
   - Phone (B-tree)
   - State/City (composite)
   - Search vector (GIN for full-text)
5. Configure full-text search:
   - tsvector column with auto-update trigger
   - Searches across name, address, city, services
6. Set up triggers for automatic search vector updates

---

#### Pipeline Stage 3: Data Import
```bash
python3 -m tools.import_to_postgres
```

**Purpose:** Import enriched JSON data into PostgreSQL

**Components Used:**
- `import_to_postgres.py` - Import tool
- Cleaned JSON data

**Actions:**
1. Connect to PostgreSQL database
2. Read `data/db_state_cleaned.json`
3. For each provider:
   - Validate data integrity
   - Filter placeholder NPIs (simulation mode)
   - Serialize JSONB fields (raw_search_data)
   - Insert into `providers` table
4. Report import statistics
5. Handle conflicts (skip duplicates)

**Data Validation:**
- NPI: Filter test values (1234567890 → NULL)
- Arrays: Convert Python lists to PostgreSQL arrays
- JSONB: Serialize raw research data
- Nulls: Handle missing optional fields

---

#### Pipeline Stage 4: Search & Query
```bash
python3 -m tools.search_postgres "provider_name" [STATE]
```

**Purpose:** Search providers via command-line interface

**Components Used:**
- `search_postgres.py` - CLI search
- PostgreSQL full-text search

**Search Methods:**
1. **Full-Text Search** (default)
   - Uses tsvector/tsquery
   - Ranks by relevance (ts_rank)
   - Supports multiple terms

2. **Pattern Matching** (fallback)
   - ILIKE for partial matches
   - Case-insensitive
   - Wildcard support

3. **State/City Filtering**
   - Exact match on state code
   - Optional city filter

**Output:**
- Legal name, DBA names
- Full address
- Phone, website
- Parent organization
- Franchise ID
- Match relevance score

---

## 4. FLOW DIAGRAMS

### 4.1 LLM-Integrated Research Flow

```
┌──────────────┐
│  User Query  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 0: PROMPT INTERPRETATION                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • Parse intent (search/add/compare/list/research)       │ │
│  │ • Extract entities (providers, locations)               │ │
│  │ • Resolve pronouns (this, that, they → entities)        │ │
│  │ • Resolve "near me" → user location                     │ │
│  │ • Create multi-step plan if needed                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│  Tokens: ~800                                                │
└──────────────────────────┬───────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │ Clarification needed?         │
           └───────────────┬───────────────┘
                    │
         ┌──────────┴──────────┐
         │ YES                 │ NO
         ▼                     ▼
┌─────────────────┐   ┌────────────────────────────────────────┐
│ Ask User for    │   │  LAYER 1: DATABASE SEARCH              │
│ Clarification   │   │  ┌──────────────────────────────────┐  │
│ (STOP)          │   │  │ • Exact NPI match                │  │
└─────────────────┘   │  │ • Exact name match               │  │
                      │  │ • SQL LIKE pattern               │  │
                      │  │ • Full-text search               │  │
                      │  │ • Levenshtein fuzzy (>80%)       │  │
                      │  └──────────────────────────────────┘  │
                      │  Tokens: 0 (rule-based)                │
                      └────────────────┬───────────────────────┘
                                       │
                       ┌───────────────┴───────────────┐
                       │ Match found (≥80%)?           │
                       └───────────────┬───────────────┘
                                │
                     ┌──────────┴──────────┐
                     │ YES                 │ NO
                     ▼                     ▼
           ┌─────────────────┐   ┌────────────────────────────────┐
           │ RETURN RESULTS  │   │  LAYER 2: SEMANTIC MATCHING    │
           │ (STOP)          │   │  ┌─────────────────────────┐   │
           └─────────────────┘   │  │ • Abbreviation expansion│   │
                                 │  │   (CK → Comfort Keepers)│   │
                                 │  │ • Parent/subsidiary     │   │
                                 │  │ • DBA name resolution   │   │
                                 │  │ • Regional variations   │   │
                                 │  └─────────────────────────┘   │
                                 │  Tokens: ~500                  │
                                 └────────────────┬───────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  │ Match found (≥0.7)?           │
                                  └───────────────┬───────────────┘
                                           │
                                ┌──────────┴──────────┐
                                │ YES                 │ NO
                                ▼                     ▼
                      ┌─────────────────┐   ┌────────────────────────────┐
                      │ RETURN RESULTS  │   │  LAYER 3: WEB RESEARCH     │
                      │ (STOP)          │   │  ┌──────────────────────┐  │
                      └─────────────────┘   │  │ 3a. Web Search       │  │
                                            │  │ 3b. Content Fetch    │  │
                                            │  │ 3c. LLM Extraction   │  │
                                            │  └──────────────────────┘  │
                                            │  Tokens: ~2,000-5,000      │
                                            └────────────────┬───────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────┐
                                            │  LAYER 4: DEDUPLICATION    │
                                            │  ┌──────────────────────┐  │
                                            │  │ Pass 1: Rule-based   │  │
                                            │  │ • Phone matching     │  │
                                            │  │ • Address normalize  │  │
                                            │  │                      │  │
                                            │  │ Pass 2: LLM (edge)   │  │
                                            │  │ • Same building      │  │
                                            │  │ • Franchise logic    │  │
                                            │  └──────────────────────┘  │
                                            │  Tokens: ~1,000            │
                                            └────────────────┬───────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────┐
                                            │  LAYER 5: NPI VALIDATION   │
                                            │  ┌──────────────────────┐  │
                                            │  │ • NPI Registry search│  │
                                            │  │ • LLM fuzzy matching │  │
                                            │  │ • Confidence scoring │  │
                                            │  └──────────────────────┘  │
                                            │  Tokens: ~500              │
                                            └────────────────┬───────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────┐
                                            │  DATABASE STORAGE          │
                                            │  ┌──────────────────────┐  │
                                            │  │ • Upsert provider    │  │
                                            │  │ • Store raw data     │  │
                                            │  │ • Update history     │  │
                                            │  └──────────────────────┘  │
                                            └────────────────┬───────────┘
                                                             │
                                                             ▼
                                                   ┌─────────────────┐
                                                   │ RETURN RESULTS  │
                                                   └─────────────────┘
```

### 4.2 Token Cost by Path

```
Path 1: Found in Database
────────────────────────────────────
Layer 0 (Interpretation)    ~800 tokens
Layer 1 (Database)             0 tokens
                            ─────────────
TOTAL                       ~800 tokens


Path 2: Needs Semantic Match
────────────────────────────────────
Layer 0 (Interpretation)    ~800 tokens
Layer 1 (Database)             0 tokens
Layer 2 (Semantic)          ~500 tokens
                            ─────────────
TOTAL                     ~1,300 tokens


Path 3: Full Web Research
────────────────────────────────────
Layer 0 (Interpretation)    ~800 tokens
Layer 1 (Database)             0 tokens
Layer 2 (Semantic)          ~500 tokens
Layer 3 (Web Research)    ~3,000 tokens
Layer 4 (Deduplication)   ~1,000 tokens
Layer 5 (NPI Matching)      ~500 tokens
                            ─────────────
TOTAL                     ~5,800 tokens
```

### 4.3 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA STORES                                     │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   PostgreSQL    │  In-Memory      │  External APIs  │  Claude Tools         │
│   ┌───────────┐ │  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐        │
│   │ providers │ │  │ context   │  │  │ NPI       │  │  │ web_search│        │
│   │ history   │ │  │ last_res  │  │  │ Registry  │  │  │ web_fetch │        │
│   │ sessions  │ │  │ user_ctx  │  │  └───────────┘  │  └───────────┘        │
│   └───────────┘ │  └───────────┘  │                 │                       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                    │
         │ R/W             │ R/W             │ Read               │ Read
         │                 │                 │                    │
┌────────┴─────────────────┴─────────────────┴────────────────────┴───────────┐
│                           PROCESSING LAYERS                                  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 0: Prompt Interpretation                                        │   │
│  │   Reads: context, last_result, user_context                          │   │
│  │   Writes: parsed_query                                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 1: Database Search                                              │   │
│  │   Reads: providers, search_history                                    │   │
│  │   Writes: search_history                                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 2: Semantic Matching                                            │   │
│  │   Reads: providers (candidates)                                       │   │
│  │   Writes: none                                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 3: Web Research                                                 │   │
│  │   Reads: web_search results, web_fetch content                        │   │
│  │   Writes: research_sessions                                           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 4: Deduplication                                                │   │
│  │   Reads: raw_locations                                                │   │
│  │   Writes: unique_locations, dedup_report                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 5: NPI Validation                                               │   │
│  │   Reads: NPI Registry API                                             │   │
│  │   Writes: npi_match_result                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Database Storage                                                      │   │
│  │   Writes: providers, search_history, research_sessions               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. DEPENDENCIES

### 5.1 Python Packages

| Package | Version | Purpose | Layer |
|---------|---------|---------|-------|
| psycopg2-binary | ≥2.9.9 | PostgreSQL driver | 1, Storage |
| anthropic | ≥0.18.0 | Claude API client | 0, 2, 3, 4, 5 |
| beautifulsoup4 | ≥4.12.0 | HTML parsing | 3 |
| requests | ≥2.31.0 | HTTP client | 3, 5 |
| python-dateutil | ≥2.8.2 | Date handling | All |

### 5.2 External Services

| Service | Required | Fallback |
|---------|----------|----------|
| PostgreSQL 16 | Yes | SQLite (limited) |
| Claude API | Yes (production) | Simulated (testing) |
| NPI Registry | No | Skip NPI validation |
| Web Search | No | Manual URL input |

### 5.3 Layer Dependencies

```
Layer 0 ─────────────────────────────────────────────────────────────────┐
   │ Depends on: LLM, Conversation Context, User Context                 │
   │ Required for: All subsequent layers                                 │
   ▼                                                                     │
Layer 1 ─────────────────────────────────────────────────────────────────┤
   │ Depends on: PostgreSQL, Layer 0 output                              │
   │ Required for: Quick lookups (can short-circuit here)                │
   ▼                                                                     │
Layer 2 ─────────────────────────────────────────────────────────────────┤
   │ Depends on: LLM, Layer 1 failure, Database records                  │
   │ Required for: Non-obvious matches (can short-circuit here)          │
   ▼                                                                     │
Layer 3 ─────────────────────────────────────────────────────────────────┤
   │ Depends on: Web Search, Web Fetch, LLM, Layer 2 failure             │
   │ Required for: New provider discovery                                │
   ▼                                                                     │
Layer 4 ─────────────────────────────────────────────────────────────────┤
   │ Depends on: Layer 3 output, LLM (optional)                          │
   │ Required for: Data quality                                          │
   ▼                                                                     │
Layer 5 ─────────────────────────────────────────────────────────────────┤
   │ Depends on: NPI Registry API, LLM                                   │
   │ Required for: Official validation                                   │
   ▼                                                                     │
Storage ─────────────────────────────────────────────────────────────────┘
   │ Depends on: PostgreSQL, All layer outputs
   │ Required for: Persistence
```

---

## 6. ERROR HANDLING

### 6.1 Layer-Specific Errors

| Layer | Error | Handling |
|-------|-------|----------|
| 0 | LLM timeout | Retry once, then basic parsing |
| 0 | Invalid JSON response | Fallback to regex extraction |
| 1 | Database connection | Retry 3x, then fail gracefully |
| 2 | No candidates | Skip to Layer 3 |
| 3 | Web search fails | Ask user for direct URL |
| 3 | Page fetch fails | Try alternative URLs |
| 4 | Dedup uncertain | Keep both, flag for review |
| 5 | NPI API down | Skip validation, note in results |

### 6.2 Global Error Handling

```python
try:
    result = research.process_query(query)
except DatabaseError:
    return {"error": "Database unavailable", "suggestion": "Try again later"}
except LLMError:
    return {"error": "AI processing failed", "partial_results": layer1_results}
except NetworkError:
    return {"error": "Network issue", "cached_results": get_cached(query)}
```

---

## 7. CONFIGURATION

### 7.1 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/providers
DB_POOL_SIZE=10

# LLM
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=4000

# Thresholds
FUZZY_MATCH_THRESHOLD=0.8
SEMANTIC_MATCH_THRESHOLD=0.7
DEDUP_CONFIDENCE_THRESHOLD=0.9

# Limits
MAX_WEB_PAGES=5
MAX_LOCATIONS_PER_SEARCH=100
```

### 7.2 Layer Configuration

```python
LAYER_CONFIG = {
    "layer_0": {
        "enabled": True,
        "max_tokens": 1000,
        "timeout_seconds": 30
    },
    "layer_1": {
        "enabled": True,
        "fuzzy_threshold": 0.8,
        "max_results": 50
    },
    "layer_2": {
        "enabled": True,
        "max_tokens": 500,
        "match_threshold": 0.7
    },
    "layer_3": {
        "enabled": True,
        "max_pages": 5,
        "max_tokens_per_page": 2000
    },
    "layer_4": {
        "enabled": True,
        "use_llm_for_edge_cases": True,
        "max_tokens": 1000
    },
    "layer_5": {
        "enabled": True,
        "max_tokens": 500,
        "require_high_confidence": False
    }
}
```
