# Provider Location Research Skill

## Purpose
Systematically research and catalog healthcare provider locations by state with accurate counting, deduplication, and verification to prevent incomplete or incorrect location counts.

## When to Use This Skill
- User requests: "Find all [Provider] locations in [State]"
- Building provider databases or contact lists
- Researching franchise or branch networks
- Comparing provider coverage across regions
- Any task involving counting or cataloging multiple locations

## Critical Prevention Rule: NEVER Start Research Without Verified Count

**STOP and verify count BEFORE beginning detailed research on individual locations.**

The most common error is starting research with an incomplete location count, wasting tokens on partial datasets. This skill prevents the "14 vs 21" problem by requiring count verification first.

---

## The 4-Phase Workflow

### Phase 1: Initial Count Verification (MANDATORY)
**Goal:** Establish accurate target count BEFORE researching individual locations.

**Steps:**
1. **Extract claimed count from provider website**
   - Search: `"[Provider]" "[State]" "showing * locations"`
   - Look for phrases: "showing X locations", "X offices in [State]", "serving X communities"
   - Example: "Home Instead has 21 locations in New York"

2. **Use web_search to find location directory page**
   - Search: `"[Provider]" "[State]" locations directory`
   - Identify the main locations listing page URL

3. **Verify count matches claimed number**
   - If web_search returns fewer results than claimed → Use web_fetch to get complete HTML
   - If count mismatch > 10% → STOP and investigate before proceeding

**Quality Gate:** Do NOT proceed to Phase 2 until you have confidence in the total count.

---

### Phase 2: Structured Data Extraction
**Goal:** Extract ALL location data systematically using code, not manual parsing.

**Why code extraction:**
- Prevents human parsing errors
- Handles large datasets efficiently
- Makes duplicates visible immediately
- Creates audit trail

**Implementation:**
```python
from bs4 import BeautifulSoup
import re

def extract_locations(html_content):
    """
    Extract locations from provider website HTML
    Returns list of dicts with franchise_id, name, phone, address
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    locations = []
    
    # Find all location entries (adjust selector based on site structure)
    location_divs = soup.find_all('div', class_='location-card')
    
    for div in location_divs:
        location = {
            'franchise_id': extract_franchise_id(div),
            'name': extract_name(div),
            'phone': extract_phone(div),
            'address': extract_address(div)
        }
        locations.append(location)
    
    return locations

def extract_franchise_id(div):
    """Extract franchise/location ID from various patterns"""
    # Check for explicit ID
    if id_elem := div.find(id=re.compile(r'franchise|location')):
        return id_elem.text.strip()
    
    # Check for data attributes
    if 'data-franchise-id' in div.attrs:
        return div['data-franchise-id']
    
    # Extract from URL
    if link := div.find('a', href=True):
        match = re.search(r'/(\d+)/?$', link['href'])
        if match:
            return match.group(1)
    
    return None

def extract_phone(div):
    """Extract phone number"""
    if phone := div.find('a', href=re.compile(r'^tel:')):
        return phone.text.strip()
    
    if phone := div.find(class_=re.compile(r'phone|tel|contact')):
        return phone.text.strip()
    
    return None

def extract_address(div):
    """Extract full address"""
    if addr := div.find(class_=re.compile(r'address|location')):
        return addr.text.strip()
    
    return None
```

**Quality Gate:** Extracted count must match claimed count (±10%).

---

### Phase 3: Cross-Validation
**Goal:** Verify extraction completeness and identify gaps.

**Steps:**
1. **Compare extracted vs. claimed count**
   ```python
   claimed_count = 21
   extracted_count = len(locations)
   
   if abs(extracted_count - claimed_count) > claimed_count * 0.1:
       print(f"⚠️ COUNT MISMATCH: Claimed {claimed_count}, Extracted {extracted_count}")
       print(f"   Difference: {abs(extracted_count - claimed_count)} locations")
       # STOP - investigate before proceeding
   ```

2. **Regional verification**
   - If state has major cities, search by city: `"[Provider]" "[City]" location phone`
   - Cross-reference with caring.com: `site:caring.com "[Provider]" [State]`

3. **Handle duplicates BEFORE user confirmation**
   - Apply deduplication logic (see Phase 4)
   - Track which entries were merged and why

**Quality Gate:** Final unique count must be within 10% of claimed count.

---

### Phase 4: Deduplication & User Confirmation
**Goal:** Remove duplicates and present clean dataset for approval.

#### Deduplication Logic: Phone OR Address

**Rule:** Locations are duplicates if they have:
- **Same phone number**, OR
- **Same address** (normalized)

