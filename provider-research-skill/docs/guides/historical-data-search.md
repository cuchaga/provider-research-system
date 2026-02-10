# Enhanced Historical Data Search - Feature Documentation

## Overview

The Provider Research Skill has been enhanced to perform comprehensive historical data searches for franchise locations, including:

- **Ownership changes** - Previous owners, acquisitions, mergers
- **Business name changes** - Previous DBAs, rebranding events  
- **Corporate transactions** - Sale prices, transaction dates, parties involved
- **Franchise transfers** - Franchise sales between operators
- **Corporate restructuring** - Mergers, spin-offs, reorganizations

## How It Works

### 1. Automatic Historical Search

When researching franchises with `include_history=True`, the system automatically:

```python
from provider_research import FranchiseResearcher

researcher = FranchiseResearcher(db_config)

results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="Massachusetts",
    include_history=True  # ← Enables historical data search
)
```

### 2. Data Sources Searched

The system searches multiple sources for historical business data:

#### **News & Media**
- Google News search for historical articles
- Industry publications (Senior Housing News, Home Health Care News)
- Business journals and trade publications
- Local newspaper archives

#### **Government & Regulatory**
- SEC EDGAR filings (for public companies)
- State business registries
- Corporate filing databases

#### **Specialized Databases**
- Business transaction databases
- Franchise registry data
- Real estate transfer records

### 3. What Gets Extracted

For each location, the system extracts:

```python
{
    "legal_name": "Home Instead Senior Care of Boston",
    "current_address": "123 Main St, Boston, MA",
    "current_phone": "617-555-0100",
    "current_owner": "Home Instead Inc",
    
    # Historical data automatically added:
    "previous_names": ["Caring Hearts Home Care"],
    "previous_owners": [
        {
            "owner_name": "Smith Family Trust",
            "owned_until": "2019-03-15",
            "source": "Boston Business Journal"
        }
    ],
    "ownership_history": [
        {
            "event_type": "acquisition",
            "event_date": "2019-03-15",
            "description": "Acquired by Home Instead Inc from Smith Family Trust",
            "previous_value": "Smith Family Trust",
            "new_value": "Home Instead Inc",
            "transaction_value": "$2.3M",
            "source": "Boston Business Journal",
            "confidence": "high"
        }
    ]
}
```

### 4. Search Templates Used

The system uses intelligent search queries:

```python
historical_search_templates = [
    "{franchise} {location} sold",
    "{franchise} {location} ownership change",
    "{franchise} {location} acquisition",
    "{franchise} franchise sale {location}",
    "{franchise} {location} new owner",
    "{location} senior care franchise sold",
    "{franchise} {location} merger",
    "{franchise} franchise transfer {location}"
]
```

## Implementation Details

### Core Methods

#### `_search_historical_data()`
Main orchestrator for historical searches
- Generates search queries
- Coordinates multiple data sources
- Merges results into location records

#### `_search_google_news()`
Searches Google News for historical articles
- Searches news archives
- Extracts article titles and URLs
- Filters for relevant content

#### `_search_business_journals()`
Searches industry-specific publications
- Senior Housing News
- Home Health Care News
- Franchise Times
- Other trade publications

#### `_search_sec_filings()`
Searches SEC EDGAR for public company data
- 8-K filings (material events)
- 10-K annual reports
- S-4 merger filings
- Proxy statements (DEF 14A)

#### `_extract_historical_events()`
Uses LLM to extract structured data from articles
- Identifies event types
- Extracts dates and parties
- Determines transaction values
- Assigns confidence scores

## Usage Examples

### Example 1: Research with Full History

```python
from provider_research import FranchiseResearcher

researcher = FranchiseResearcher(db_config)

# Research with full 25-year history
results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="Massachusetts",
    include_history=True
)

# Access historical data
for location in results['locations']:
    print(f"\n{location.legal_name}")
    print(f"Current owner: {location.parent_organization}")
    
    if location.previous_owners:
        print("\nPrevious owners:")
        for owner in location.previous_owners:
            print(f"  - {owner['owner_name']} (until {owner['owned_until']})")
    
    if location.ownership_history:
        print("\nOwnership events:")
        for event in location.ownership_history:
            print(f"  - {event.event_date}: {event.description}")
```

### Example 2: Custom Date Range

```python
# Search only last 5 years
results = researcher.research_franchise_locations(
    franchise_name="Visiting Angels",
    location="California",
    include_history=True,
    date_range=("2020-01-01", "2025-12-31")
)
```

### Example 3: Export with History

```python
# Research and export
results = researcher.research_franchise_locations(
    franchise_name="Comfort Keepers",
    location="Michigan",
    include_history=True
)

# Export to JSON with all historical data
researcher.export_results(results, "comfort_keepers_mi_history.json")
```

### Example 4: Import to Database

```python
# Research with history
results = researcher.research_franchise_locations(
    franchise_name="BrightStar Care",
    location="Texas",
    include_history=True
)

# Import to database (includes history)
stats = researcher.import_results(results, dry_run=False)

print(f"Imported {stats['providers_imported']} providers")
print(f"Tracked {stats['ownership_changes_tracked']} ownership changes")
print(f"Recorded {stats['historical_events_imported']} historical events")
```

## Database Integration

Historical data is stored in the `provider_history` table:

```sql
CREATE TABLE provider_history (
    id UUID PRIMARY KEY,
    provider_id UUID REFERENCES providers(id),
    change_type VARCHAR(50),  -- 'ownership_change', 'name_change', etc.
    field_name VARCHAR(100),  -- 'parent_organization', 'legal_name', etc.
    old_value TEXT,
    new_value TEXT,
    effective_date DATE,
    source VARCHAR(200),
    notes TEXT,
    recorded_at TIMESTAMP
);
```

## Configuration

### Enable/Disable Historical Search

```python
# Disable for faster research (current data only)
results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="MA",
    include_history=False  # ← Skip historical search
)
```

### Custom Search Sources

```python
from provider_research.core.franchise_researcher import DataSource

# Limit to specific sources
results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="MA",
    include_history=True,
    sources=[
        DataSource.BUSINESS_JOURNAL,
        DataSource.NEWS_ARCHIVE,
        DataSource.SEC_FILINGS
    ]
)
```

## Benefits

1. **Complete Business Picture** - Understand full ownership history
2. **Transaction Intelligence** - Track franchise valuations and trends
3. **Risk Assessment** - Identify frequent ownership changes
4. **Market Analysis** - Understand consolidation trends
5. **Due Diligence** - Verify ownership claims and corporate structure

## Technical Notes

- Historical searches may be rate-limited by external sources
- Results depend on public data availability
- LLM extraction provides structured data from unstructured articles
- Confidence scores help assess data quality
- Sources are tracked for verification

## Future Enhancements

- [ ] Real-time news monitoring for ownership changes
- [ ] Integration with subscription databases (LexisNexis, etc.)
- [ ] Automatic notification of ownership changes
- [ ] Historical timeline visualization
- [ ] Cross-reference with real estate records

## See Also

- [franchise_research_usage.py](../examples/franchise_research_usage.py) - Usage examples
- [FranchiseResearcher API](../provider_research/core/franchise_researcher.py) - Full source code
- [Database Schema](../docs/guides/database-setup.md) - Database structure

---

**Status:** ✅ Implemented (February 9, 2026)
**Version:** 2.0.0
**Feature:** Historical Data Integration
