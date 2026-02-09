"""
Provider Semantic Matcher Skill
================================
Skill 3: Intelligent Provider Matching Beyond String Matching

Purpose:
    Use LLM intelligence to match providers when exact/fuzzy search fails.
    Understands abbreviations, parent/subsidiary relationships, DBA names.

Capabilities:
    - Abbreviation expansion (CK → Comfort Keepers)
    - Parent/subsidiary matching (Home Instead → Home Instead - Metrowest)
    - DBA name resolution
    - Regional variation handling
    - Context-aware matching

Usage:
    from provider_research import ProviderSemanticMatcher
    
    matcher = ProviderSemanticMatcher()
    matches = matcher.match(
        query="CK in Michigan",
        candidates=[...database_records...]
    )
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SemanticMatch:
    """Result from semantic matching"""
    provider_id: str
    provider_name: str
    match_score: float
    match_type: str  # abbreviation, parent_child, dba, regional
    reasoning: str
    confidence: float


class ProviderSemanticMatcher:
    """
    Skill 3: Semantic Matching
    
    Intelligently matches providers beyond exact strings using:
    - Abbreviation understanding
    - Parent/subsidiary relationships
    - Business context
    """
    
    SEMANTIC_MATCH_PROMPT = """You are matching a user's provider search against database records.

USER SEARCHING FOR: "{search_query}"
LOCATION FILTER: {location_filter}

DATABASE RECORDS:
{database_records}

Determine which database records (if any) match what the user is searching for.
Consider:
1. Abbreviations: "CK" could be "Comfort Keepers", "VA" could be "Visiting Angels"
2. Parent companies: "Home Instead" could match "Home Instead - Metrowest"
3. DBA names: Business might operate under different name
4. Regional variations: "Home Instead Senior Care" vs "Home Instead"

Return JSON array of matches:
[
    {{
        "provider_id": "uuid",
        "provider_name": "Full Legal Name",
        "match_score": 0.95,
        "match_type": "abbreviation|parent_child|dba|regional|exact",
        "reasoning": "Brief explanation",
        "confidence": 0.9
    }}
]

IMPORTANT:
- Only return matches you're confident about (score > 0.7)
- If no good matches exist, return empty array []
- Don't force matches that don't make sense
- Consider location filters when matching

