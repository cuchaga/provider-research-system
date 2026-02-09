# Provider Research LLM - Test Cases

## Overview

This document outlines test cases for validating the LLM-enhanced provider research system.
Each test case includes input, expected behavior, and success criteria.

---

## Test Category 1: Prompt Interpretation (Layer 0)

### Test 1.1: Simple Direct Query
**Input:**
```python
user_query = "Find Home Instead in Boston, MA"
conversation_history = []
user_context = {"location": "New York, NY"}
```

**Expected Output:**
```python
{
    "intent": "search",
    "providers": [{"name": "Home Instead", "location": "Boston, MA"}],
    "filters": {"state": "MA", "city": "Boston"},
    "references_resolved": {},
    "clarification_needed": None,
    "confidence": >= 0.9
}
```

**Success Criteria:**
- ✅ Intent correctly identified as "search"
- ✅ Provider name extracted: "Home Instead"
- ✅ Location extracted: Boston, MA
- ✅ State normalized to "MA"
- ✅ No clarification needed

---

### Test 1.2: Pronoun Resolution ("their")
**Input:**
```python
user_query = "What about their other locations?"
conversation_history = [
    {"role": "user", "content": "Find Home Instead in Boston"},
    {"role": "assistant", "content": "Found Home Instead - Metrowest in Wellesley, MA"}
]
user_context = {}
```

**Expected Output:**
```python
{
    "intent": "search" or "list",
    "providers": [{"name": "Home Instead"}],  # Resolved from context
    "references_resolved": {"their": "Home Instead"},
    "clarification_needed": None
}
```

**Success Criteria:**
- ✅ "their" resolved to "Home Instead" from conversation history
- ✅ Intent is search/list for more locations
- ✅ No clarification needed

---

### Test 1.3: "Near Me" Resolution
**Input:**
```python
user_query = "Find Comfort Keepers near me"
conversation_history = []
user_context = {"location": "Detroit, MI"}
```

**Expected Output:**
```python
{
    "intent": "search",
    "providers": [{"name": "Comfort Keepers", "location": "Detroit, MI"}],
    "filters": {"state": "MI", "city": "Detroit"},
    "references_resolved": {"near me": "Detroit, MI"}
}
```

**Success Criteria:**
- ✅ "near me" resolved to user's location (Detroit, MI)
- ✅ State filter set to MI
- ✅ City filter set to Detroit

---

### Test 1.4: "That" Reference Resolution
**Input:**
```python
user_query = "Add that to the database"
conversation_history = [
    {"role": "user", "content": "Find GCP REIT IV in Michigan"},
    {"role": "assistant", "content": "Found GCP REIT IV at 303 W Madison St, Chicago..."}
]
user_context = {}
# Assume last_result contains GCP REIT IV data
```

**Expected Output:**
```python
{
    "intent": "add",
    "references_resolved": {"that": "GCP REIT IV"},
    "clarification_needed": None
}
```

**Success Criteria:**
- ✅ Intent is "add"
- ✅ "that" resolved to last research result
- ✅ No clarification needed

---

### Test 1.5: Comparison Query
**Input:**
```python
user_query = "Compare Comfort Keepers vs Visiting Angels in Detroit"
conversation_history = []
user_context = {}
```

**Expected Output:**
```python
{
    "intent": "compare",
    "providers": [
        {"name": "Comfort Keepers", "location": "Detroit"},
        {"name": "Visiting Angels", "location": "Detroit"}
    ],
    "filters": {"city": "Detroit"}
}
```

**Success Criteria:**
- ✅ Intent is "compare"
- ✅ Both providers extracted
- ✅ Location filter applied to both

---

### Test 1.6: Ambiguous Query (Needs Clarification)
**Input:**
```python
user_query = "Find that provider"
conversation_history = []  # No context
user_context = {}
```

**Expected Output:**
```python
{
    "intent": "clarify",
    "clarification_needed": "Which provider would you like me to find?"
}
```

**Success Criteria:**
- ✅ Recognizes query is ambiguous
- ✅ Asks for clarification
- ✅ Does NOT proceed with search

---

### Test 1.7: Multi-Step Complex Query
**Input:**
```python
user_query = "Find all skilled nursing facilities at GCP REIT properties in Michigan"
conversation_history = []
user_context = {}
```

