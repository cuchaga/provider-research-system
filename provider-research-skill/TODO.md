# TODO: Add Top Home Healthcare Providers

## ✨ NEW: FranchiseResearcher Skill Created!

A new reusable skill has been created to automate this entire process:
- **File:** `provider_research/core/franchise_researcher.py`
- **Examples:** `examples/franchise_research_usage.py`

This skill makes it easy to search and add franchises for ANY company in ANY location, not just Home Instead in MA.

### Quick Usage:
```python
from provider_research import FranchiseResearcher

researcher = FranchiseResearcher(db_config, llm_client)

# Research all locations
results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="Massachusetts",
    include_history=True  # Includes ownership & name changes
)

# Import to database
researcher.import_results(results, dry_run=False)
```

---

## Objective
Use the new FranchiseResearcher skill to add the top 10 largest home healthcare provider chains in the US.

## Tasks

### Research & Planning
- [x] ~~Research top 10 US home healthcare chains~~ → Use FranchiseResearcher for each
- [x] ~~Create flexible search system~~ → FranchiseResearcher skill created!

### Data Collection (Using FranchiseResearcher Skill)
- [ ] Run FranchiseResearcher for Home Instead (all states or specific)
- [ ] Run FranchiseResearcher for Visiting Angels
- [ ] Run FranchiseResearcher for Comfort Keepers  
- [ ] Run FranchiseResearcher for Right at Home
- [ ] Run FranchiseResearcher for BrightStar Care
- [ ] Run FranchiseResearcher for remaining top chains
- [ ] Review and export all results to JSON

### Validation & Database
- [ ] Review exported JSON files for data quality
- [ ] Verify NPI data for high-value locations
- [ ] Review historical events for accuracy
- [ ] Run batch import with dry_run=True
- [ ] Run actual import to database
- [ ] Verify database entries and run tests

---

## Target Providers

### Confirmed Top Chains
1. Home Instead
2. Visiting Angels
3. Comfort Keepers (CK)
4. Right at Home
5. BrightStar Care

### To Research
6-10. TBD (Synergy HomeCare, Honor, Interim HealthCare, etc.)

---

## Implementation Plan

### Phase 1: Test with One Franchise
```bash
# Test the skill with Home Instead in MA
python examples/franchise_research_usage.py
```

### Phase 2: Scale to All Top Chains
```python
# Create batch script for all franchises
franchises = [
    "Home Instead",
    "Visiting Angels", 
    "Comfort Keepers",
    "Right at Home",
    "BrightStar Care"
]

for franchise in franchises:
    results = researcher.research_franchise_locations(
        franchise_name=franchise,
        location="United States",  # Or specific states
        include_history=True
    )
    researcher.export_results(results, f"data/exports/{franchise}.json")
```

### Phase 3: Import to Database
- Review all exported JSON files
- Fix any data quality issues
- Import in batch with historical tracking

---

## Features Included

✅ Multi-source data collection (websites, NPI, directories)  
✅ Historical tracking (ownership changes, acquisitions, name changes)  
✅ Newspaper/business journal search integration  
✅ Automated validation and deduplication  
✅ Batch export to JSON/CSV  
✅ Database import with full history  
✅ Confidence scoring  
✅ Reusable for any franchise, any location  

---

## Notes
- The FranchiseResearcher skill uses all existing skills (WebResearcher, DatabaseManager, SemanticMatcher)
- Includes comprehensive historical data extraction from news sources
- Simulation mode available for testing without API calls
- See `examples/franchise_research_usage.py` for 7 detailed examples

---

**Created:** February 9, 2026 (Evening)  
**Updated:** February 9, 2026 (Late Evening) - Added FranchiseResearcher skill  
**Status:** Skill created, ready for implementation  
**Priority:** High - Use new skill to efficiently add all major franchises  
**Related Files:** 
- `provider_research/core/franchise_researcher.py`
- `examples/franchise_research_usage.py`
