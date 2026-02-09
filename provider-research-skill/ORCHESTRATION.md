# Provider Research Orchestration Skill

## Purpose
Orchestrate the complete provider research workflow by coordinating between existing database search, web research, and database insertion. This skill ensures a systematic approach: check existing data first, research only when needed, and update the database with user approval.

## When to Use This Skill
- User requests: "Find [Provider] in [Location]"
- User asks: "Do we have data on [Provider]?"
- Building or updating provider databases
- Any provider lookup or research request

## The Orchestration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER REQUEST                                 │
│              "Find Home Instead in Boston, MA"                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: DATABASE SEARCH                                        │
│  • Use provider_search.py fuzzy matching                         │
│  • Check for existing records                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
                  ┌────────┐
                  │ Found? │
                  └────┬───┘
                       │
         ┌─────────────┼─────────────┐
         │YES          │             │NO
         ▼             │             ▼
┌────────────────┐     │    ┌────────────────────────┐
│ PHASE 2A:      │     │    │ PHASE 2B:              │
│ PRESENT MATCH  │     │    │ WEB RESEARCH           │
│ • Show data    │     │    │ • Use provider         │
│ • Ask user:    │     │    │   research skill       │
│   "Is this     │     │    │ • 4-phase workflow     │
│    correct?"   │     │    │ • Get complete data    │
└────────┬───────┘     │    └──────────┬─────────────┘
         │             │               │
         ▼             │               ▼
    ┌────────┐         │        ┌─────────────┐
    │Correct?│         │        │ PHASE 3:    │
    └───┬────┘         │        │ PRESENT     │
        │              │        │ RESULTS     │
  ┌─────┼──────┐       │        │ • Show data │
  │YES  │  NO  │       │        │ • Ask: "Add │
  ▼     │      ▼       │        │   to DB?"   │
┌────┐  │  ┌────────┐  │        └──────┬──────┘
│DONE│  │  │Continue│  │               │
└────┘  │  │to 2B   │  │               ▼
        │  └───┬────┘  │          ┌─────────┐
        │      │       │          │Add to   │
        │      └───────┘          │DB?      │
        │                         └────┬────┘
        │                              │
        │                    ┌─────────┼─────────┐
        │                    │YES               │NO
        │                    ▼                  ▼
        │            ┌───────────────┐    ┌─────────┐
        │            │ PHASE 4:      │    │ DONE    │
        │            │ ADD TO DB     │    │ (data   │
        │            │ • Use database│    │ provided│
        │            │   tool        │    │ only)   │
        │            │ • Confirm     │    └─────────┘
        │            │   success     │
        │            └───────────────┘
        │                    │
        └────────────────────┴──────────────────────────────────────┐
                                                                      ▼
                                                                 ┌────────┐
                                                                 │ DONE   │
                                                                 └────────┘
```

---

## Phase 1: Database Search (ALWAYS START HERE)

### Goal
Check if we already have data before doing expensive web research.

### Implementation

```python
import sys
sys.path.append('/home/claude')
from provider_search import search_providers, display_results

def phase1_search_database(provider_name, state=None):
    """
    Search existing database with fuzzy matching
    
    Args:
        provider_name: Name to search for (handles typos)
        state: Optional state filter (e.g., 'MA', 'NY')
    
    Returns:
        results: List of matches or empty list
    """
    print(f"{'='*80}")
    print(f"PHASE 1: SEARCHING DATABASE")
    print(f"{'='*80}\n")
    print(f"Query: '{provider_name}'")
    if state:
        print(f"State: {state}")
    print()
    
    # Search with fuzzy matching (handles typos automatically)
    results = search_providers(
        query=provider_name,
        state=state,
        fuzzy_threshold=0.4,  # 40% similarity minimum
        limit=10,
        verbose=True
    )
    
    if results:
        print(f"\n✅ Found {len(results)} match(es) in database\n")
        display_results(results, show_full_details=True)
        return results
    else:
        print(f"\n❌ No matches found in database")
        print(f"Will need to search the web...\n")
        return []