Return ONLY valid JSON array, no markdown."""
    
    # Common healthcare provider abbreviations
    KNOWN_ABBREVIATIONS = {
        'ck': 'comfort keepers',
        'va': 'visiting angels',
        'hi': 'home instead',
        'bs': 'brightstar',
        'brightstar': 'brightstar care',
        'gcpreit': 'gcp reit',
    }
    
    def __init__(self, llm_client=None):
        """
        Initialize semantic matcher.
        
        Args:
            llm_client: Optional LLM client for semantic matching
        """
        self.llm_client = llm_client
    
    def match(
        self,
        query: str,
        candidates: List[Dict],
        location_filter: Dict = None,
        threshold: float = 0.7
    ) -> List[SemanticMatch]:
        """
        Semantically match a query against candidate providers.
        
        Args:
            query: Search query
            candidates: List of provider dictionaries from database
            location_filter: Optional {state, city} filter
            threshold: Minimum confidence threshold (0.0-1.0)
        
        Returns:
            List of SemanticMatch objects
        """
        if not candidates:
            return []
        
        location_filter = location_filter or {}
        
        # Try rule-based abbreviation expansion first (fast)
        expanded_query = self._expand_abbreviations(query)
        rule_matches = self._rule_based_matching(expanded_query, candidates, location_filter)
        
        if rule_matches:
            return [m for m in rule_matches if m.confidence >= threshold]
        
        # Fall back to LLM semantic matching
        if self.llm_client:
            llm_matches = self._llm_semantic_matching(query, candidates, location_filter)
            return [m for m in llm_matches if m.confidence >= threshold]
        else:
            # Simulate for testing
            sim_matches = self._simulate_semantic_matching(query, candidates, location_filter)
            return [m for m in sim_matches if m.confidence >= threshold]
    
    def _expand_abbreviations(self, query: str) -> str:
        """Expand known abbreviations."""
        query_lower = query.lower()
        
        for abbrev, full_name in self.KNOWN_ABBREVIATIONS.items():
            # Match abbreviation as whole word
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, query_lower):
                query_lower = re.sub(pattern, full_name, query_lower)
        
        return query_lower
    
    def _rule_based_matching(
        self,
        query: str,
        candidates: List[Dict],
        location_filter: Dict
    ) -> List[SemanticMatch]:
        """Fast rule-based matching for common patterns."""
        matches = []
        query_lower = query.lower()
        
        for candidate in candidates:
            legal_name = candidate.get('legal_name', '').lower()
            parent_org = candidate.get('parent_organization', '').lower()
            dba_names = candidate.get('dba_names', [])
            if isinstance(dba_names, str):
                try:
                    dba_names = json.loads(dba_names)
                except:
                    dba_names = []
            
            # Check location filter
            if location_filter:
                state_match = not location_filter.get('state') or \
                             candidate.get('address_state') == location_filter['state']
                city_match = not location_filter.get('city') or \
                            location_filter['city'].lower() in candidate.get('address_city', '').lower()
                
                if not (state_match and city_match):
                    continue
            
            # Match patterns
            match_score = 0
            match_type = None
            reasoning = None
            
            # 1. Parent company match
            if parent_org and query_lower in parent_org:
                match_score = 0.9
                match_type = 'parent_child'
                reasoning = f"Query '{query}' matches parent organization '{parent_org}'"
            
            # 2. Legal name substring
            elif query_lower in legal_name:
                match_score = 0.95
                match_type = 'exact'
                reasoning = f"Query '{query}' found in legal name"
            
            # 3. DBA name match
            elif any(query_lower in str(dba).lower() for dba in dba_names):
                match_score = 0.85
                match_type = 'dba'
                reasoning = f"Query matches DBA name"
            
            # 4. Reverse: legal name in query (e.g., query="Home Instead Metrowest")
            elif legal_name and legal_name in query_lower:
                match_score = 0.9
                match_type = 'regional'
                reasoning = f"Legal name '{legal_name}' is variant of query"
            
            if match_score > 0:
                matches.append(SemanticMatch(
                    provider_id=candidate.get('id'),
                    provider_name=candidate.get('legal_name'),
                    match_score=match_score,
                    match_type=match_type,
                    reasoning=reasoning,
                    confidence=match_score
                ))
        
        # Sort by score
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches
    
    def _llm_semantic_matching(
        self,
        query: str,
        candidates: List[Dict],
        location_filter: Dict
    ) -> List[SemanticMatch]:
        """Use LLM for semantic matching."""
        # Prepare candidate records for LLM
        records_text = self._format_candidates_for_llm(candidates)
        location_text = f"State: {location_filter.get('state', 'Any')}, City: {location_filter.get('city', 'Any')}"
        
        prompt = self.SEMANTIC_MATCH_PROMPT.format(
            search_query=query,
            location_filter=location_text,
            database_records=records_text
        )
        
        response = self._call_llm(prompt)
        return self._parse_llm_matches(response)
    
    def _simulate_semantic_matching(
        self,
        query: str,
        candidates: List[Dict],
        location_filter: Dict
    ) -> List[SemanticMatch]:
        """Simulate semantic matching for testing."""
        # For simulation, use the rule-based approach with lower threshold
        expanded = self._expand_abbreviations(query)
        return self._rule_based_matching(expanded, candidates, location_filter)
    
    def _format_candidates_for_llm(self, candidates: List[Dict]) -> str:
        """Format candidate records for LLM prompt."""
        lines = []
        for i, cand in enumerate(candidates[:20], 1):  # Limit to 20 to save tokens
            lines.append(f"{i}. ID: {cand.get('id')}")
            lines.append(f"   Legal Name: {cand.get('legal_name')}")
            lines.append(f"   Parent Org: {cand.get('parent_organization', 'None')}")
            lines.append(f"   Location: {cand.get('address_city')}, {cand.get('address_state')}")
            if cand.get('dba_names'):
                lines.append(f"   DBA Names: {cand.get('dba_names')}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        if self.llm_client:
            response = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        return "[]"
    
    def _parse_llm_matches(self, response: str) -> List[SemanticMatch]:
        """Parse LLM response into SemanticMatch objects."""
        # Extract JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        try:
            data = json.loads(response)
            matches = []
            
            for item in data:
                matches.append(SemanticMatch(
                    provider_id=item['provider_id'],
                    provider_name=item['provider_name'],
                    match_score=item['match_score'],
                    match_type=item['match_type'],
                    reasoning=item['reasoning'],
                    confidence=item['confidence']
                ))
            
            return matches
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM semantic matches: {e}")
            return []
    
    def explain_match(self, match: SemanticMatch) -> str:
        """Generate human-readable explanation of match."""
        explanations = {
            'abbreviation': f"'{match.provider_name}' matches the abbreviation in your query",
            'parent_child': f"'{match.provider_name}' is part of the organization you searched for",
            'dba': f"'{match.provider_name}' operates under the name you searched",
            'regional': f"'{match.provider_name}' is a regional variant of your query",
            'exact': f"'{match.provider_name}' directly matches your search"
        }
        
        base = explanations.get(match.match_type, match.reasoning)
        return f"{base} (confidence: {match.confidence:.0%})"