**Expected Output:**
```python
{
    "intent": "research",
    "multi_step_plan": [
        "Step 1: Find GCP REIT IV properties in Michigan",
        "Step 2: Get addresses of those properties",
        "Step 3: Search for skilled nursing facilities at each address"
    ],
    "filters": {"state": "MI", "provider_type": "skilled nursing"}
}
```

**Success Criteria:**
- ✅ Recognizes this requires multiple steps
- ✅ Creates logical execution plan
- ✅ Identifies both the real estate owner AND the provider type filter

---

### Test 1.8: Address Reference from Context
**Input:**
```python
user_query = "Search for providers at that address"
conversation_history = [
    {"role": "user", "content": "Find GCP REIT IV in Michigan"},
    {"role": "assistant", "content": "Found Pine Ridge Villas at 4200 W Utica Rd, Shelby Township, MI 48317"}
]
user_context = {}
```

**Expected Output:**
```python
{
    "intent": "search",
    "providers": [{"address": "4200 W Utica Rd, Shelby Township, MI 48317"}],
    "references_resolved": {"that address": "4200 W Utica Rd, Shelby Township, MI 48317"}
}
```

**Success Criteria:**
- ✅ "that address" resolved from conversation
- ✅ Full address extracted correctly

---

## Test Category 2: Semantic Matching (Layer 2)

### Test 2.1: Abbreviation Expansion
**Input:**
```python
search_query = "CK"
database_records = [
    {"id": "1", "legal_name": "Comfort Keepers of Oakland", "address_state": "MI"},
    {"id": "2", "legal_name": "Home Instead Senior Care", "address_state": "MI"},
    {"id": "3", "legal_name": "CK Franchising Inc", "address_state": "MI"}
]
```

**Expected Output:**
```python
{
    "matches": [
        {"id": "3", "name": "CK Franchising Inc", "score": 0.95, "match_type": "abbreviation"},
        {"id": "1", "name": "Comfort Keepers of Oakland", "score": 0.9, "match_type": "abbreviation"}
    ]
}
```

**Success Criteria:**
- ✅ Recognizes "CK" = "Comfort Keepers"
- ✅ Returns both CK-related records
- ✅ Does NOT match "Home Instead"

---

### Test 2.2: Parent/Subsidiary Match
**Input:**
```python
search_query = "Home Instead"
database_records = [
    {"id": "1", "legal_name": "Home Instead - Metrowest", "parent_organization": "Home Instead Inc"},
    {"id": "2", "legal_name": "Home Instead Senior Care of Boston", "parent_organization": "Home Instead Inc"},
    {"id": "3", "legal_name": "Visiting Angels of Boston", "parent_organization": "Visiting Angels"}
]
```

**Expected Output:**
```python
{
    "matches": [
        {"id": "1", "score": 0.95, "match_type": "parent_child"},
        {"id": "2", "score": 0.95, "match_type": "parent_child"}
    ]
}
```

**Success Criteria:**
- ✅ Matches both Home Instead locations
- ✅ Recognizes parent organization relationship
- ✅ Does NOT match Visiting Angels

---

### Test 2.3: No False Positives
**Input:**
```python
search_query = "BrightStar Care"
database_records = [
    {"id": "1", "legal_name": "Comfort Keepers", "address_state": "MI"},
    {"id": "2", "legal_name": "Home Instead", "address_state": "MI"},
    {"id": "3", "legal_name": "Visiting Angels", "address_state": "MI"}
]
```

**Expected Output:**
```python
{
    "matches": [],
    "no_match_reason": "BrightStar Care not found in database records"
}
```

**Success Criteria:**
- ✅ Returns empty matches
- ✅ Does NOT force a match
- ✅ Provides reason for no match

---

## Test Category 3: Data Extraction (Layer 3)

### Test 3.1: Extract from Clean HTML
**Input:**
```python
provider_name = "Home Instead"
state = "MA"
web_content = """
<div class="location">
    <h3>Home Instead - Metrowest</h3>
    <p class="address">65 Central St, Wellesley, MA 02482</p>
    <p class="phone">(781) 237-3636</p>
</div>
<div class="location">
    <h3>Home Instead - Boston</h3>
    <p class="address">123 Main St, Boston, MA 02101</p>
    <p class="phone">(617) 555-0100</p>
</div>
"""
```