```

### User Confirmation Template

```python
def confirm_database_match(results):
    """
    Present database matches to user and ask for confirmation
    
    Returns:
        tuple: (is_correct, selected_result)
    """
    if not results:
        return False, None
    
    print(f"\n{'='*80}")
    print(f"FOUND IN DATABASE")
    print(f"{'='*80}\n")
    
    # Show top match details
    match_type, score, data = results[0]
    legal_name, address, city, state, phone, ptype, parent, raw = data
    
    print(f"Top Match ({score*100:.1f}% similarity):")
    print(f"  Name: {legal_name}")
    print(f"  Location: {city}, {state}")
    print(f"  Address: {address}")
    print(f"  Phone: {phone}")
    if parent:
        print(f"  Parent Organization: {parent}")
    
    print(f"\n{'='*80}")
    print(f"❓ Is this the provider you're looking for?")
    print(f"{'='*80}\n")
    print(f"Options:")
    print(f"  1. YES - Use this data")
    print(f"  2. NO - Search the web for more/different results")
    
    # In actual use, Claude will present this to the user and wait for response
    # For now, return structure for Claude to handle
    
    return {
        'action': 'await_user_confirmation',
        'match_data': data,
        'options': ['yes', 'no'],
        'next_if_yes': 'done',
        'next_if_no': 'phase2b_web_research'
    }
```

---

## Phase 2A: Present Database Match

### When
Database search found match(es).

### Action
1. Display the top match(es) to user
2. Ask: "Is this correct?"
3. If YES → DONE
4. If NO → Continue to Phase 2B

### Template

```python
def phase2a_present_match(results):
    """
    Show database results and get user confirmation
    """
    print(f"\n{'='*80}")
    print(f"PHASE 2A: DATABASE MATCH FOUND")
    print(f"{'='*80}\n")
    
    # Show all matches
    for idx, (match_type, score, data) in enumerate(results[:3], 1):
        legal_name, address, city, state, phone, ptype, parent, raw = data
        print(f"{idx}. {legal_name} ({score*100:.1f}% match)")
        print(f"   {city}, {state} | {phone}")
    
    print(f"\n❓ Is this what you were looking for?")
    print(f"   • YES - I'll use this existing data")
    print(f"   • NO - Search the web for different/additional information")
    
    # Claude waits for user response here
    return 'await_user_input'
```

---

## Phase 2B: Web Research

### When
- No database match found, OR
- User said database match is incorrect

### Action
Use the **Provider Research Skill** to conduct web research.

### Implementation

```python
def phase2b_web_research(provider_name, state, city=None):
    """
    Conduct web research using the Provider Research Skill workflow
    
    This executes the full 4-phase workflow:
      1. Initial Count Verification
      2. Structured Data Extraction
      3. Cross-Validation
      4. Deduplication
    
    Returns:
        research_results: Dict with location data
    """
    print(f"\n{'='*80}")
    print(f"PHASE 2B: WEB RESEARCH")
    print(f"{'='*80}\n")
    print(f"No existing data found. Starting web research...")
    print(f"Using Provider Research Skill (4-phase workflow)\n")
    
    # Reference the Provider Research Skill document
    print("📋 Following Provider Research Skill workflow:")
    print("   ✓ Phase 1: Verify location count")
    print("   ✓ Phase 2: Extract structured data")
    print("   ✓ Phase 3: Cross-validate")
    print("   ✓ Phase 4: Deduplicate")
    print()
    
    # NOTE: Claude will actually execute the Provider Research Skill here
    # This is a reference to show the integration point
    
    """
    ACTUAL IMPLEMENTATION BY CLAUDE:
    
    1. Read /home/claude/provider_research_skill.md
    2. Execute Phase 1: Count Verification
       - web_search for location count
       - web_fetch for directory page
    3. Execute Phase 2: Data Extraction
       - Parse HTML with BeautifulSoup
       - Extract all locations
    4. Execute Phase 3: Cross-Validation
       - Regional searches
       - Third-party sources
    5. Execute Phase 4: Deduplication
       - Apply phone OR address logic
       - Generate duplicate report
    6. Return results to orchestrator
    """
    
    return {
        'action': 'execute_provider_research_skill',
        'parameters': {
            'provider_name': provider_name,
            'state': state,
            'city': city
        }
    }
