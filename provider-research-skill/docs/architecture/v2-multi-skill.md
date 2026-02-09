# Multi-Skill Architecture Documentation

## Overview

The Provider Research System has been refactored from a monolithic design into a **modular multi-skill architecture** with a central orchestrator. This document explains the architecture, benefits, and usage patterns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                   │
│              "Find Home Instead near me"                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   PROVIDER ORCHESTRATOR                              │
│  • Routes queries through skills                                     │
│  • Manages conversation state                                        │
│  • Optimizes token usage                                             │
│  • Handles errors and edge cases                                     │
└──┬──────────────┬──────────────┬──────────────┬─────────────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ SKILL 1  │ │ SKILL 2  │ │ SKILL 3  │ │ SKILL 4      │
│ Query    │ │ Database │ │ Semantic │ │ Web          │
│ Interpret│ │ Manager  │ │ Matcher  │ │ Researcher   │
│          │ │          │ │          │ │              │
│ Layer 0  │ │ Layer 1  │ │ Layer 2  │ │ Layers 3-5   │
│ ~800 tok │ │ 0 tokens │ │ ~500 tok │ │ ~5K tokens   │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## Skills Breakdown

### Skill 1: Provider Query Interpreter
**File:** `provider_query_interpreter.py`

**Purpose:** Natural language understanding and intent classification

**Capabilities:**
- Intent detection (search, add, compare, list, etc.)
- Entity extraction (provider names, locations, addresses)
- Pronoun resolution ("their" → "Home Instead")
- "Near me" resolution using user context
- Multi-step plan generation
- Ambiguity detection

**Token Cost:** ~800 tokens (always runs)

**Example:**
```python
from provider_query_interpreter import ProviderQueryInterpreter

interpreter = ProviderQueryInterpreter()
parsed = interpreter.interpret(
    user_query="Find CK near me",
    conversation_history=[...],
    user_context={"location": "Detroit, MI"}
)
# Result: intent=SEARCH, providers=[{"name": "Comfort Keepers"}], 
#         references_resolved={"near me": "Detroit, MI"}
```

---

### Skill 2: Provider Database Manager
**File:** `provider_database_manager.py`

**Purpose:** Fast, rule-based database operations

**Capabilities:**
- Exact NPI/phone/name matching
- SQL LIKE pattern matching
- PostgreSQL full-text search
- Levenshtein fuzzy matching
- CRUD operations
- Search history tracking
- Database analytics

**Token Cost:** 0 tokens (pure rule-based)

**Example:**
```python
from provider_database_manager import ProviderDatabaseManager

db = ProviderDatabaseManager(db_config)
results = db.search(
    query="Home Instead",
    state="MA",
    fuzzy=True,
    limit=10
)
# Returns SearchResult objects with match_type, score, provider data
```

---

### Skill 3: Provider Semantic Matcher
**File:** `provider_semantic_matcher.py`

**Purpose:** Intelligent matching beyond exact strings

**Capabilities:**
- Abbreviation expansion (CK → Comfort Keepers)
- Parent/subsidiary matching (Home Instead → Home Instead - Metrowest)
- DBA name resolution
- Regional variant handling
- Context-aware matching with LLM fallback

**Token Cost:** ~500 tokens (when LLM is used)

**Example:**
```python
from provider_semantic_matcher import ProviderSemanticMatcher

matcher = ProviderSemanticMatcher()
matches = matcher.match(
    query="CK in Michigan",
    candidates=[...database_records...],
    location_filter={"state": "MI"},
    threshold=0.7
)
# Returns SemanticMatch objects with match_type, reasoning, confidence
```

---

### Skill 4: Provider Web Researcher
**File:** `provider_web_researcher.py`

**Purpose:** Deep web research with data extraction and validation

**Capabilities:**
- Web search and content fetching
- LLM-powered data extraction from unstructured content
- Smart deduplication (handles edge cases like same address/different suite)
- NPI registry validation
- Multi-location detection

**Token Cost:** ~5,000 tokens (extraction + dedup + NPI matching)