**Expected Output:**
```python
{
    "locations": [
        {
            "name": "Home Instead - Metrowest",
            "address": "65 Central St",
            "city": "Wellesley",
            "state": "MA",
            "zip": "02482",
            "phone": "781-237-3636"
        },
        {
            "name": "Home Instead - Boston",
            "address": "123 Main St",
            "city": "Boston",
            "state": "MA",
            "zip": "02101",
            "phone": "617-555-0100"
        }
    ],
    "extraction_confidence": >= 0.9
}
```

**Success Criteria:**
- ✅ Extracts both locations
- ✅ Phone numbers normalized to XXX-XXX-XXXX
- ✅ City/state/zip parsed correctly
- ✅ High confidence score

---

### Test 3.2: Extract from Messy/Unstructured Content
**Input:**
```python
provider_name = "Comfort Keepers"
state = "MI"
web_content = """
Our Locations:
Comfort Keepers of Oakland County serves families in Troy, Rochester, and Birmingham.
Call us today at 248-555-1234 or visit our office at 500 Maple Road, Troy MI 48084.

We also have a location in Macomb County!
Address: 12345 Gratiot Ave, Clinton Township, Michigan 48035
Phone: (586) 555-9876
"""
```

**Expected Output:**
```python
{
    "locations": [
        {
            "name": "Comfort Keepers of Oakland County",
            "address": "500 Maple Road",
            "city": "Troy",
            "state": "MI",
            "zip": "48084",
            "phone": "248-555-1234"
        },
        {
            "name": "Comfort Keepers of Macomb County",
            "address": "12345 Gratiot Ave",
            "city": "Clinton Township",
            "state": "MI",
            "zip": "48035",
            "phone": "586-555-9876"
        }
    ],
    "extraction_confidence": >= 0.7,
    "warnings": ["Location names inferred from context"]
}
```

**Success Criteria:**
- ✅ Extracts from unstructured text
- ✅ Infers location names from context
- ✅ Lower confidence due to ambiguity
- ✅ Includes appropriate warnings

---

## Test Category 4: Deduplication (Layer 4)

### Test 4.1: Same Phone = Duplicate
**Input:**
```python
locations = [
    {"id": "1", "name": "Home Instead #236", "phone": "516-826-6307", "address": "123 Main St"},
    {"id": "2", "name": "Home Instead #379", "phone": "516-826-6307", "address": "456 Oak Ave"},
    {"id": "3", "name": "Home Instead #500", "phone": "212-555-0100", "address": "789 Pine St"}
]
```

**Expected Output:**
```python
{
    "unique_locations": [
        {"id": "1", ...},  # Kept
        {"id": "3", ...}   # Kept
    ],
    "duplicates_found": 1,
    "duplicate_groups": [
        {"keep": "1", "remove": ["2"], "reason": "Same phone number"}
    ]
}
```

**Success Criteria:**
- ✅ Identifies #236 and #379 as duplicates (same phone)
- ✅ Keeps one, removes the other
- ✅ #500 remains (different phone)

---

### Test 4.2: Same Address Different Suite = NOT Duplicate
**Rationale:** Different suite numbers in the same building represent different provider locations. For example, a dentist in Suite 201 and a physical therapist in Suite 305 are separate businesses.

**Input:**
```python
locations = [
    {"id": "1", "name": "Provider A", "phone": "111-111-1111", "address": "19 Merrick Ave Suite 201, Freeport, NY"},
    {"id": "2", "name": "Provider A", "phone": "222-222-2222", "address": "19 Merrick Ave Suite 305, Freeport, NY"},
    {"id": "3", "name": "Provider B", "phone": "333-333-3333", "address": "21 Merrick Ave, Freeport, NY"}
]
```

**Expected Output:**
```python
{
    "unique_locations": [
        {"id": "1", ...},  # Kept (Suite 201)
        {"id": "2", ...},  # Kept (Suite 305 - different suite = different location)
        {"id": "3", ...}   # Kept (different street number)
    ],
    "duplicates_found": 0,
    "notes": "Different suites are considered different provider locations"
}
```

**Success Criteria:**
- ✅ Suite 201 and Suite 305 are NOT duplicates (different locations)
- ✅ All 3 locations kept as unique
- ✅ Only exact address matches (including suite) would be duplicates

