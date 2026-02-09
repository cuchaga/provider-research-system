"""
Provider Research - LLM Enhanced Module
========================================
Adds intelligent layers to the provider research workflow:
- Layer 0: Prompt Interpretation (understands user intent)
- Layer 2: Semantic Matching (finds providers beyond string matching)
- Layer 3: Intelligent Data Extraction (extracts from unstructured web content)
- Layer 4: Smart Deduplication (handles edge cases)
- Layer 5: NPI Matching Intelligence (fuzzy business name matching)

Usage:
    from provider_research.core.research_llm import ProviderResearchLLM
    # Or use the package-level import:
    from provider_research import ProviderResearchLLM
    
    research = ProviderResearchLLM(db_config, anthropic_api_key)
    result = research.process_query(
        user_query="Find Home Instead near me",
        conversation_history=[...],
        user_context={"location": "Boston, MA"}
    )
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os

# Optional: Use Anthropic API directly for LLM calls
# If running inside Claude, these would be internal calls
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class Intent(Enum):
    """User intent classifications"""
    SEARCH = "search"                    # Find a provider
    ADD = "add"                          # Add to database
    COMPARE = "compare"                  # Compare providers
    LIST = "list"                        # List providers (by state, type, etc.)
    UPDATE = "update"                    # Update existing record
    DELETE = "delete"                    # Remove from database
    CLARIFY = "clarify"                  # Need more info from user
    RESEARCH = "research"                # Deep web research
    VERIFY = "verify"                    # Verify/validate existing data
    RELATE = "relate"                    # Find related entities


@dataclass
class ParsedQuery:
    """Structured output from prompt interpretation"""
    intent: Intent
    providers: List[Dict[str, Any]]      # [{name, location, address, phone}]
    filters: Dict[str, Any]              # {state, city, type, parent_org}
    references_resolved: Dict[str, str]  # {this: "GCP REIT IV", they: "Pine Ridge"}
    multi_step_plan: List[str]           # ["find GCP properties", "search for SNFs"]
    clarification_needed: Optional[str]  # "Which state did you mean?"
    confidence: float                    # 0.0 - 1.0
    raw_interpretation: str              # LLM's reasoning


@dataclass 
class MatchResult:
    """Result from semantic matching"""
    provider_id: str
    provider_name: str
    match_score: float
    match_type: str                      # exact, fuzzy, semantic, parent_child
    reasoning: str


@dataclass
class ExtractionResult:
    """Result from LLM data extraction"""
    locations: List[Dict[str, Any]]
    extraction_confidence: float
    source_url: str
    warnings: List[str]


class ProviderResearchLLM:
    """
    LLM-enhanced provider research system.
    
    Integrates intelligent interpretation, matching, and extraction
    with the existing rule-based database operations.
    """
    
    # Prompt templates
    INTERPRETATION_PROMPT = """You are a healthcare provider research assistant. Analyze the user's query and extract structured information.

CONVERSATION CONTEXT:
{conversation_history}

USER CONTEXT:
- Location: {user_location}
- Previous searches: {previous_searches}
- Last result: {last_result}

CURRENT QUERY: "{user_query}"

Analyze this query and return a JSON response with:
{{
    "intent": "search|add|compare|list|update|delete|clarify|research|verify|relate",
    "providers": [
        {{"name": "...", "location": "city, state", "address": "full address if mentioned", "phone": "if mentioned"}}
    ],
    "filters": {{
        "state": "XX or null",
        "city": "name or null", 
        "provider_type": "type or null",
        "parent_organization": "name or null"
    }},
    "references_resolved": {{
        "this": "what 'this' refers to",
        "that": "what 'that' refers to",
        "they": "what 'they' refers to",
        "it": "what 'it' refers to"
    }},
    "multi_step_plan": [
        "Step 1: description",
        "Step 2: description"
    ],
    "clarification_needed": "Question to ask user, or null if query is clear",
    "confidence": 0.95,
    "reasoning": "Brief explanation of interpretation"
}}

IMPORTANT RULES:
1. Resolve pronouns and references using conversation context
2. If user says "near me" or "local", use their location from context
3. If query is ambiguous, set clarification_needed
4. For complex queries, break into multi_step_plan
5. Extract ALL mentioned providers, even if comparing multiple
6. Normalize state names to 2-letter codes (California → CA)
7. If user references "the address" or "that location", resolve from context