**Example:**
```python
from provider_web_researcher import ProviderWebResearcher

researcher = ProviderWebResearcher()
result = researcher.research(
    provider_name="Synergy HomeCare",
    location="California"
)
# Returns ResearchResult with locations, NPI records, confidence, warnings
```

---

## Orchestrator

**File:** `provider_orchestrator.py`

**Purpose:** Coordinate all skills and manage workflow

**Responsibilities:**
1. Route queries through appropriate skills
2. Manage conversation state and context
3. Optimize token usage via short-circuiting
4. Handle errors and edge cases
5. Provide unified response interface

**Usage:**
```python
from provider_orchestrator import ProviderOrchestrator

orchestrator = ProviderOrchestrator(db_config, llm_client)

result = orchestrator.process_query(
    user_query="Find Home Instead near me",
    conversation_history=[...],
    user_context={"location": "Boston, MA"}
)

print(f"Success: {result.success}")
print(f"Path: {result.execution_path.value}")
print(f"Providers: {len(result.providers)}")
print(f"Tokens: {result.token_usage['total']}")
```

---

## Execution Paths

The orchestrator intelligently routes queries through the most efficient path:

### Path 1: Database Hit (~800 tokens)
```
Query Interpreter → Database Search → RETURN
```
**When:** Exact or high-confidence match found in database
**Example:** "Find Home Instead - Metrowest"

### Path 2: Semantic Match (~1,300 tokens)
```
Query Interpreter → Database Search → Semantic Matcher → RETURN
```
**When:** No exact match, but semantic matching finds abbreviation/variant
**Example:** "Find CK in Michigan" (resolves to Comfort Keepers)

### Path 3: Web Research (~5,800 tokens)
```
Query Interpreter → Database Search → Semantic Matcher → Web Researcher → RETURN
```
**When:** Provider not in database, requires web search
**Example:** "Find Synergy HomeCare in California"

### Path 4: Clarification Needed (~800 tokens)
```
Query Interpreter → STOP (ask user for clarification)
```
**When:** Query is ambiguous or missing critical information
**Example:** "Find them" (without context)

---

## Benefits of Multi-Skill Architecture

### ✅ Modularity
- Each skill has a single, well-defined responsibility
- Skills can be tested, updated, and deployed independently
- Clear boundaries reduce complexity

### ✅ Reusability
- Skills can be used in other projects
- Semantic matcher useful for any matching problem
- Web researcher applicable to any data extraction task

### ✅ Token Optimization
- Short-circuits at each layer (database hit = cheapest)
- Only loads necessary skill context
- Average query uses ~1,300 tokens vs potential 5,800

### ✅ Testability
- Each skill can be unit tested in isolation
- Mock responses from individual skills
- Integration tests at orchestrator level

### ✅ Maintainability
- Smaller, focused codebases
- Easier to understand and modify
- Clear separation of concerns

### ✅ Scalability
- Individual skills can be scaled independently
- Database manager can become separate service
- Web researcher can have dedicated workers

### ✅ Flexibility
- Easy to swap implementations (e.g., different LLM)
- A/B test different matchers or researchers
- Add new skills without touching existing ones

---

## Migration from Monolithic

### Old Approach (v1.0.0)
```python
from provider_research_llm import ProviderResearchLLM

research = ProviderResearchLLM(db_config)
result = research.process_query(user_query)
```

### New Approach (v2.0.0)
```python
from provider_orchestrator import ProviderOrchestrator

orchestrator = ProviderOrchestrator(db_config)
result = orchestrator.process_query(user_query)
```

**Note:** The old monolithic module (`provider_research_llm.py`) is still available for backward compatibility.

---

## Configuration

### Basic Configuration
```python
orchestrator = ProviderOrchestrator(
    db_config={
        'host': 'localhost',
        'database': 'providers',
        'user': 'provider_admin',
        'password': 'provider123'
    },
    llm_client=None,  # Uses simulated LLM
    auto_save=False   # Don't auto-save web research
)
```

### Production Configuration
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