---

### Test 4.3: Franchise vs Corporate = NOT Duplicate
**Input:**
```python
locations = [
    {"id": "1", "name": "Home Instead Corporate HQ", "address": "13323 California St, Omaha, NE", "type": "corporate"},
    {"id": "2", "name": "Home Instead #547", "address": "100 Main St, Boston, MA", "type": "franchise"}
]
```

**Expected Output:**
```python
{
    "unique_locations": [
        {"id": "1", ...},
        {"id": "2", ...}
    ],
    "duplicates_found": 0,
    "notes": "Corporate HQ and franchise location are distinct entities"
}
```

**Success Criteria:**
- ✅ Corporate and franchise are NOT duplicates
- ✅ Both kept in unique list

---

## Test Category 5: NPI Matching (Layer 5)

### Test 5.1: Exact Business Name Match
**Input:**
```python
provider_info = {
    "name": "Home Instead Senior Care",
    "address": "65 Central St",
    "city": "Wellesley",
    "state": "MA",
    "phone": "781-237-3636"
}
npi_results = [
    {"npi": "1234567890", "name": "HOME INSTEAD SENIOR CARE", "address": "65 CENTRAL ST, WELLESLEY, MA"},
    {"npi": "0987654321", "name": "VISITING ANGELS", "address": "100 MAIN ST, BOSTON, MA"}
]
```

**Expected Output:**
```python
{
    "best_match": {
        "npi": "1234567890",
        "confidence": 0.98,
        "reasoning": "Name and address match exactly"
    }
}
```

**Success Criteria:**
- ✅ Matches to correct NPI
- ✅ High confidence (>0.95)
- ✅ Provides clear reasoning

---

### Test 5.2: Fuzzy Business Name Match
**Input:**
```python
provider_info = {
    "name": "Comfort Keepers of Oakland County",
    "city": "Troy",
    "state": "MI",
    "phone": "248-555-1234"
}
npi_results = [
    {"npi": "1111111111", "name": "CK FRANCHISING INC", "address": "500 MAPLE RD, TROY, MI", "phone": "248-555-1234"},
    {"npi": "2222222222", "name": "COMFORT KEEPERS #892", "address": "123 OTHER ST, DETROIT, MI"}
]
```

**Expected Output:**
```python
{
    "best_match": {
        "npi": "1111111111",
        "confidence": 0.9,
        "reasoning": "Phone number matches, CK = Comfort Keepers, same city"
    },
    "alternative_matches": [
        {"npi": "2222222222", "confidence": 0.5, "reasoning": "Same brand, different location"}
    ]
}
```

**Success Criteria:**
- ✅ Matches despite different business name format
- ✅ Uses phone number as strong signal
- ✅ Recognizes "CK" abbreviation
- ✅ Provides alternative with lower confidence

---

### Test 5.3: No Good Match
**Input:**
```python
provider_info = {
    "name": "BrightStar Care of Boston",
    "city": "Boston",
    "state": "MA",
    "phone": "617-555-0000"
}
npi_results = [
    {"npi": "1111111111", "name": "HOME INSTEAD", "address": "WELLESLEY, MA"},
    {"npi": "2222222222", "name": "COMFORT KEEPERS", "address": "TROY, MI"}
]
```

**Expected Output:**
```python
{
    "best_match": None,
    "no_match_reason": "No NPI records match BrightStar Care. Search results are for different organizations."
}
```

**Success Criteria:**
- ✅ Returns no match (not forced)
- ✅ Explains why no match found

---

## Test Category 6: End-to-End Pipeline

### Test 6.1: Full Pipeline - Found in Database
**Input:**
```python
user_query = "Find Home Instead in Massachusetts"
# Database contains Home Instead - Metrowest
```

**Expected Flow:**
```
Layer 0: Interpret → intent=search, provider="Home Instead", state="MA"
Layer 1: Database search → FOUND (Home Instead - Metrowest)
→ RETURN RESULT (skip layers 2-5)
```

**Expected Output:**
```python
{
    "results": [{"name": "Home Instead - Metrowest", "city": "Wellesley", ...}],
    "source": "database",
    "execution_trace": ["Layer 0: Interpreted", "Layer 1: Found in database"],
    "tokens_used": ~800  # Only interpretation
}
```