```

---

## Phase 3: Present Web Research Results

### When
Web research completed successfully.

### Action
1. Show research summary (count, locations, deduplication)
2. Ask: "Should I add this to the database?"
3. If YES → Phase 4
4. If NO → Provide data but don't save

### Template

```python
def phase3_present_results(research_results):
    """
    Present web research results and ask about database insertion
    
    Args:
        research_results: Dict from Provider Research Skill
            - locations: List of location dicts
            - duplicate_report: Deduplication summary
            - claimed_count: Count from website
            - token_cost: Estimated tokens used
    """
    print(f"\n{'='*80}")
    print(f"PHASE 3: WEB RESEARCH COMPLETE")
    print(f"{'='*80}\n")
    
    locations = research_results['locations']
    dup_report = research_results['duplicate_report']
    
    print(f"Research Summary:")
    print(f"  • Claimed count: {research_results['claimed_count']}")
    print(f"  • Extracted: {dup_report['total_input']} raw locations")
    print(f"  • Unique: {dup_report['total_unique']} locations")
    print(f"  • Duplicates removed: {dup_report['total_duplicates']}")
    print(f"  • Token cost: ~{research_results['token_cost']:,}")
    
    # Show sample locations
    print(f"\nSample Locations:")
    for loc in locations[:5]:
        print(f"  • {loc['name']} - {loc['city']}, {loc['state']}")
        print(f"    Phone: {loc['phone']}")
    
    if len(locations) > 5:
        print(f"  ... and {len(locations) - 5} more")
    
    print(f"\n{'='*80}")
    print(f"❓ Should I add these {dup_report['total_unique']} locations to the database?")
    print(f"{'='*80}\n")
    print(f"Options:")
    print(f"  • YES - Add to database for future quick lookups")
    print(f"  • NO - Just provide the data (don't save)")
    print(f"\nNote: Adding to database will enable:")
    print(f"  ✓ Instant lookups in future sessions")
    print(f"  ✓ Fuzzy search (handles typos)")
    print(f"  ✓ No need to re-research")
    
    return 'await_user_input'
```

---

## Phase 4: Add to Database

### When
User confirms they want to save the research results.

### Action
1. Use `provider_database_sqlite.py` to insert records
2. Handle bulk insertion with transaction
3. Confirm success with summary

### Implementation

```python
import sys
sys.path.append('/home/claude')
from provider_database_sqlite import ProviderDatabaseSQLite