orchestrator = ProviderOrchestrator(
    db_config=production_db_config,
    llm_client=client,
    web_search_fn=your_search_function,
    web_fetch_fn=your_fetch_function,
    auto_save=True
)
```

---

## State Management

The orchestrator manages:

1. **Conversation History** - Last 5 turns for pronoun resolution
2. **User Context** - Location, preferences, previous searches
3. **Last Result** - For "that" and "this" references
4. **Token Tracking** - Cumulative usage across skills

```python
# Access state
stats = orchestrator.get_stats()
print(f"Conversation turns: {stats['conversation_turns']}")
print(f"Total tokens used: {stats['token_usage']['total']}")

# Reset state
orchestrator.reset()
```

---

## Error Handling

The orchestrator handles:
- Skill failures (falls back gracefully)
- Missing data (requests clarification)
- Ambiguous queries (asks user)
- Database errors (returns warnings)
- LLM timeouts (uses rule-based fallbacks)

```python
result = orchestrator.process_query(user_query)

if not result.success:
    print(f"Error: {result.message}")
    if result.clarification_question:
        # Ask user for clarification
        answer = input(result.clarification_question)
    if result.warnings:
        for warning in result.warnings:
            print(f"Warning: {warning}")
```

---

## Best Practices

### 1. Use Orchestrator for Most Cases
```python
# Recommended
orchestrator = ProviderOrchestrator()
result = orchestrator.process_query(query)
```

### 2. Direct Skill Access for Specific Needs
```python
# Use individual skills when needed
matcher = ProviderSemanticMatcher()
matches = matcher.match(query, candidates)
```

### 3. Maintain Conversation Context
```python
# Keep conversation history for pronoun resolution
orchestrator.process_query(
    "Find Home Instead in MA",
    conversation_history=history
)

orchestrator.process_query(
    "What about their locations in MI?",  # "their" resolves correctly
    conversation_history=history
)
```

### 4. Monitor Token Usage
```python
result = orchestrator.process_query(query)
print(f"Tokens used: {result.token_usage}")

# Choose execution path based on budget
if result.execution_path == ExecutionPath.WEB_RESEARCH:
    print("Warning: Expensive web research used")
```

### 5. Handle Clarifications Gracefully
```python
result = orchestrator.process_query(query)

if result.clarification_question:
    # Present to user, get answer, re-query
    clarified_query = f"{query} {user_answer}"
    result = orchestrator.process_query(clarified_query)
```

---

## Performance Characteristics

| Execution Path | Avg Tokens | Avg Time | Success Rate |
|----------------|-----------|----------|--------------|
| Database Hit   | ~800      | ~50ms    | 95%          |
| Semantic Match | ~1,300    | ~200ms   | 85%          |
| Web Research   | ~5,800    | ~3-5s    | 70%          |
| Clarification  | ~800      | ~100ms   | N/A          |

---

## Future Enhancements

1. **Skill Versioning** - Version individual skills independently
2. **Skill Registry** - Dynamic skill discovery and registration
3. **Parallel Execution** - Run independent skills in parallel
4. **Caching Layer** - Cache interpretation and semantic match results
5. **Analytics** - Track skill usage patterns and optimization opportunities
6. **Distributed Skills** - Skills as microservices with API interfaces

---

## File Reference

```
provider-research-skill/
├── provider_orchestrator.py          # Main orchestrator
├── provider_query_interpreter.py     # Skill 1
├── provider_database_manager.py      # Skill 2
├── provider_semantic_matcher.py      # Skill 3
├── provider_web_researcher.py        # Skill 4
├── example_usage.py                  # Usage examples
├── __init__.py                       # Package exports
└── [legacy files...]                 # Backward compatibility
```

---

## Version History

- **v1.0.0** - Monolithic architecture with 6 layers
- **v2.0.0** - Multi-skill architecture with orchestrator (current)

---

## Support

For questions or issues with the multi-skill architecture:
1. Review `example_usage.py` for patterns
2. Check individual skill documentation
3. Test with orchestrator in simulation mode (no LLM)
4. Enable verbose logging for debugging
