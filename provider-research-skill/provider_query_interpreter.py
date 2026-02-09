"""
Provider Query Interpreter Skill
=================================
Skill 1: Natural Language Understanding for Provider Queries

Purpose:
    Transform natural language queries into structured ParsedQuery objects.
    Handles pronoun resolution, intent classification, and entity extraction.

Capabilities:
    - Intent classification (search, add, compare, list, etc.)
    - Pronoun resolution ("their" → "Home Instead")
    - "Near me" resolution using user context
    - Multi-step plan generation for complex queries
    - Ambiguity detection and clarification requests

Usage:
    from provider_query_interpreter import ProviderQueryInterpreter
    
    interpreter = ProviderQueryInterpreter()
    result = interpreter.interpret(
        user_query="Find Home Instead near me",
        conversation_history=[...],
        user_context={"location": "Boston, MA"}
    )
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Intent(Enum):
    """User intent classifications"""
    SEARCH = "search"
    ADD = "add"
    COMPARE = "compare"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    CLARIFY = "clarify"
    RESEARCH = "research"
    VERIFY = "verify"
    RELATE = "relate"


@dataclass
class ParsedQuery:
    """Structured output from query interpretation"""
    intent: Intent
    providers: List[Dict[str, Any]]
    filters: Dict[str, Any]
    references_resolved: Dict[str, str]
    multi_step_plan: List[str]
    clarification_needed: Optional[str]
    confidence: float
    raw_interpretation: str


class ProviderQueryInterpreter:
    """
    Skill 1: Query Interpretation
    
    Converts natural language into structured queries with:
    - Intent understanding
    - Entity extraction
    - Reference resolution
    - Context awareness
    """
    
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
    
    def __init__(self, llm_client=None):
        """
        Initialize query interpreter.
        
        Args:
            llm_client: Optional LLM client (Claude API, etc.)
                       If None, uses simulated interpretation
        """
        self.llm_client = llm_client
        self.conversation_cache = []
        self.last_result = None
    
    def interpret(
        self,
        user_query: str,
        conversation_history: List[Dict] = None,
        user_context: Dict = None
    ) -> ParsedQuery:
        """
        Interpret a natural language query.
        
        Args:
            user_query: Raw user input
            conversation_history: Recent conversation turns
            user_context: User's location, preferences, etc.
        
        Returns:
            ParsedQuery with structured intent and entities
        """
        conversation_history = conversation_history or []
        user_context = user_context or {}
        
        # Update conversation cache
        self.conversation_cache = conversation_history[-5:]  # Keep last 5 turns
        
        # Build prompt
        prompt = self._build_interpretation_prompt(
            user_query,
            conversation_history,
            user_context
        )
        
        # Call LLM or simulate
        if self.llm_client:
            response = self._call_llm(prompt)
        else:
            response = self._simulate_interpretation(user_query, conversation_history, user_context)
        
        # Parse response
        parsed = self._parse_llm_response(response)
        
        return parsed
    
    def _build_interpretation_prompt(
        self,
        user_query: str,
        conversation_history: List[Dict],
        user_context: Dict
    ) -> str:
        """Build the LLM prompt with context."""
        conv_text = "\n".join([
            f"{turn['role']}: {turn['content']}"
            for turn in conversation_history[-3:]
        ]) or "No previous conversation"
        
        last_result_text = json.dumps(self.last_result) if self.last_result else "None"
        previous_searches = user_context.get('previous_searches', [])
        prev_searches_text = ", ".join(previous_searches[:3]) if previous_searches else "None"
        
        return self.INTERPRETATION_PROMPT.format(
            conversation_history=conv_text,
            user_location=user_context.get('location', 'Unknown'),
            previous_searches=prev_searches_text,
            last_result=last_result_text,
            user_query=user_query
        )
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API (Claude, etc.)"""
        if self.llm_client:
            # Actual API call
            response = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        return ""
    
    def _simulate_interpretation(
        self,
        user_query: str,
        conversation_history: List[Dict],
        user_context: Dict
    ) -> str:
        """Simulate intelligent interpretation for testing/demonstration."""
        query_lower = user_query.lower()
        
        # Detect intent
        if any(word in query_lower for word in ['find', 'search', 'look for', 'locate']):
            intent = "search"
        elif any(word in query_lower for word in ['add', 'insert', 'save', 'store']):
            intent = "add"
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            intent = "compare"
        elif any(word in query_lower for word in ['list', 'show all', 'how many']):
            intent = "list"
        else:
            intent = "search"
        
        # Extract provider names (simple pattern matching)
        providers = []
        provider_patterns = [
            r'home instead',
            r'comfort keepers?',
            r'ck\b',
            r'visiting angels?',
            r'brightstar care',
            r'gcp reit',
        ]
        
        for pattern in provider_patterns:
            if re.search(pattern, query_lower):
                name = re.search(pattern, query_lower).group(0)
                # Normalize abbreviations
                if name == 'ck':
                    name = 'Comfort Keepers'
                providers.append({"name": name.title(), "location": None})
        
        # Extract location
        state_match = re.search(r'\b([A-Z]{2})\b', user_query)
        city_match = re.search(r'in ([A-Z][a-z]+(?: [A-Z][a-z]+)*)', user_query)
        
        filters = {}
        if state_match:
            filters['state'] = state_match.group(1)
        if city_match:
            filters['city'] = city_match.group(1)
        
        # Handle "near me"
        references_resolved = {}
        if 'near me' in query_lower or 'local' in query_lower:
            user_location = user_context.get('location', '')
            references_resolved['near me'] = user_location
            if user_location and ',' in user_location:
                city, state = user_location.split(',')
                filters['city'] = city.strip()
                filters['state'] = state.strip()
        
        # Pronoun resolution
        if any(word in query_lower for word in ['their', 'they', 'them']):
            # Look for last mentioned provider
            for turn in reversed(conversation_history):
                if turn['role'] == 'assistant':
                    # Extract provider name from previous response
                    for pattern in provider_patterns:
                        match = re.search(pattern, turn['content'].lower())
                        if match:
                            references_resolved['their'] = match.group(0).title()
                            if not providers:
                                providers.append({"name": match.group(0).title(), "location": None})
                            break
                    if 'their' in references_resolved:
                        break
        
        if any(word in query_lower for word in ['that', 'this', 'it']):
            if self.last_result:
                ref_name = self.last_result.get('name', 'last result')
                references_resolved['that'] = ref_name
                if intent == 'add' and not providers:
                    providers.append({"name": ref_name, "location": None})
        
        # Multi-step planning
        multi_step = []
        if 'compare' in query_lower and len(providers) > 1:
            multi_step = [
                f"Step 1: Search for {providers[0]['name']}",
                f"Step 2: Search for {providers[1]['name']}",
                "Step 3: Compare locations, coverage, services"
            ]
        
        # Check for ambiguity
        clarification = None
        if not providers and intent in ['search', 'add']:
            clarification = "Which provider are you looking for?"
        elif not filters.get('state') and intent == 'list':
            clarification = "Which state would you like me to search in?"
        
        confidence = 0.9 if providers else 0.5
        
        result = {
            "intent": intent,
            "providers": providers,
            "filters": filters,
            "references_resolved": references_resolved,
            "multi_step_plan": multi_step,
            "clarification_needed": clarification,
            "confidence": confidence,
            "reasoning": f"Detected {intent} intent with {len(providers)} providers"
        }
        
        return json.dumps(result, indent=2)
    
    def _parse_llm_response(self, response: str) -> ParsedQuery:
        """Parse LLM JSON response into ParsedQuery object."""
        # Extract JSON from response (may be wrapped in markdown)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        data = json.loads(response)
        
        return ParsedQuery(
            intent=Intent(data['intent']),
            providers=data.get('providers', []),
            filters=data.get('filters', {}),
            references_resolved=data.get('references_resolved', {}),
            multi_step_plan=data.get('multi_step_plan', []),
            clarification_needed=data.get('clarification_needed'),
            confidence=data.get('confidence', 0.0),
            raw_interpretation=data.get('reasoning', response)
        )
    
    def update_last_result(self, result: Dict):
        """Update the last result cache for reference resolution."""
        self.last_result = result
    
    def clear_context(self):
        """Clear conversation and result cache."""
        self.conversation_cache = []
        self.last_result = None
