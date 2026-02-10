# Data Source URL Tracking - Implementation Guide

## Overview

The Provider Research System now tracks all URLs where data is obtained for each provider. URLs are captured at every stage of the research process and stored in the database's `data_source_urls` field.

## Architecture

### 1. Data Structures

**FranchiseLocation** - Enhanced with URL tracking:
```python
@dataclass
class FranchiseLocation:
    # ... other fields ...
    data_sources: Optional[List[str]] = None  # Source identifiers (e.g., "franchise_locator")
    data_source_urls: Optional[List[str]] = None  # Actual URLs where data was obtained
```

**HistoricalEvent** - Already supports URLs:
```python
@dataclass
class HistoricalEvent:
    # ... other fields ...
    source_url: Optional[str] = None  # URL of news article, filing, etc.
```

**Database Schema**:
```sql
ALTER TABLE providers ADD COLUMN data_source_urls TEXT[];
```

### 2. URL Collection Flow

#### Step 1: Web Search
When `WebResearcher` conducts searches, it collects URLs:
```python
web_results = web_researcher.research(
    provider_name="Home Instead",
    location="Boston, MA"
)
# web_results.source_urls contains all URLs searched
```

#### Step 2: Location Creation
URLs are captured when creating FranchiseLocation objects:
```python
location_obj = self._convert_to_franchise_location(
    loc_data,
    franchise_name,
    source=DataSource.FRANCHISE_LOCATOR.value,
    source_urls=web_results.source_urls  # URLs passed here
)
```

#### Step 3: Historical Research
Historical search methods capture article URLs:
- `_search_google_news()` - Returns articles with URLs
- `_search_business_journals()` - Returns articles with URLs  
- `_search_sec_filings()` - Returns filings with URLs

#### Step 4: Historical Event Creation
URLs from articles are attached to events:
```python
HistoricalEvent(
    event_type=EventType.OWNERSHIP_CHANGE.value,
    event_date="2020-06-15",
    description="Previous ownership change",
    source=article['source'],
    source_url=article.get('url'),  # URL captured here
    # ... other fields ...
)
```

#### Step 5: Merging Historical Data
When historical events are merged into locations, their URLs are collected:
```python
def _merge_historical_data(self, locations, historical_data):
    for loc in locations:
        # ... merge events ...
        # Collect URLs from historical events
        for event in events:
            if event.source_url and event.source_url not in loc.data_source_urls:
                loc.data_source_urls.append(event.source_url)
```

#### Step 6: Deduplication Merging
When duplicate locations are merged, URLs are combined:
```python
def _merge_location_data(self, target, source):
    # Merge data source URLs
    if source.data_source_urls:
        target.data_source_urls.extend(source.data_source_urls)
        target.data_source_urls = list(set(target.data_source_urls))  # Deduplicate
```

#### Step 7: Database Import
URLs are written to the database:
```python
provider_data = {
    'legal_name': location.legal_name,
    'city': location.city,
    'state': location.state,
    # ... other fields ...
    'data_source_urls': location.data_source_urls  # URLs passed to database
}
provider_id = db.add_provider(provider_data)
```

#### Step 8: Database Storage
The database manager converts URLs to PostgreSQL array format:
```python
def to_pg_array(items):
    if not items:
        return None
    # Format as: '{"url1","url2","url3"}'
    return '{' + ','.join([f'"{str(item)}"' for item in items]) + '}'

data_source_urls_array = to_pg_array(provider_data.get('data_source_urls'))
# Stored in database as TEXT[] array
```

## Usage Examples

### Research with URL Tracking

```python
from provider_research import FranchiseResearcher

# Initialize
researcher = FranchiseResearcher(db_config=db_config)

# Research locations
results = researcher.research_franchise_locations(
    franchise_name="Home Instead",
    location="Massachusetts",
    include_history=True
)

# Check captured URLs
for location in results['locations']:
    print(f"Location: {location.legal_name}")
    print(f"Sources: {', '.join(location.data_sources)}")
    print(f"URLs: {len(location.data_source_urls)}")
    for url in location.data_source_urls:
        print(f"  - {url}")
```

### Import to Database

```python
# Import results (URLs are automatically included)
import_stats = researcher.import_results(
    results=results,
    dry_run=False
)
```

### Display with URLs

```python
from provider_research import ProviderDatabaseManager

db = ProviderDatabaseManager()

# Display with URLs
providers = db.display_providers(
    fields=['business_name', 'current_address', 'data_source_urls']
)

for provider in providers:
    print(f"{provider['business_name']}")
    for url in provider.get('data_source_urls', []):
        print(f"  📎 {url}")
```

### Command Line Display

```bash
# Show all providers with data source URLs
python3 display_providers.py business_name data_source_urls

# Show default fields (includes URLs in "Additional Fields" section)
python3 display_providers.py
```

## URL Sources

The system captures URLs from:

1. **Franchise Locators** - Official franchise finder pages
2. **Google News** - Historical news articles about ownership changes
3. **Business Journals** - Senior Housing News, Home Health Care News
4. **SEC EDGAR** - Corporate filings (8-K, 10-K, S-4)
5. **NPI Registry** - Healthcare provider validation
6. **State Registries** - Business entity records
7. **Other Web Sources** - Any additional research sources

## Benefits

### Data Provenance
- Track exactly where each piece of data came from
- Verify information by reviewing original sources
- Audit research quality and thoroughness

### Historical Tracking
- Link ownership changes to news articles
- Connect events to SEC filings
- Trace information back to original publications

### Research Quality
- More URLs = higher confidence score
- Multiple sources validate data
- Enable fact-checking and verification

### Compliance & Transparency
- Document research methodology
- Provide citations for stakeholders
- Support regulatory requirements

## Testing

Run the comprehensive URL tracking test:

```bash
python3 test_url_tracking.py
```

This verifies:
- ✓ Web search URLs are captured
- ✓ Historical article URLs are captured
- ✓ URLs are merged during deduplication
- ✓ URLs are written to database
- ✓ URLs can be retrieved for display

## Implementation Notes

### PostgreSQL Array Handling
URLs are stored as PostgreSQL TEXT[] arrays. The helper function `to_pg_array()` properly escapes and formats URLs for storage.

### Deduplication
When locations are merged (duplicates), all unique URLs are preserved. No URLs are lost during the deduplication process.

### Historical Events
The `provider_history` table already supports `source_url` field. When recording historical events, URLs are automatically included.

### Confidence Scoring
Having data source URLs adds +0.05 to the confidence score, rewarding well-documented research.

## Migration

To add the field to an existing database:

```bash
python3 add_data_source_urls_field.py
```

This adds the `data_source_urls TEXT[]` column to the `providers` table.