---

### Test 6.2: Full Pipeline - Needs Semantic Match
**Input:**
```python
user_query = "Find CK in Michigan"
# Database contains "Comfort Keepers of Oakland" but not "CK"
```

**Expected Flow:**
```
Layer 0: Interpret → intent=search, provider="CK", state="MI"
Layer 1: Database search → NOT FOUND (no "CK" match)
Layer 2: Semantic match → FOUND (CK = Comfort Keepers)
→ RETURN RESULT
```

**Expected Output:**
```python
{
    "results": [{"name": "Comfort Keepers of Oakland", ...}],
    "source": "semantic_match",
    "execution_trace": ["Layer 0", "Layer 1: Not found", "Layer 2: Semantic match found"],
    "tokens_used": ~1300
}
```

---

### Test 6.3: Full Pipeline - Needs Web Research
**Input:**
```python
user_query = "Find Visiting Angels in Texas"
# Database has no Texas providers
```

**Expected Flow:**
```
Layer 0: Interpret → intent=search, provider="Visiting Angels", state="TX"
Layer 1: Database search → NOT FOUND
Layer 2: Semantic match → NOT FOUND
Layer 3: Web research → Suggest to user
```

**Expected Output:**
```python
{
    "results": None,
    "suggestions": ["Would you like me to search the web for Visiting Angels in Texas?"],
    "execution_trace": ["Layer 0", "Layer 1: Not found", "Layer 2: No semantic match"],
    "tokens_used": ~1300
}
```

---

## Summary: Test Matrix

| Test ID | Category | Description | Layers Tested |
|---------|----------|-------------|---------------|
| 1.1 | Interpretation | Simple direct query | 0 |
| 1.2 | Interpretation | Pronoun resolution ("their") | 0 |
| 1.3 | Interpretation | "Near me" resolution | 0 |
| 1.4 | Interpretation | "That" reference | 0 |
| 1.5 | Interpretation | Comparison query | 0 |
| 1.6 | Interpretation | Ambiguous (needs clarification) | 0 |
| 1.7 | Interpretation | Multi-step complex query | 0 |
| 1.8 | Interpretation | Address from context | 0 |
| 2.1 | Semantic | Abbreviation expansion | 2 |
| 2.2 | Semantic | Parent/subsidiary match | 2 |
| 2.3 | Semantic | No false positives | 2 |
| 3.1 | Extraction | Clean HTML | 3 |
| 3.2 | Extraction | Messy/unstructured | 3 |
| 4.1 | Deduplication | Same phone = duplicate | 4 |
| 4.2 | Deduplication | Same address diff suite | 4 |
| 4.3 | Deduplication | Franchise vs corporate | 4 |
| 5.1 | NPI Match | Exact name match | 5 |
| 5.2 | NPI Match | Fuzzy name match | 5 |
| 5.3 | NPI Match | No good match | 5 |
| 6.1 | End-to-End | Found in database | 0,1 |
| 6.2 | End-to-End | Needs semantic match | 0,1,2 |
| 6.3 | End-to-End | Needs web research | 0,1,2,3 |

---

## Test Execution Plan

### Phase 1: Unit Tests (Individual Layers)
1. Run tests 1.1-1.8 for Layer 0 (Interpretation)
2. Run tests 2.1-2.3 for Layer 2 (Semantic Matching)
3. Run tests 3.1-3.2 for Layer 3 (Extraction)
4. Run tests 4.1-4.3 for Layer 4 (Deduplication)
5. Run tests 5.1-5.3 for Layer 5 (NPI Matching)

### Phase 2: Integration Tests (End-to-End)
1. Run tests 6.1-6.3 with actual database
2. Verify layer transitions work correctly
3. Check token counting accuracy

### Phase 3: Real-World Queries
1. Test with actual provider names
2. Test with actual conversation histories
3. Test with real web content

---

## Approval Checklist

Please confirm the following before I proceed with implementation:

- [ ] Test cases cover all critical functionality
- [ ] Expected outputs are reasonable
- [ ] Success criteria are clear and measurable
- [ ] Test categories are comprehensive
- [ ] Edge cases are adequately covered
- [ ] Any additional test cases needed?

**Your feedback:**
