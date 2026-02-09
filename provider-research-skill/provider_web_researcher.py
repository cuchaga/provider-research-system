"""
Provider Web Researcher Skill
==============================
Skill 4: Deep Web Research with Data Extraction

Purpose:
    Conduct comprehensive web research when database search fails.
    Extracts structured data, deduplicates, and validates against NPI.

Capabilities:
    - Web search and content extraction
    - LLM-powered data extraction from unstructured content
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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchResult:
    """Result from web research"""
    provider_name: str
    locations: List[Dict]
    npi_records: List[Dict]
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
    
    def __init__(self, llm_client=None, web_search_fn=None, web_fetch_fn=None):
        """
        Initialize web researcher.
        
        Args:
            llm_client: LLM client for extraction/matching
            web_search_fn: Function to perform web search (returns URLs)
            web_fetch_fn: Function to fetch web page content
        """
        self.llm_client = llm_client
        self.web_search_fn = web_search_fn
        self.web_fetch_fn = web_fetch_fn
    
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
        for url in urls[:5]:  # Limit to first 5 URLs
            content = self._fetch_content(url)
            if content:
                extracted = self._extract_locations(content)
                locations.extend(extracted)
        
        if not locations:
            warnings.append("Could not extract location data from web pages")
            return self._empty_result(provider_name, warnings)
        
        # Step 3: Deduplicate locations
        locations = self._deduplicate_locations(locations)
        
        # Step 4: NPI validation
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
    
    def _fetch_content(self, url: str) -> str:
        """Fetch web page content."""
        if self.web_fetch_fn:
            return self.web_fetch_fn(url)
        else:
            # Simulate content
            return f"Sample content for {url}"
    
    def _extract_locations(self, content: str) -> List[Dict]:
        """Extract provider locations from web content."""
        if self.llm_client:
            prompt = self.EXTRACTION_PROMPT.format(web_content=content[:5000])
            response = self._call_llm(prompt, max_tokens=2000)
            return self._parse_extraction_response(response)
        else:
            # Simulate extraction
            return self._simulate_extraction(content)
    
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
        return [{
            'name': 'Sample Provider',
            'address': '123 Main St',
            'city': 'Boston',
            'state': 'MA',
            'zip': '02101',
            'phone': '(617) 555-0100',
            'website': 'https://example.com'
        }]
    
    def _empty_result(self, provider_name: str, warnings: List[str]) -> ResearchResult:
        """Create empty research result."""
        return ResearchResult(
            provider_name=provider_name,
            locations=[],
            npi_records=[],
            confidence=0.0,
            source_urls=[],
            warnings=warnings,
            research_timestamp=datetime.utcnow().isoformat()
        )