**NOT:** Require both to match (that's too strict)

#### Implementation

```python
def normalize_phone(phone):
    """Normalize phone to digits only for comparison"""
    if not phone:
        return ""
    return ''.join(filter(str.isdigit, phone))

def normalize_address(address):
    """
    Normalize address for comparison
    - Lowercase
    - Remove suite/floor numbers
    - Strip punctuation
    - Standardize spacing
    """
    if not address:
        return ""
    
    # Convert to lowercase
    addr = address.lower()
    
    # Remove common variations
    addr = addr.replace('suite', 'ste')
    addr = addr.replace('floor', 'fl')
    addr = addr.replace('apartment', 'apt')
    addr = addr.replace('.', '')
    addr = addr.replace(',', '')
    
    # Remove extra whitespace
    addr = ' '.join(addr.split())
    
    # Extract street address only (ignore suite/floor numbers)
    # Example: "19 Merrick Ave Suite 201" -> "19 merrick ave"
    parts = addr.split()
    street_parts = []
    for part in parts:
        if part in ['ste', 'suite', 'fl', 'floor', 'apt', 'unit', '#']:
            break
        street_parts.append(part)
    
    return ' '.join(street_parts)

def deduplicate_locations(locations):
    """
    Remove duplicates based on EITHER phone OR address match
    
    Args:
        locations: List of dicts with 'phone' and 'address' keys
        
    Returns:
        unique_locations: List of unique locations
        duplicate_report: Dict tracking what was removed
    """
    unique = []
    seen_phones = set()
    seen_addresses = set()
    duplicates = []
    
    # Sort by completeness (entries with both phone and address first)
    sorted_locs = sorted(
        locations,
        key=lambda x: (bool(x.get('phone')), bool(x.get('address'))),
        reverse=True
    )
    
    for loc in sorted_locs:
        phone = normalize_phone(loc.get('phone', ''))
        address = normalize_address(loc.get('address', ''))
        
        # Check if duplicate
        is_duplicate = False
        dup_reason = []
        
        if phone and phone in seen_phones:
            is_duplicate = True
            dup_reason.append('phone')
        
        if address and address in seen_addresses:
            is_duplicate = True
            dup_reason.append('address')
        
        if is_duplicate:
            duplicates.append({
                'location': loc,
                'reason': ' & '.join(dup_reason),
                'matches': phone if 'phone' in dup_reason else address
            })
        else:
            unique.append(loc)
            if phone:
                seen_phones.add(phone)
            if address:
                seen_addresses.add(address)
    
    duplicate_report = {
        'total_input': len(locations),
        'total_unique': len(unique),
        'total_duplicates': len(duplicates),
        'details': duplicates
    }
    
    return unique, duplicate_report
```

#### Edge Cases

1. **Same phone, missing address**
   - Decision: DUPLICATE (phone match)
   - Action: Keep entry with more complete data

2. **Same address with different suite numbers**
   - Example: "19 Merrick Ave Suite 201" vs "19 Merrick Ave Suite 305"
   - Decision: DUPLICATE (same street address after normalization)
   - Action: Keep first entry

3. **Similar but different addresses**
   - Example: "19 Merrick Ave" vs "21 Merrick Ave"
   - Decision: UNIQUE (different street numbers)
   - Action: Keep both

4. **Missing data**
   - Example: Phone="" and Address=""
   - Decision: UNIQUE (can't match empty data)
   - Action: Keep but flag as incomplete

#### User Confirmation Template

```python
def present_summary_for_approval(provider, state, unique_locs, dup_report, claimed_count):
    """Present summary and wait for user approval"""
    
    print(f"\n{'='*80}")
    print(f"RESEARCH SUMMARY: {provider} - {state}")
    print(f"{'='*80}\n")
    
    print(f"Claimed count (from website): {claimed_count}")
    print(f"Extracted count (raw):        {dup_report['total_input']}")
    print(f"Unique count (after dedup):   {dup_report['total_unique']}")
    print(f"Duplicates removed:           {dup_report['total_duplicates']}")
    
    if dup_report['total_duplicates'] > 0:
        print(f"\nDuplicate Details:")
        for dup in dup_report['details'][:5]:  # Show first 5
            print(f"  ✗ {dup['location'].get('name', 'N/A')} - Duplicate by {dup['reason']}")
    
    print(f"\n{'='*80}")
    print(f"VALIDATION:")
    print(f"{'='*80}\n")
    
    variance = abs(dup_report['total_unique'] - claimed_count)
    variance_pct = (variance / claimed_count * 100) if claimed_count > 0 else 0
    
    if variance_pct <= 10:
        print(f"✅ Count variance: {variance} ({variance_pct:.1f}%) - ACCEPTABLE")
    else:
        print(f"⚠️ Count variance: {variance} ({variance_pct:.1f}%) - INVESTIGATE")
    
    print(f"\nEstimated token cost for {dup_report['total_unique']} locations:")
    print(f"  • NPI lookups: ~{dup_report['total_unique'] * 1500:,} tokens")
    print(f"  • Data enrichment: ~{dup_report['total_unique'] * 1300:,} tokens")
    print(f"  • TOTAL: ~{dup_report['total_unique'] * 2800:,} tokens")
    
    print(f"\n{'='*80}")
    print(f"Ready to proceed with detailed research on {dup_report['total_unique']} locations?")
    print(f"{'='*80}\n")
```

**Quality Gate:** User must explicitly approve before proceeding with detailed research.

---

## Search Strategy Enhancements

### Why web_search > web_fetch for discovery

**web_search advantages:**
1. **Finds multiple sources** - Returns top 10 results, gives comprehensive view
2. **Structured snippets** - Pre-parsed phone numbers and addresses
3. **Cross-validation** - Can compare provider website vs caring.com vs local directories
4. **Regional discovery** - Reveals locations that may not be on main directory page

**web_fetch limitations:**
1. **Single page only** - Misses locations on separate pages
2. **Manual parsing** - Requires custom code for each site structure
3. **No context** - Doesn't show how locations appear on other platforms

### Multi-source search strategy

```python
# Search 1: Get target count
web_search('"Home Instead" "New York" "showing * locations"')

# Search 2: Get complete location list
web_search('"Home Instead" "New York" locations directory')

# Search 3: Regional fill (if gaps found)
web_search('"Home Instead" "Manhattan" location phone')
web_search('"Home Instead" "Brooklyn" location phone')

# Search 4: Third-party validation
web_search('site:caring.com "Home Instead" "New York"')
```

---

## Token Estimation

**Per-location costs (based on Home Instead MA & NY research):**

| Task | Tokens | Notes |
|------|--------|-------|
| NPI lookup (individual) | ~1,500 | Search by name + credentials validation |
| NPI lookup (organization) | ~800 | Simpler, just business name |
| Data enrichment | ~1,300 | Address formatting, phone validation, etc. |
| **Total per location** | **~2,800** | Average across mix of individual/org |

**Full project estimates:**
- 10 locations: ~28,000 tokens
- 21 locations: ~58,800 tokens (Home Instead NY)
- 50 locations: ~140,000 tokens
- 100 locations: ~280,000 tokens

**Cost-benefit analysis:**
- Upfront workflow (Phases 1-4): ~5,000-8,000 tokens
- Savings from preventing reruns: ~30,000-60,000 tokens per avoided restart
- ROI: 4-8x token savings on medium projects

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

### Pitfall 1: Fragmented web_search data
**Problem:** web_search returns 3-5 locations per result, miss full list.  
**Solution:** Always use web_fetch on the main directory page URL found via web_search.

### Pitfall 2: Manual counting errors
**Problem:** "I see 14 locations" when there are actually 21.  
**Solution:** Use code to count. Humans miss duplicates and multi-page lists.

### Pitfall 3: Starting research too early
**Problem:** Spend 40,000 tokens on 14 locations, then discover 7 more exist.  
**Solution:** Complete all 4 phases before starting detailed research.

### Pitfall 4: Over-aggressive deduplication
**Problem:** Treating same address with different suite numbers as unique.  
**Solution:** Normalize addresses by stripping suite numbers in comparison logic.

### Pitfall 5: Under-aggressive deduplication
**Problem:** Only deduplicating on phone AND address, missing obvious duplicates.  
**Solution:** Deduplicate on phone OR address (not both required).

---

## Example: Home Instead New York

**Claimed count:** "Home Instead has locations throughout New York"  
**Initial web_search:** Revealed 14 franchise IDs  
**After web_fetch + code extraction:** 23 franchise IDs found  
**After deduplication (phone OR address):** 21 unique locations  

**Duplicates identified:**
- Nassau County (#236 & #379) - Same phone: (516) 826-6307
- Manhattan (#368 & #515) - Same phone: (212) 614-8057

**Result:** ✅ 21 unique locations ready for research (~58,800 tokens)

---

## Implementation Checklist

Before starting any provider research project:

- [ ] Phase 1: Target count verified from provider website
- [ ] Phase 2: HTML extracted and parsed with code
- [ ] Phase 2: Extraction count ≥ 90% of target
- [ ] Phase 3: Regional searches completed (if needed)
- [ ] Phase 3: Third-party validation (caring.com, etc.)
- [ ] Phase 4: Deduplication applied (phone OR address)
- [ ] Phase 4: Duplicate report generated
- [ ] Phase 4: Final count within 10% of claimed
- [ ] Phase 4: User approved dataset and token estimate
- [ ] Ready to begin detailed NPI research

---

## Tools Required

1. **Python with BeautifulSoup** - HTML parsing
2. **web_search** - Multi-source discovery
3. **web_fetch** - Complete page retrieval
4. **SQLite database** - Store results (optional but recommended)
5. **NPI Registry MCP** - Provider credential lookup

---

## Success Metrics

**Before this skill:**
- 50% of projects required restarts due to incomplete counts
- Average token waste: ~35,000 per restart
- Frequent duplicates in final datasets

**After this skill:**
- 95% of projects complete on first attempt
- Token waste reduced by 80%
- Clean, deduplicated datasets
- User confidence in accuracy

---

## Questions to Ask Yourself

Before starting research:
1. "Have I verified the total count from the provider website?"
2. "Am I extracting data with code, not manually?"
3. "Have I accounted for duplicates?"
4. "Does my final count make sense?"
5. "Have I presented the summary for user approval?"

If any answer is "no," stop and complete that phase first.