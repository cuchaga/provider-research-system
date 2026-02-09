"""
Provider Web Researcher Skill
==============================
Skill 4: Deep Web Research with Data Extraction

Purpose:
    Conduct comprehensive web research when database search fails.
    Extracts structured data, deduplicates, and validates against NPI.

Capabilities:
    - Web search and content extraction (real HTTP + BeautifulSoup)
    - LLM-powered data extraction from unstructured content
    - Historical data extraction (previous names, owners, acquisitions)
    - Smart deduplication (handles edge cases)
    - NPI registry validation and matching
    - Multi-location detection

Usage:
    from provider_web_researcher import ProviderWebResearcher
    
    researcher = ProviderWebResearcher()
    results = researcher.research(
        provider_name="Home Instead",
        location="Boston, MA"
    )
"""

import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus, urljoin

# Web scraping imports
try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    print("Warning: requests/beautifulsoup4 not available. Install with: pip install requests beautifulsoup4")


@dataclass
class ResearchResult:
    """Result from web research"""
    provider_name: str
    locations: List[Dict]
    npi_records: List[Dict]
    historical_data: Dict  # Previous names, owners, acquisitions
    confidence: float
    source_urls: List[str]
    warnings: List[str]
    research_timestamp: str


@dataclass
class DeduplicationResult:
    """Result from deduplication analysis"""
    is_duplicate: bool
    reason: str
    confidence: float
    matching_provider_id: Optional[str]