Return ONLY valid JSON, no markdown or explanation outside the JSON."""

    SEMANTIC_MATCH_PROMPT = """You are matching a user's provider search against database records.

USER SEARCHING FOR: "{search_query}"
LOCATION FILTER: {location_filter}

DATABASE RECORDS:
{database_records}

Find ALL records that match the user's search. Consider:
1. Abbreviations (CK = Comfort Keepers, HI = Home Instead)
2. Parent/subsidiary relationships (franchise names)
3. DBA names and trade names
4. Regional variations ("Home Instead of Boston" = "Home Instead")
5. Common misspellings
6. Partial matches ("Visiting" might match "Visiting Angels")

Return JSON:
{{
    "matches": [
        {{
            "id": "database_id",
            "name": "provider name",
            "score": 0.95,
            "match_type": "exact|fuzzy|semantic|abbreviation|parent_child",
            "reasoning": "Why this matches"
        }}
    ],
    "no_match_reason": "If no matches, explain why"
}}

Return ONLY providers that genuinely match. Don't force matches."""

    EXTRACTION_PROMPT = """Extract healthcare provider location data from this web content.

PROVIDER NAME: {provider_name}
TARGET STATE: {state}

WEB CONTENT:
{web_content}

Extract ALL locations for this provider. For each location, extract:
- franchise_id: Any ID number associated with the location
- name: Full location name (e.g., "Home Instead - Metrowest")
- address: Full street address
- city: City name
- state: 2-letter state code
- zip: ZIP code
- phone: Phone number (format: XXX-XXX-XXXX)
- fax: Fax number if present
- website: Location-specific URL if present
- services: List of services offered
- hours: Operating hours if listed

Return JSON:
{{
    "locations": [
        {{
            "franchise_id": "123",
            "name": "Provider Name - Location",
            "address": "123 Main St",
            "city": "Boston",
            "state": "MA",
            "zip": "02101",
            "phone": "617-555-0100",
            "fax": null,
            "website": "https://...",
            "services": ["Home Care", "Respite Care"],
            "hours": "Mon-Fri 9am-5pm"
        }}
    ],
    "total_found": 5,
    "extraction_confidence": 0.9,
    "warnings": ["Some locations may be missing phone numbers"]
}}

RULES:
1. Only extract locations in the target state (if specified)
2. Normalize phone numbers to XXX-XXX-XXXX format
3. If data is ambiguous, include it with lower confidence
4. Note any warnings about data quality
5. Don't invent data - use null for missing fields"""

    DEDUPLICATION_PROMPT = """Analyze these provider locations for duplicates.

LOCATIONS TO ANALYZE:
{locations}

Identify duplicate entries. Two locations are duplicates if:
1. Same phone number (even if addresses differ slightly)
2. Same street address (ignoring suite/floor numbers)
3. Same organization at same location (even with name variations)

NOT duplicates:
- Same organization, different physical locations
- Parent company vs franchise location
- Different suite numbers = usually same location (duplicate)

Return JSON:
{{
    "duplicate_groups": [
        {{
            "keep": {{"id": "...", "reason": "Most complete record"}},
            "remove": [{{"id": "...", "reason": "Same phone as kept record"}}]
        }}
    ],
    "unique_count": 15,
    "duplicates_found": 3,
    "confidence": 0.95,
    "notes": "Any observations about the data"
}}"""

    NPI_MATCH_PROMPT = """Match this provider to NPI registry results.

PROVIDER WE'RE RESEARCHING:
- Name: {provider_name}
- Address: {provider_address}
- City: {provider_city}
- State: {provider_state}
- Phone: {provider_phone}
- Parent Organization: {parent_org}

NPI SEARCH RESULTS:
{npi_results}

Determine which NPI record(s) match this provider. Consider:
1. Business names often differ from NPI registered names
2. Franchise numbers may appear in NPI names (e.g., "COMFORT KEEPERS #547")
3. Parent company may be registered instead of local franchise
4. Address should be close (same city/ZIP)
5. Phone number match is strong evidence

Return JSON:
{{
    "best_match": {{
        "npi": "1234567890",
        "confidence": 0.95,
        "reasoning": "Phone number matches exactly, address is same city"
    }},
    "alternative_matches": [
        {{
            "npi": "0987654321",
            "confidence": 0.6,
            "reasoning": "Same parent company, different location"
        }}
    ],
    "no_match_reason": "If no good matches, explain why"
}}"""

    def __init__(self, db=None, llm_client=None):
        """
        Initialize the LLM-enhanced research system.
        
        Args:
            db: Database connection (ProviderDatabasePostgres instance)
            llm_client: Anthropic client or None (for internal Claude use)
        """
        self.db = db
        self.llm_client = llm_client
        self.conversation_history = []
        self.last_result = None
        
    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Call the LLM with a prompt.
        
        In production, this would call the Anthropic API.
        When running inside Claude, this represents internal reasoning.
        """
        if self.llm_client and HAS_ANTHROPIC:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            # Placeholder for internal Claude reasoning
            # In actual use, Claude would process this directly
            return '{"error": "LLM client not configured"}'
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}", "raw": response}

    # =========================================================================
    # LAYER 0: PROMPT INTERPRETATION
    # =========================================================================
    
    def interpret_query(
        self,
        user_query: str,
        conversation_history: List[Dict] = None,
        user_context: Dict = None
    ) -> ParsedQuery:
        """
        Layer 0: Interpret user's natural language query.
        
        Resolves references, extracts entities, determines intent,
        and creates an execution plan.
        
        Args:
            user_query: Raw user input
            conversation_history: List of previous messages
            user_context: User info (location, preferences)
            
        Returns:
            ParsedQuery with structured interpretation
        """
        conversation_history = conversation_history or []
        user_context = user_context or {}
        
        # Format conversation history
        history_text = "\n".join([
            f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')[:200]}"
            for msg in conversation_history[-5:]  # Last 5 turns
        ]) or "No previous conversation"
        
        # Format previous searches
        previous_searches = user_context.get('previous_searches', [])
        searches_text = ", ".join(previous_searches[-3:]) if previous_searches else "None"
        
        # Format last result
        last_result_text = "None"
        if self.last_result:
            last_result_text = json.dumps(self.last_result, indent=2)[:500]
        
        prompt = self.INTERPRETATION_PROMPT.format(
            conversation_history=history_text,
            user_location=user_context.get('location', 'Unknown'),
            previous_searches=searches_text,
            last_result=last_result_text,
            user_query=user_query
        )
        
        response = self._call_llm(prompt)
        parsed = self._parse_json_response(response)
        
        if "error" in parsed:
            # Fallback to basic parsing
            return ParsedQuery(
                intent=Intent.SEARCH,
                providers=[{"name": user_query}],
                filters={},
                references_resolved={},
                multi_step_plan=[f"Search for: {user_query}"],
                clarification_needed=None,
                confidence=0.5,
                raw_interpretation=f"Fallback parsing: {parsed.get('error')}"
            )
        
        return ParsedQuery(
            intent=Intent(parsed.get('intent', 'search')),
            providers=parsed.get('providers', []),
            filters=parsed.get('filters', {}),
            references_resolved=parsed.get('references_resolved', {}),
            multi_step_plan=parsed.get('multi_step_plan', []),
            clarification_needed=parsed.get('clarification_needed'),
            confidence=parsed.get('confidence', 0.8),
            raw_interpretation=parsed.get('reasoning', '')
        )

    # =========================================================================
    # LAYER 2: SEMANTIC MATCHING
    # =========================================================================
    
    def semantic_match(
        self,
        search_query: str,
        location_filter: Dict = None,
        database_records: List[Dict] = None
    ) -> List[MatchResult]:
        """
        Layer 2: Find semantic matches beyond string similarity.
        
        Handles abbreviations, parent/child relationships, DBAs,
        and other cases that rule-based matching misses.
        
        Args:
            search_query: What user is looking for
            location_filter: {state, city} filter
            database_records: Records to search (or fetches from DB)
            
        Returns:
            List of MatchResult with confidence scores
        """
        if database_records is None and self.db:
            # Fetch records from database
            state = location_filter.get('state') if location_filter else None
            database_records = self.db.list_providers_by_state(state) if state else self.db.list_all_providers()
        
        if not database_records:
            return []
        
        # Format records for prompt (limit to prevent token overflow)
        records_text = json.dumps(database_records[:50], indent=2, default=str)
        location_text = json.dumps(location_filter) if location_filter else "None"
        
        prompt = self.SEMANTIC_MATCH_PROMPT.format(
            search_query=search_query,
            location_filter=location_text,
            database_records=records_text
        )
        
        response = self._call_llm(prompt)
        parsed = self._parse_json_response(response)
        
        matches = []
        for match in parsed.get('matches', []):
            matches.append(MatchResult(
                provider_id=match.get('id', ''),
                provider_name=match.get('name', ''),
                match_score=match.get('score', 0.0),
                match_type=match.get('match_type', 'unknown'),
                reasoning=match.get('reasoning', '')
            ))
        
        return sorted(matches, key=lambda x: x.match_score, reverse=True)

    # =========================================================================
    # LAYER 3: INTELLIGENT DATA EXTRACTION
    # =========================================================================
    
    def extract_locations(
        self,
        web_content: str,
        provider_name: str,
        state: str = None
    ) -> ExtractionResult:
        """
        Layer 3: Extract structured data from unstructured web content.
        
        Uses LLM to understand varied HTML structures and extract
        location data reliably.
        
        Args:
            web_content: HTML or text content from web scraping
            provider_name: Provider we're extracting for
            state: Target state filter (optional)
            
        Returns:
            ExtractionResult with locations and confidence
        """
        # Truncate content if too long
        max_content_length = 40000
        if len(web_content) > max_content_length:
            web_content = web_content[:max_content_length] + "\n...[truncated]..."
        
        prompt = self.EXTRACTION_PROMPT.format(
            provider_name=provider_name,
            state=state or "Any",
            web_content=web_content
        )
        
        response = self._call_llm(prompt, max_tokens=4000)
        parsed = self._parse_json_response(response)
        
        return ExtractionResult(
            locations=parsed.get('locations', []),
            extraction_confidence=parsed.get('extraction_confidence', 0.5),
            source_url=parsed.get('source_url', 'unknown'),
            warnings=parsed.get('warnings', [])
        )

    # =========================================================================
    # LAYER 4: SMART DEDUPLICATION
    # =========================================================================
    
    def deduplicate_locations(
        self,
        locations: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """
        Layer 4: Intelligent deduplication with edge case handling.
        
        Uses LLM to identify duplicates that rule-based matching misses,
        such as same address with different suite numbers.
        
        Args:
            locations: List of location dicts to deduplicate
            
        Returns:
            Tuple of (unique_locations, dedup_report)
        """
        if len(locations) <= 1:
            return locations, {"duplicates_found": 0, "unique_count": len(locations)}
        
        # First pass: obvious duplicates (rule-based, fast)
        obvious_dupes = self._find_obvious_duplicates(locations)
        
        # Remove obvious duplicates
        remaining = [loc for loc in locations if loc.get('id') not in obvious_dupes]
        
        # Second pass: LLM for ambiguous cases
        if len(remaining) > 1:
            locations_text = json.dumps(remaining[:30], indent=2, default=str)
            
            prompt = self.DEDUPLICATION_PROMPT.format(locations=locations_text)
            response = self._call_llm(prompt)
            parsed = self._parse_json_response(response)
            
            # Apply LLM-identified duplicates
            llm_dupes = set()
            for group in parsed.get('duplicate_groups', []):
                for remove in group.get('remove', []):
                    llm_dupes.add(remove.get('id'))
            
            remaining = [loc for loc in remaining if loc.get('id') not in llm_dupes]
            
            return remaining, {
                "total_input": len(locations),
                "obvious_duplicates": len(obvious_dupes),
                "llm_duplicates": len(llm_dupes),
                "unique_count": len(remaining),
                "confidence": parsed.get('confidence', 0.8)
            }
        
        return remaining, {
            "total_input": len(locations),
            "obvious_duplicates": len(obvious_dupes),
            "llm_duplicates": 0,
            "unique_count": len(remaining)
        }
    
    def _find_obvious_duplicates(self, locations: List[Dict]) -> set:
        """Rule-based duplicate detection for obvious cases.
        
        NOTE: Different suite/unit numbers are considered DIFFERENT locations.
        Only exact address matches (including suite) are duplicates.
        Phone number matches are still considered duplicates.
        """
        dupes = set()
        seen_phones = {}
        seen_addresses = {}
        
        for loc in locations:
            loc_id = loc.get('id', id(loc))
            
            # Check phone - same phone = duplicate (strong signal)
            phone = re.sub(r'\D', '', loc.get('phone', ''))
            if phone and len(phone) >= 10:
                if phone in seen_phones:
                    dupes.add(loc_id)
                else:
                    seen_phones[phone] = loc_id
            
            # Check address - KEEP suite/unit numbers (different suites = different locations)
            address = loc.get('address', '').lower()
            # Normalize suite/unit format for consistent comparison
            # "Suite 201" -> "ste 201", "Unit #5" -> "unit 5", etc.
            address = re.sub(r'\bsuite\b', 'ste', address)
            address = re.sub(r'\bapartment\b', 'apt', address)
            address = re.sub(r'#(\d)', r'unit \1', address)  # "#5" -> "unit 5"
            # Remove punctuation but keep alphanumeric and spaces
            address = re.sub(r'[^\w\s]', ' ', address)
            # Normalize whitespace
            address = ' '.join(address.split())
            
            if address and len(address) > 10:
                if address in seen_addresses:
                    dupes.add(loc_id)
                else:
                    seen_addresses[address] = loc_id
        
        return dupes

    # =========================================================================
    # LAYER 5: NPI MATCHING INTELLIGENCE
    # =========================================================================
    
    def match_to_npi(
        self,
        provider_info: Dict,
        npi_results: List[Dict]
    ) -> Dict:
        """
        Layer 5: Intelligently match provider to NPI registry results.
        
        Handles cases where business names don't match registered names.
        
        Args:
            provider_info: Provider data {name, address, city, state, phone}
            npi_results: Results from NPI registry search
            
        Returns:
            Dict with best_match, alternative_matches, reasoning
        """
        if not npi_results:
            return {"best_match": None, "no_match_reason": "No NPI results to match against"}
        
        prompt = self.NPI_MATCH_PROMPT.format(
            provider_name=provider_info.get('name', 'Unknown'),
            provider_address=provider_info.get('address', 'Unknown'),
            provider_city=provider_info.get('city', 'Unknown'),
            provider_state=provider_info.get('state', 'Unknown'),
            provider_phone=provider_info.get('phone', 'Unknown'),
            parent_org=provider_info.get('parent_organization', 'Unknown'),
            npi_results=json.dumps(npi_results[:10], indent=2)
        )
        
        response = self._call_llm(prompt)
        return self._parse_json_response(response)

    # =========================================================================
    # MAIN PROCESSING PIPELINE
    # =========================================================================
    
    def process_query(
        self,
        user_query: str,
        conversation_history: List[Dict] = None,
        user_context: Dict = None
    ) -> Dict:
        """
        Main entry point: Process a user query through all layers.
        
        Args:
            user_query: Natural language query
            conversation_history: Previous conversation turns
            user_context: User info {location, preferences, etc.}
            
        Returns:
            Dict with results, execution trace, and any clarifications needed
        """
        result = {
            "query": user_query,
            "execution_trace": [],
            "clarification_needed": None,
            "results": None,
            "suggestions": []
        }
        
        # Layer 0: Interpret the query
        result["execution_trace"].append("Layer 0: Interpreting query...")
        parsed = self.interpret_query(user_query, conversation_history, user_context)
        result["parsed_query"] = asdict(parsed)
        
        # Check if clarification needed
        if parsed.clarification_needed:
            result["clarification_needed"] = parsed.clarification_needed
            result["execution_trace"].append(f"Clarification needed: {parsed.clarification_needed}")
            return result
        
        # Execute based on intent
        if parsed.intent == Intent.SEARCH:
            result = self._execute_search(parsed, result)
        elif parsed.intent == Intent.ADD:
            result = self._execute_add(parsed, result)
        elif parsed.intent == Intent.COMPARE:
            result = self._execute_compare(parsed, result)
        elif parsed.intent == Intent.LIST:
            result = self._execute_list(parsed, result)
        elif parsed.intent == Intent.RESEARCH:
            result = self._execute_research(parsed, result)
        else:
            result["execution_trace"].append(f"Intent '{parsed.intent.value}' not yet implemented")
        
        # Store result for context in future queries
        self.last_result = result.get("results")
        
        return result
    
    def _execute_search(self, parsed: ParsedQuery, result: Dict) -> Dict:
        """Execute a search intent."""
        result["execution_trace"].append("Executing search intent...")
        
        for provider in parsed.providers:
            provider_name = provider.get('name', '')
            location = provider.get('location', '')
            
            # Layer 1: Database search (rule-based, fast)
            result["execution_trace"].append(f"Layer 1: Searching database for '{provider_name}'...")
            
            if self.db:
                state = parsed.filters.get('state')
                db_results = self.db.search_providers(provider_name, state=state)
                
                if db_results:
                    result["execution_trace"].append(f"Found {len(db_results)} results in database")
                    result["results"] = db_results
                    result["source"] = "database"
                    return result
            
            # Layer 2: Semantic matching
            result["execution_trace"].append("Layer 2: Trying semantic matching...")
            semantic_matches = self.semantic_match(provider_name, parsed.filters)
            
            if semantic_matches and semantic_matches[0].match_score > 0.7:
                result["execution_trace"].append(f"Semantic match found: {semantic_matches[0].provider_name}")
                result["results"] = [asdict(m) for m in semantic_matches]
                result["source"] = "semantic_match"
                return result
            
            # No match found
            result["execution_trace"].append("No matches found in database")
            result["suggestions"].append(f"Would you like me to search the web for '{provider_name}'?")
        
        return result
    
    def _execute_add(self, parsed: ParsedQuery, result: Dict) -> Dict:
        """Execute an add intent."""
        result["execution_trace"].append("Executing add intent...")
        
        # Resolve what to add
        if self.last_result:
            result["execution_trace"].append("Adding last research result to database...")
            result["results"] = {"action": "add", "data": self.last_result}
        else:
            result["clarification_needed"] = "What would you like me to add to the database?"
        
        return result
    
    def _execute_compare(self, parsed: ParsedQuery, result: Dict) -> Dict:
        """Execute a compare intent."""
        result["execution_trace"].append("Executing compare intent...")
        
        if len(parsed.providers) < 2:
            result["clarification_needed"] = "Please specify at least two providers to compare."
            return result
        
        comparisons = []
        for provider in parsed.providers:
            # Search for each provider
            if self.db:
                db_results = self.db.search_providers(provider.get('name', ''))
                comparisons.append({
                    "provider": provider.get('name'),
                    "found": len(db_results) > 0,
                    "data": db_results[0] if db_results else None
                })
        
        result["results"] = {"comparison": comparisons}
        return result
    
    def _execute_list(self, parsed: ParsedQuery, result: Dict) -> Dict:
        """Execute a list intent."""
        result["execution_trace"].append("Executing list intent...")
        
        if self.db:
            state = parsed.filters.get('state')
            if state:
                providers = self.db.list_providers_by_state(state)
                result["results"] = providers
                result["execution_trace"].append(f"Found {len(providers)} providers in {state}")
            else:
                providers = self.db.list_all_providers()
                result["results"] = providers
                result["execution_trace"].append(f"Found {len(providers)} total providers")
        
        return result
    
    def _execute_research(self, parsed: ParsedQuery, result: Dict) -> Dict:
        """Execute a deep research intent."""
        result["execution_trace"].append("Executing research intent...")
        result["execution_trace"].append("This would trigger the full 4-phase research workflow")
        result["suggestions"].append("Use the Provider Research Skill for comprehensive web research")
        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_research_system(db_config: Dict = None, api_key: str = None) -> ProviderResearchLLM:
    """
    Factory function to create an LLM-enhanced research system.
    
    Args:
        db_config: PostgreSQL connection config
        api_key: Anthropic API key (optional)
        
    Returns:
        Configured ProviderResearchLLM instance
    """
    db = None
    if db_config:
        from ..database.postgres import ProviderDatabasePostgres
        db = ProviderDatabasePostgres(db_config)
    
    llm_client = None
    if api_key and HAS_ANTHROPIC:
        llm_client = anthropic.Anthropic(api_key=api_key)
    
    return ProviderResearchLLM(db=db, llm_client=llm_client)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PROVIDER RESEARCH LLM MODULE")
    print("=" * 80)
    print()
    print("This module provides LLM-enhanced capabilities for provider research:")
    print()
    print("LAYERS:")
    print("  0. Prompt Interpretation - Understands user intent, resolves references")
    print("  1. Database Search - Fast rule-based lookup (0 tokens)")
    print("  2. Semantic Matching - Finds matches beyond string similarity")
    print("  3. Data Extraction - Extracts structured data from web content")
    print("  4. Smart Deduplication - Handles edge cases in duplicate detection")
    print("  5. NPI Matching - Intelligently matches providers to NPI records")
    print()
    print("EXAMPLE QUERIES IT CAN HANDLE:")
    print("  - 'Find Home Instead near me'")
    print("  - 'What about their other locations?'")
    print("  - 'Add that to the database'")
    print("  - 'Compare Comfort Keepers vs Visiting Angels in Detroit'")
    print("  - 'Find healthcare providers at the GCP REIT properties'")
    print()
    print("Usage:")
    print("  from provider_research import ProviderResearchLLM")
    print("  research = ProviderResearchLLM(db=db_connection)")
    print("  result = research.process_query('Find Home Instead in Boston')")