def phase4_add_to_database(research_results):
    """
    Add web research results to database
    
    Args:
        research_results: Dict with locations and metadata
    
    Returns:
        success: Boolean
        summary: Dict with insertion details
    """
    print(f"\n{'='*80}")
    print(f"PHASE 4: ADDING TO DATABASE")
    print(f"{'='*80}\n")
    
    locations = research_results['locations']
    
    print(f"Initializing database connection...")
    db = ProviderDatabaseSQLite(db_path='/home/claude/providers.db')
    
    added_count = 0
    skipped_count = 0
    errors = []
    
    print(f"Adding {len(locations)} locations...\n")
    
    for idx, location in enumerate(locations, 1):
        try:
            # Format data for database insertion
            search_result = {
                'npi_data': location.get('npi_data', {}),
                'location_website': location.get('website'),
                'parent_organization_website': location.get('parent_website'),
                'dba_names': location.get('dba_names', []),
                'confidence_score': location.get('confidence_score', 0.95),
                'franchise_owner': location.get('owner'),
                'franchise_id': location.get('franchise_id')
            }
            
            # Add to database
            provider_id = db.add_provider(search_result)
            added_count += 1
            
            if idx % 5 == 0:
                print(f"  ✓ Added {idx}/{len(locations)}")
                
        except Exception as e:
            skipped_count += 1
            errors.append({
                'location': location.get('name', 'Unknown'),
                'error': str(e)
            })
            print(f"  ✗ Skipped {location.get('name', 'Unknown')}: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"DATABASE INSERTION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Summary:")
    print(f"  ✓ Successfully added: {added_count}")
    print(f"  ✗ Skipped (errors): {skipped_count}")
    print(f"  📊 Database now contains updated provider data")
    
    if errors:
        print(f"\nErrors:")
        for err in errors[:5]:
            print(f"  • {err['location']}: {err['error']}")
    
    print(f"\n✅ DONE - Data is now searchable in future sessions")
    
    return {
        'success': added_count > 0,
        'added': added_count,
        'skipped': skipped_count,
        'errors': errors
    }
```

---

## Complete Orchestration Flow (Main Entry Point)

```python
def orchestrate_provider_research(provider_name, location=None, state=None, city=None):
    """
    Main orchestration function - coordinates all phases
    
    Args:
        provider_name: Provider name to search/research
        location: "City, State" format (e.g., "Boston, MA")
        state: State abbreviation (e.g., "MA")
        city: City name (optional, for more targeted search)
    
    Flow:
        1. Parse location if provided
        2. Phase 1: Search database
        3. If found → Phase 2A: Present & confirm
        4. If not found or incorrect → Phase 2B: Web research
        5. Phase 3: Present web results
        6. Phase 4: Add to database (if user confirms)
    """
    
    # Parse location string if provided
    if location and not state:
        # "Boston, MA" → city="Boston", state="MA"
        parts = location.split(',')
        if len(parts) == 2:
            city = parts[0].strip()
            state = parts[1].strip()
    
    print(f"\n{'='*100}")
    print(f"PROVIDER RESEARCH ORCHESTRATOR")
    print(f"{'='*100}\n")
    print(f"Request:")
    print(f"  Provider: {provider_name}")
    if city:
        print(f"  City: {city}")
    if state:
        print(f"  State: {state}")
    print()
    
    # ========================================================================
    # PHASE 1: DATABASE SEARCH
    # ========================================================================
    results = phase1_search_database(provider_name, state)
    
    if results:
        # Found in database
        confirmation = phase2a_present_match(results)
        
        # User says "YES" - data is correct
        if confirmation == 'yes':
            print(f"\n✅ Using existing database record")
            return {
                'source': 'database',
                'data': results[0]
            }
        
        # User says "NO" - need to search web
        print(f"\n🔍 User wants different data. Proceeding to web research...")
    
    # ========================================================================
    # PHASE 2B: WEB RESEARCH
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Starting web research (Provider Research Skill workflow)...")
    print(f"{'='*80}\n")
    
    # NOTE: In actual implementation, Claude will:
    # 1. Read provider_research_skill.md
    # 2. Execute the 4-phase workflow
    # 3. Return research_results
    
    # For this template, we show the integration point:
    """
    research_results = execute_provider_research_skill(
        provider_name=provider_name,
        state=state,
        city=city
    )
    """
    
    # Placeholder for the workflow
    print("📋 Claude will now execute:")
    print("   1. Count verification via web_search")
    print("   2. Data extraction with code")
    print("   3. Cross-validation")
    print("   4. Deduplication (phone OR address)")
    print()
    
    # ========================================================================
    # PHASE 3: PRESENT WEB RESULTS
    # ========================================================================
    # After research completes:
    """
    phase3_present_results(research_results)
    
    # Wait for user input
    user_wants_to_add = get_user_confirmation()
    
    if not user_wants_to_add:
        print("✅ Providing data without saving to database")
        return {
            'source': 'web_research',
            'data': research_results,
            'saved_to_db': False
        }
    """
    
    # ========================================================================
    # PHASE 4: ADD TO DATABASE
    # ========================================================================
    """
    insertion_summary = phase4_add_to_database(research_results)
    
    return {
        'source': 'web_research',
        'data': research_results,
        'saved_to_db': True,
        'insertion_summary': insertion_summary
    }
    """
    
    return {
        'status': 'template_complete',
        'message': 'This is the orchestration template. Claude will execute the actual workflow.'
    }
```

---

## Quick Reference Commands

### For Claude to Execute

```python
# Start the orchestration
orchestrate_provider_research(
    provider_name="Home Instead",
    state="MA"
)

# Or with city
orchestrate_provider_research(
    provider_name="Home Instead",
    location="Boston, MA"
)

# Just database search (skip web research)
results = phase1_search_database("Home Instead", state="MA")

# Just web research (when database has no data)
research_results = execute_provider_research_skill(
    provider_name="Home Instead",
    state="NY"
)
```

---

## Integration with Existing Skills

### This Orchestrator Uses:

1. **provider_search.py** (Phase 1)
   - Fuzzy search with typo tolerance
   - Returns existing database records
   - Fast, no web calls needed

2. **provider_research_skill.md** (Phase 2B)
   - 4-phase web research workflow
   - Count verification → Extraction → Validation → Deduplication
   - Comprehensive location discovery

3. **provider_database_sqlite.py** (Phase 4)
   - Database insertion
   - Handles bulk additions
   - Maintains data integrity

### Directory Structure

```
/home/claude/
├── provider_search.py                          # Fuzzy database search
├── provider_database_sqlite.py                 # Database operations
├── provider_research_skill.md                  # Web research workflow
├── provider_research_orchestration_skill.md    # THIS FILE
├── providers.db                                # SQLite database
└── providers_test.db                          # Test database
```

---

## Decision Tree for Claude

```
User asks about provider
        │
        ▼
Is location specified?
    │
    ├─ YES → Extract city/state
    └─ NO → Ask user for state (optional but recommended)
        │
        ▼
Search database first (ALWAYS)
        │
        ├─ Found → Show to user → Confirm
        │           │
        │           ├─ Confirmed → DONE
        │           └─ Not confirmed → Continue to web
        │
        └─ Not found → Continue to web
                │
                ▼
Execute Provider Research Skill
    (Read skill doc, follow 4 phases)
                │
                ▼
Present results → Ask about database
        │
        ├─ YES → Add to database → Confirm
        └─ NO → Provide data only
                │
                ▼
            DONE
```

---

## User Experience Examples

### Example 1: Found in Database

```
User: "Find Home Instead in Wellesley, MA"

Claude:
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: SEARCHING DATABASE                                 │
└─────────────────────────────────────────────────────────────┘

✅ Found 1 match in database

[EXACT] 100.0% - Home Instead - Metrowest
  Location: Wellesley, MA
  Phone: (781) 237-3636
  Address: 65 Central St, Wellesley, MA 02482

Is this the provider you're looking for?
  • YES - Use this data
  • NO - Search the web for more information

User: "yes"

Claude: ✅ Here's the information from our database:
[provides data]
```

### Example 2: Not in Database

```
User: "Find Home Instead locations in New York"

Claude:
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: SEARCHING DATABASE                                 │
└─────────────────────────────────────────────────────────────┘

❌ No matches found in database
Will need to search the web...

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2B: WEB RESEARCH                                       │
└─────────────────────────────────────────────────────────────┘

Starting Provider Research Skill workflow...
✓ Phase 1: Verifying location count...
✓ Phase 2: Extracting structured data...
✓ Phase 3: Cross-validating...
✓ Phase 4: Deduplicating...

[time passes]

┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: WEB RESEARCH COMPLETE                               │
└─────────────────────────────────────────────────────────────┘

Research Summary:
  • Claimed count: 21
  • Unique locations: 21
  • Duplicates removed: 2
  • Token cost: ~58,800

Should I add these 21 locations to the database?
  • YES - Add to database for future quick lookups
  • NO - Just provide the data

User: "yes"

Claude:
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: ADDING TO DATABASE                                  │
└─────────────────────────────────────────────────────────────┘

✓ Successfully added: 21
📊 Database now contains updated provider data

✅ DONE - Data is now searchable in future sessions
```

### Example 3: Found but Incorrect

```
User: "Find Homestead in Massachusetts"

Claude:
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: SEARCHING DATABASE                                 │
└─────────────────────────────────────────────────────────────┘

⚠️ No exact matches for 'Homestead'. 
Trying fuzzy matching (threshold: 40%)...

✅ Found 2 fuzzy matches:

1. Home Instead - Metrowest (85.5% match)
   Wellesley, MA | (781) 237-3636

2. Homebridge Healthcare (72.3% match)
   Boston, MA | (617) 555-0100

Is this what you were looking for?
  • YES - Use this existing data
  • NO - Search the web for different information

User: "no, I meant Homestead Senior Living"

Claude:
🔍 Understood. Proceeding to web research for "Homestead Senior Living"...

[continues to Phase 2B]
```

---

## Success Metrics

**Efficiency Gains:**
- 80% of queries answered from database (instant, 0 tokens)
- 20% require web research (full workflow)
- Average token savings: ~25,000 per avoided research

**User Experience:**
- Clear phase indicators
- Explicit confirmation points
- No surprises in workflow
- Database grows over time (compound efficiency)

**Data Quality:**
- Deduplicated entries
- Verified counts
- User-approved additions
- Audit trail maintained

---

## Notes for Claude

### When Starting Orchestration:

1. **ALWAYS search database first** - Even if you think it's not there, check anyway
2. **Wait for user confirmation** - Don't assume YES, explicitly ask
3. **Explain token costs** - Help user understand the trade-off
4. **Follow the phases** - Don't skip ahead or combine steps
5. **Reference the skills** - Actually read provider_research_skill.md when doing web research

### Common Mistakes to Avoid:

❌ Starting web research without checking database  
❌ Adding to database without user permission  
❌ Not explaining what you're doing at each phase  
❌ Skipping deduplication when adding to database  
❌ Not showing the data before asking "add to database?"  

### Best Practices:

✅ Use clear phase headers in output  
✅ Show progress indicators during long operations  
✅ Summarize what you found before asking questions  
✅ Explain benefits of adding to database  
✅ Confirm success after database operations  

---

## Integration Checklist

Before using this orchestrator, verify:

- [ ] provider_search.py exists and works
- [ ] provider_database_sqlite.py exists and works
- [ ] provider_research_skill.md is complete
- [ ] Database file is accessible (providers.db)
- [ ] Python environment has sqlite3, beautifulsoup4, difflib

Ready to orchestrate!