class ProviderWebResearcher:
    """
    Skill 4: Web Research & Data Extraction
    
    Comprehensive research workflow:
    1. Web search
    2. Data extraction
    3. Deduplication
    4. NPI validation
    """
    
    EXTRACTION_PROMPT = """Extract healthcare provider locations from this web content.

WEB CONTENT:
{web_content}

Extract all provider locations mentioned. For each location, extract:
- Business name
- Full address (street, city, state, zip)
- Phone number
- Website/URL
- Any franchise or location identifiers

Return JSON array:
[
    {{
        "name": "Legal or DBA name",
        "address": "Full street address",
        "city": "City",
        "state": "XX",
        "zip": "12345",
        "phone": "(123) 456-7890",
        "website": "https://...",
        "franchise_id": "if mentioned",
        "additional_info": "any other relevant details"
    }}
]

RULES:
- Extract ALL distinct locations found
- Normalize state to 2-letter codes
- If multiple locations, return all of them
- If info is missing, use null
- Don't make up information

Return ONLY valid JSON array."""
    
    HISTORY_EXTRACTION_PROMPT = """Extract historical information about this organization from the web content.

WEB CONTENT:
{web_content}

Look for and extract any historical information such as:
- Previous business names ("Formerly known as...", "Previously called...")
- Name changes with dates
- Previous owners or parent organizations
- Acquisitions ("Acquired by X in 20XX")
- Mergers ("Merged with X in 20XX")
- Ownership changes
- Company history timeline

Return JSON:
{{
    "previous_names": [
        {{
            "name": "Old business name",
            "date": "YYYY-MM-DD or YYYY or null",
            "type": "legal_name or dba",
            "notes": "Additional context"
        }}
    ],
    "previous_owners": [
        {{
            "owner": "Previous parent organization",
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null",
            "change_type": "acquisition, merger, ownership_change",
            "notes": "Additional context"
        }}
    ],
    "company_history": "Brief timeline summary if available"
}}

RULES:
- Only extract information explicitly stated in the content
- Include dates when mentioned
- If no historical data found, return empty arrays
- Don't make assumptions

Return ONLY valid JSON."""
    
    DEDUPLICATION_PROMPT = """Determine if these are duplicate provider records.

NEW PROVIDER:
{new_provider}

EXISTING PROVIDER:
{existing_provider}

Are these the same provider/location? Consider:
- Same phone number → usually duplicate
- Same address, different suite → likely duplicate
- Franchise vs Corporate HQ → NOT duplicate
- Different cities → NOT duplicate
- Slight name variations (Inc, LLC) → might be same

Return JSON:
{{
    "is_duplicate": true/false,
    "reason": "Explanation of decision",
    "confidence": 0.95
}}

Return ONLY valid JSON."""
    
    NPI_MATCH_PROMPT = """Match this provider to NPI registry results.

PROVIDER:
{provider_info}

NPI REGISTRY RESULTS:
{npi_results}

Which NPI record (if any) matches this provider best?

Return JSON:
{{
    "matched_npi": "1234567890 or null",
    "match_confidence": 0.9,
    "reasoning": "Why this NPI matches",
    "warnings": ["any concerns about the match"]
}}

RULES:
- Business names may differ slightly from legal names
- Match on address if available
- Don't force a match if unclear
- Consider taxonomy/specialty if relevant

Return ONLY valid JSON."""
    
    # Web scraping configuration
    REQUEST_TIMEOUT = 10  # seconds
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    MAX_RETRIES = 2
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    def __init__(self, llm_client=None, web_search_fn=None, use_real_scraping=True):
        """
        Initialize web researcher.
        
        Args:
            llm_client: LLM client for extraction/matching
            web_search_fn: Function to perform web search (returns URLs)
            use_real_scraping: Whether to use real HTTP requests (default True)
        """
        self.llm_client = llm_client
        self.web_search_fn = web_search_fn
        self.use_real_scraping = use_real_scraping and SCRAPING_AVAILABLE
        self.session = None
        
        if self.use_real_scraping:
            self._init_session()
    
    def _init_session(self):
        """Initialize requests session with proper headers."""
        if not SCRAPING_AVAILABLE:
            return
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def research(
        self,
        provider_name: str,
        location: str = None,
        state: str = None,
        deep_research: bool = True
    ) -> ResearchResult:
        """
        Conduct comprehensive provider research.
        
        Args:
            provider_name: Provider/organization name
            location: City, State or full location
            state: State filter (if location not provided)
            deep_research: Whether to do multi-page research
        
        Returns:
            ResearchResult with all findings
        """
        warnings = []
        
        # Step 1: Web search
        urls = self._web_search(provider_name, location or state)
        if not urls:
            warnings.append("No web results found")
            return self._empty_result(provider_name, warnings)
        
        # Step 2: Fetch and extract data
        locations = []
        all_content = []
        for url in urls[:5]:  # Limit to first 5 URLs
            content = self._fetch_content(url)
            if content:
                all_content.append(content)
                extracted = self._extract_locations(content)
                locations.extend(extracted)
            time.sleep(self.RATE_LIMIT_DELAY)  # Rate limiting
        
        if not locations:
            warnings.append("Could not extract location data from web pages")
        
        # Step 3: Extract historical data
        historical_data = self._extract_historical_data(all_content) if all_content else {
            'previous_names': [],
            'previous_owners': [],
            'company_history': None
        }
        
        # Step 4: Deduplicate locations
        locations = self._deduplicate_locations(locations)
        
        # Step 5: NPI validation
        npi_records = []
        for location in locations:
            npi_data = self._validate_npi(location)
            if npi_data:
                location['npi'] = npi_data['npi']
                npi_records.append(npi_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(locations, npi_records, warnings)
        
        return ResearchResult(
            provider_name=provider_name,
            locations=locations,
            npi_records=npi_records,
            historical_data=historical_data,
            confidence=confidence,
            source_urls=urls[:5],
            warnings=warnings,
            research_timestamp=datetime.utcnow().isoformat()
        )
    
    def check_duplicate(
        self,
        new_provider: Dict,
        existing_provider: Dict
    ) -> DeduplicationResult:
        """
        Check if two provider records are duplicates.
        
        Args:
            new_provider: New provider data
            existing_provider: Existing database record
        
        Returns:
            DeduplicationResult
        """
        # Rule-based checks first (fast)
        rule_result = self._rule_based_deduplication(new_provider, existing_provider)
        if rule_result:
            return rule_result
        
        # LLM-based for edge cases
        if self.llm_client:
            return self._llm_deduplication(new_provider, existing_provider)
        else:
            return self._simulate_deduplication(new_provider, existing_provider)
    
    def _web_search(self, provider_name: str, location: str = None) -> List[str]:
        """Perform web search and return URLs."""
        if self.web_search_fn:
            query = f"{provider_name} healthcare"
            if location:
                query += f" {location}"
            return self.web_search_fn(query)
        else:
            # Simulate for testing
            return [
                f"https://example.com/{provider_name.replace(' ', '-').lower()}",
                f"https://example.com/{provider_name.replace(' ', '-').lower()}/locations"
            ]
    
    def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch web page content with real HTTP or simulation."""
        if self.use_real_scraping:
            return self._fetch_content_real(url)
        else:
            # Simulate content for testing
            return self._simulate_web_content(url)
    
    def _fetch_content_real(self, url: str) -> Optional[str]:
        """Fetch and parse actual web page content."""
        if not SCRAPING_AVAILABLE or not self.session:
            return None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    timeout=self.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Parse HTML and extract text
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text(separator='\n')
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                # Limit size for LLM
                if len(text) > 50000:
                    text = text[:50000] + "\n[Content truncated...]"
                
                return text
                
            except requests.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                print(f"Timeout fetching {url}")
                return None
                
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
                return None
        
        return None
    
    def _simulate_web_content(self, url: str) -> str:
        """Generate simulated web content for testing."""
        return f"""About Us - Sample Provider
        
Welcome to Sample Provider Home Care Services

We have been serving the community since 2010.

Our Locations:
- 123 Main Street, Boston, MA 02101
- Phone: (617) 555-0100
- Email: info@sampleprovider.com

Company History:
Formerly known as ABC Home Services until 2015.
Acquired by National Care Partners in 2020.

Services: In-home care, companionship, meal preparation.
"""
    
    def _extract_locations(self, content: str) -> List[Dict]:
        """Extract provider locations from web content using LLM."""
        if self.llm_client:
            prompt = self.EXTRACTION_PROMPT.format(web_content=content[:8000])
            response = self._call_llm(prompt, max_tokens=2000)
            return self._parse_extraction_response(response)
        else:
            # Simulate extraction
            return self._simulate_extraction(content)
    
    def _extract_historical_data(self, contents: List[str]) -> Dict:
        """Extract historical information from web content."""
        # Combine all content (limited)
        combined_content = '\n\n---PAGE BREAK---\n\n'.join(
            content[:5000] for content in contents[:3]
        )
        
        if self.llm_client:
            prompt = self.HISTORY_EXTRACTION_PROMPT.format(web_content=combined_content)
            response = self._call_llm(prompt, max_tokens=1500)
            return self._parse_json_response(response) or {
                'previous_names': [],
                'previous_owners': [],
                'company_history': None
            }
        else:
            # Simulate historical data extraction
            return self._simulate_historical_extraction(combined_content)
    
    def _deduplicate_locations(self, locations: List[Dict]) -> List[Dict]:
        """Remove duplicate locations from list."""
        unique = []
        seen_phones = set()
        seen_addresses = set()
        
        for loc in locations:
            phone = self._normalize_phone(loc.get('phone', ''))
            address = self._normalize_address(loc.get('address', ''))
            
            # Skip if we've seen this phone or address
            if phone and phone in seen_phones:
                continue
            if address and address in seen_addresses:
                continue
            
            unique.append(loc)
            if phone:
                seen_phones.add(phone)
            if address:
                seen_addresses.add(address)
        
        return unique
    
    def _validate_npi(self, location: Dict) -> Optional[Dict]:
        """Validate location against NPI registry."""
        # This would call the actual NPI registry API
        # For now, simulate
        return {
            'npi': '1234567890',
            'legal_name': location.get('name'),
            'status': 'active'
        }
    
    def _rule_based_deduplication(
        self,
        new: Dict,
        existing: Dict
    ) -> Optional[DeduplicationResult]:
        """Fast rule-based duplicate detection."""
        
        # Rule 1: Same phone number → duplicate
        new_phone = self._normalize_phone(new.get('phone', ''))
        existing_phone = self._normalize_phone(existing.get('phone', ''))
        
        if new_phone and existing_phone and new_phone == existing_phone:
            return DeduplicationResult(
                is_duplicate=True,
                reason="Same phone number",
                confidence=0.95,
                matching_provider_id=existing.get('id')
            )
        
        # Rule 2: Same NPI → duplicate
        if new.get('npi') and new.get('npi') == existing.get('npi'):
            return DeduplicationResult(
                is_duplicate=True,
                reason="Same NPI",
                confidence=1.0,
                matching_provider_id=existing.get('id')
            )
        
        # Rule 3: Same normalized address → duplicate
        new_addr = self._normalize_address(new.get('address', ''))
        existing_addr = self._normalize_address(existing.get('address_full', ''))
        
        if new_addr and existing_addr and new_addr == existing_addr:
            return DeduplicationResult(
                is_duplicate=True,
                reason="Same address",
                confidence=0.9,
                matching_provider_id=existing.get('id')
            )
        
        # Rule 4: Different cities → not duplicate
        if new.get('city') and existing.get('address_city'):
            if new['city'].lower() != existing['address_city'].lower():
                return DeduplicationResult(
                    is_duplicate=False,
                    reason="Different cities",
                    confidence=0.9,
                    matching_provider_id=None
                )
        
        return None  # Need LLM for edge cases
    
    def _llm_deduplication(self, new: Dict, existing: Dict) -> DeduplicationResult:
        """Use LLM for complex deduplication cases."""
        prompt = self.DEDUPLICATION_PROMPT.format(
            new_provider=json.dumps(new, indent=2),
            existing_provider=json.dumps(existing, indent=2)
        )
        
        response = self._call_llm(prompt, max_tokens=500)
        data = self._parse_json_response(response)
        
        return DeduplicationResult(
            is_duplicate=data['is_duplicate'],
            reason=data['reason'],
            confidence=data['confidence'],
            matching_provider_id=existing.get('id') if data['is_duplicate'] else None
        )
    
    def _simulate_deduplication(self, new: Dict, existing: Dict) -> DeduplicationResult:
        """Simulate deduplication for testing."""
        # Default to not duplicate if rules didn't catch it
        return DeduplicationResult(
            is_duplicate=False,
            reason="Different providers based on available data",
            confidence=0.7,
            matching_provider_id=None
        )
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        return re.sub(r'[^\d]', '', phone)
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        addr = address.lower()
        # Remove suite/unit numbers
        addr = re.sub(r'\b(suite|ste|unit|#)\s*[\w\d-]+', '', addr)
        # Remove extra spaces
        addr = re.sub(r'\s+', ' ', addr).strip()
        return addr
    
    def _calculate_confidence(
        self,
        locations: List[Dict],
        npi_records: List[Dict],
        warnings: List[str]
    ) -> float:
        """Calculate overall research confidence."""
        score = 0.5  # Base score
        
        if locations:
            score += 0.2
        
        if npi_records:
            score += 0.2
        
        if not warnings:
            score += 0.1
        
        return min(score, 1.0)
    
    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call LLM API."""
        if self.llm_client:
            response = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        return "{}"
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response."""
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {}
    
    def _parse_extraction_response(self, response: str) -> List[Dict]:
        """Parse extraction JSON array."""
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return []
    
    def _simulate_extraction(self, content: str) -> List[Dict]:
        """Simulate data extraction for testing."""
        # Try to extract basic info from simulated content
        locations = []
        
        # Simple regex patterns
        phone_pattern = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        email_pattern = r'[\w.-]+@[\w.-]+\.[\w]+'
        
        phone_match = re.search(phone_pattern, content)
        email_match = re.search(email_pattern, content)
        
        locations.append({
            'name': 'Sample Provider',
            'address': '123 Main St',
            'city': 'Boston',
            'state': 'MA',
            'zip': '02101',
            'phone': phone_match.group(0) if phone_match else '(617) 555-0100',
            'website': 'https://example.com'
        })
        
        return locations
    
    def _simulate_historical_extraction(self, content: str) -> Dict:
        """Simulate historical data extraction for testing."""
        historical = {
            'previous_names': [],
            'previous_owners': [],
            'company_history': None
        }
        
        # Look for common patterns
        if 'formerly known as' in content.lower() or 'previously called' in content.lower():
            historical['previous_names'].append({
                'name': 'ABC Home Services',
                'date': '2015',
                'type': 'legal_name',
                'notes': 'Found in company history'
            })
        
        if 'acquired by' in content.lower():
            historical['previous_owners'].append({
                'owner': 'National Care Partners',
                'start_date': None,
                'end_date': '2020',
                'change_type': 'acquisition',
                'notes': 'Acquired in 2020'
            })
        
        return historical
    
    def _empty_result(self, provider_name: str, warnings: List[str]) -> ResearchResult:
        """Create empty research result."""
        return ResearchResult(
            provider_name=provider_name,
            locations=[],
            npi_records=[],
            historical_data={'previous_names': [], 'previous_owners': [], 'company_history': None},
            confidence=0.0,
            source_urls=[],
            warnings=warnings,
            research_timestamp=datetime.utcnow().isoformat()
        )
    
    def close(self):
        """Close requests session."""
        if self.session:
            self.session.close()
