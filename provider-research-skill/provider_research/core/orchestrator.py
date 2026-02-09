"""
Provider Research Orchestrator
===============================
Main Orchestrator for Multi-Skill Provider Research System

Purpose:
    Coordinate all 4 skills to execute complete provider research workflows.
    Manages state, handles errors, optimizes token usage through short-circuiting.

Architecture:
    Skill 1: Query Interpreter  → Understands user intent
    Skill 2: Database Manager   → Fast rule-based search
    Skill 3: Semantic Matcher   → Intelligent matching
    Skill 4: Web Researcher     → Deep research & validation
    
    Orchestrator: Coordinates flow, manages state, provides unified interface

Usage:
    from provider_research import ProviderOrchestrator
    
    orchestrator = ProviderOrchestrator(db_config, api_key)
    result = orchestrator.process_query(
        user_query="Find Home Instead near me",
        conversation_history=[...],
        user_context={"location": "Boston, MA"}
    )
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from ..core.query_interpreter import ProviderQueryInterpreter, Intent, ParsedQuery
from ..database.manager import ProviderDatabaseManager, SearchResult
from ..core.semantic_matcher import ProviderSemanticMatcher, SemanticMatch
from ..search.web_researcher import ProviderWebResearcher, ResearchResult, DeduplicationResult


class ExecutionPath(Enum):
    """Execution paths through the system"""
    DB_HIT = "database_hit"              # Found in database (cheapest)
    SEMANTIC = "semantic_match"          # Semantic matching needed
    WEB_RESEARCH = "web_research"        # Full web research (expensive)
    MULTI_STEP = "multi_step"           # Complex multi-step query
    CLARIFICATION = "clarification_needed"  # Need user input


@dataclass
class OrchestrationResult:
    """Complete result from orchestration"""
    success: bool
    execution_path: ExecutionPath
    intent: Intent
    providers: List[Dict]
    message: str
    confidence: float
    token_usage: Dict[str, int]
    execution_time_ms: float
    steps_executed: List[str]
    warnings: List[str]
    clarification_question: Optional[str]
    raw_data: Dict


class ProviderOrchestrator:
    """
    Main Orchestrator - Coordinates All Skills
    
    Responsibilities:
    1. Route queries through appropriate skills
    2. Manage conversation state and context
    3. Optimize token usage via short-circuiting
    4. Handle errors and edge cases
    5. Provide unified response interface
    """
    
    def __init__(
        self,
        db_config: Dict = None,
        llm_client = None,
        web_search_fn = None,
        web_fetch_fn = None,
        auto_save: bool = False
    ):
        """
        Initialize orchestrator with all skills.
        
        Args:
            db_config: Database configuration
            llm_client: LLM client for AI-powered skills
            web_search_fn: Function for web search
            web_fetch_fn: Function for web content fetching
            auto_save: Automatically save research results to DB
        """
        # Initialize all skills
        self.interpreter = ProviderQueryInterpreter(llm_client)
        self.database = ProviderDatabaseManager(db_config)
        self.matcher = ProviderSemanticMatcher(llm_client)
        self.researcher = ProviderWebResearcher(llm_client, web_search_fn, web_fetch_fn)
        
        # Configuration
        self.llm_client = llm_client
        self.auto_save = auto_save
        
        # State management
        self.conversation_history = []
        self.user_context = {}
        self.last_result = None
        
        # Metrics
        self.total_token_usage = {
            'interpreter': 0,
            'matcher': 0,
            'researcher': 0,
            'total': 0
        }
    
    def process_query(
        self,
        user_query: str,
        conversation_history: List[Dict] = None,
        user_context: Dict = None
    ) -> OrchestrationResult:
        """
        Main entry point - process a user query through the system.
        
        Args:
            user_query: Natural language query
            conversation_history: Recent conversation turns
            user_context: User location, preferences, etc.
        
        Returns:
            OrchestrationResult with complete response
        """
        start_time = datetime.utcnow()
        steps = []
        warnings = []
        token_usage = {'interpreter': 0, 'matcher': 0, 'researcher': 0}
        
        # Update state
        if conversation_history:
            self.conversation_history = conversation_history
        if user_context:
            self.user_context = user_context
        
        try:
            # ===== STEP 1: INTERPRET QUERY (Layer 0) =====
            steps.append("Step 1: Interpreting query")
            parsed = self.interpreter.interpret(
                user_query,
                self.conversation_history,
                self.user_context
            )
            token_usage['interpreter'] = 800  # Estimated
            
            # Check if clarification needed
            if parsed.clarification_needed:
                return self._build_clarification_response(parsed, start_time, steps, token_usage)
            
            # Update conversation
            self._update_conversation(user_query, parsed)
            
            # Route based on intent
            if parsed.intent == Intent.ADD:
                return self._handle_add_intent(parsed, start_time, steps, token_usage, warnings)
            elif parsed.intent == Intent.COMPARE:
                return self._handle_compare_intent(parsed, start_time, steps, token_usage, warnings)
            elif parsed.intent == Intent.LIST:
                return self._handle_list_intent(parsed, start_time, steps, token_usage, warnings)
            else:  # SEARCH, RESEARCH, VERIFY, etc.
                return self._handle_search_intent(parsed, start_time, steps, token_usage, warnings)
        
        except Exception as e:
            return self._build_error_response(str(e), start_time, steps, token_usage)
    
    def _handle_search_intent(
        self,
        parsed: ParsedQuery,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict,
        warnings: List[str]
    ) -> OrchestrationResult:
        """Handle search/research intents."""
        
        if not parsed.providers:
            warnings.append("No provider specified in query")
            return self._build_result(
                success=False,
                path=ExecutionPath.CLARIFICATION,
                intent=parsed.intent,
                providers=[],
                message="Could not identify which provider to search for",
                confidence=0.0,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings,
                clarification="Which healthcare provider are you looking for?"
            )
        
        provider_query = parsed.providers[0]
        provider_name = provider_query.get('name', '')
        
        # ===== STEP 2: DATABASE SEARCH (Layer 1) =====
        steps.append(f"Step 2: Searching database for '{provider_name}'")
        db_results = self.database.search(
            query=provider_name,
            state=parsed.filters.get('state'),
            city=parsed.filters.get('city'),
            parent_organization=parsed.filters.get('parent_organization'),
            fuzzy=True
        )
        
        # Short-circuit: High confidence DB match
        if db_results and db_results[0].confidence >= 0.85:
            providers = [result.provider for result in db_results]
            self.last_result = providers[0]
            self.interpreter.update_last_result(providers[0])
            
            return self._build_result(
                success=True,
                path=ExecutionPath.DB_HIT,
                intent=parsed.intent,
                providers=providers,
                message=f"Found {len(providers)} provider(s) in database",
                confidence=db_results[0].confidence,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings
            )
        
        # ===== STEP 3: SEMANTIC MATCHING (Layer 2) =====
        steps.append("Step 3: No high-confidence DB match, trying semantic matching")
        
        # Get candidate records for semantic matching
        candidates = [result.provider for result in db_results] if db_results else []
        
        # If no candidates, get some from database to match against
        if not candidates:
            all_providers = self.database.search(
                state=parsed.filters.get('state'),
                limit=50
            )
            candidates = [result.provider for result in all_providers]
        
        if candidates:
            semantic_matches = self.matcher.match(
                query=provider_name,
                candidates=candidates,
                location_filter=parsed.filters,
                threshold=0.7
            )
            token_usage['matcher'] = 500  # Estimated
            
            # Short-circuit: Good semantic match
            if semantic_matches and semantic_matches[0].confidence >= 0.8:
                # Get full provider records
                providers = [
                    self.database.search(npi=match.provider_id)[0].provider
                    if self.database.search(npi=match.provider_id)
                    else {'id': match.provider_id, 'legal_name': match.provider_name}
                    for match in semantic_matches
                ]
                
                self.last_result = providers[0]
                self.interpreter.update_last_result(providers[0])
                
                return self._build_result(
                    success=True,
                    path=ExecutionPath.SEMANTIC,
                    intent=parsed.intent,
                    providers=providers,
                    message=f"Found {len(providers)} provider(s) via semantic matching",
                    confidence=semantic_matches[0].confidence,
                    start_time=start_time,
                    steps=steps,
                    token_usage=token_usage,
                    warnings=warnings
                )
        
        # ===== STEP 4: WEB RESEARCH (Layers 3-5) =====
        steps.append("Step 4: No DB/semantic match, conducting web research")
        
        research_result = self.researcher.research(
            provider_name=provider_name,
            location=provider_query.get('location'),
            state=parsed.filters.get('state')
        )
        token_usage['researcher'] = 5000  # Estimated (extraction + dedup + NPI)
        
        if research_result.locations:
            # Check for duplicates before saving
            for location in research_result.locations:
                if self.auto_save:
                    # Check if duplicate
                    existing = self.database.search(
                        phone=location.get('phone'),
                        limit=1
                    )
                    
                    if existing:
                        dup_check = self.researcher.check_duplicate(location, existing[0].provider)
                        if not dup_check.is_duplicate:
                            provider_id = self.database.add_provider(location)
                            location['id'] = provider_id
                    else:
                        provider_id = self.database.add_provider(location)
                        location['id'] = provider_id
            
            self.last_result = research_result.locations[0]
            self.interpreter.update_last_result(research_result.locations[0])
            
            message = f"Found {len(research_result.locations)} location(s) via web research"
            if self.auto_save:
                message += " (saved to database)"
            else:
                message += " (not saved - use auto_save=True to save automatically)"
            
            return self._build_result(
                success=True,
                path=ExecutionPath.WEB_RESEARCH,
                intent=parsed.intent,
                providers=research_result.locations,
                message=message,
                confidence=research_result.confidence,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings + research_result.warnings
            )
        else:
            return self._build_result(
                success=False,
                path=ExecutionPath.WEB_RESEARCH,
                intent=parsed.intent,
                providers=[],
                message=f"Could not find '{provider_name}' in database or web research",
                confidence=0.0,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings + research_result.warnings
            )
    
    def _handle_add_intent(
        self,
        parsed: ParsedQuery,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict,
        warnings: List[str]
    ) -> OrchestrationResult:
        """Handle add-to-database intent."""
        steps.append("Step 2: Adding provider to database")
        
        if not parsed.providers:
            warnings.append("No provider data to add")
            return self._build_result(
                success=False,
                path=ExecutionPath.CLARIFICATION,
                intent=parsed.intent,
                providers=[],
                message="No provider data specified to add",
                confidence=0.0,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings,
                clarification="What provider information should I add?"
            )
        
        provider_data = parsed.providers[0]
        
        # Check for duplicates
        existing = self.database.search(
            query=provider_data.get('name', ''),
            phone=provider_data.get('phone'),
            limit=5
        )
        
        if existing:
            dup_check = self.researcher.check_duplicate(provider_data, existing[0].provider)
            if dup_check.is_duplicate:
                return self._build_result(
                    success=False,
                    path=ExecutionPath.DB_HIT,
                    intent=parsed.intent,
                    providers=[existing[0].provider],
                    message=f"Provider already exists in database: {dup_check.reason}",
                    confidence=dup_check.confidence,
                    start_time=start_time,
                    steps=steps,
                    token_usage=token_usage,
                    warnings=warnings
                )
        
        # Add to database
        provider_id = self.database.add_provider({
            'legal_name': provider_data.get('name'),
            'address': provider_data.get('address'),
            'city': provider_data.get('city'),
            'state': provider_data.get('state'),
            'phone': provider_data.get('phone'),
            'npi': provider_data.get('npi')
        })
        
        provider_data['id'] = provider_id
        
        return self._build_result(
            success=True,
            path=ExecutionPath.DB_HIT,
            intent=parsed.intent,
            providers=[provider_data],
            message=f"Successfully added provider to database (ID: {provider_id})",
            confidence=0.95,
            start_time=start_time,
            steps=steps,
            token_usage=token_usage,
            warnings=warnings
        )
    
    def _handle_compare_intent(
        self,
        parsed: ParsedQuery,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict,
        warnings: List[str]
    ) -> OrchestrationResult:
        """Handle comparison intent."""
        steps.append("Step 2: Comparing providers")
        
        if len(parsed.providers) < 2:
            return self._build_result(
                success=False,
                path=ExecutionPath.CLARIFICATION,
                intent=parsed.intent,
                providers=[],
                message="Need at least 2 providers to compare",
                confidence=0.0,
                start_time=start_time,
                steps=steps,
                token_usage=token_usage,
                warnings=warnings,
                clarification="Which providers would you like to compare?"
            )
        
        # Search for each provider
        comparison_results = []
        for provider_query in parsed.providers[:5]:  # Limit to 5
            results = self.database.search(
                query=provider_query.get('name'),
                state=parsed.filters.get('state'),
                limit=10
            )
            comparison_results.append({
                'query': provider_query.get('name'),
                'results': [r.provider for r in results]
            })
        
        return self._build_result(
            success=True,
            path=ExecutionPath.MULTI_STEP,
            intent=parsed.intent,
            providers=comparison_results,
            message=f"Comparison results for {len(parsed.providers)} providers",
            confidence=0.85,
            start_time=start_time,
            steps=steps,
            token_usage=token_usage,
            warnings=warnings
        )
    
    def _handle_list_intent(
        self,
        parsed: ParsedQuery,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict,
        warnings: List[str]
    ) -> OrchestrationResult:
        """Handle list/inventory intent."""
        steps.append("Step 2: Listing providers")
        
        results = self.database.search(
            state=parsed.filters.get('state'),
            city=parsed.filters.get('city'),
            parent_organization=parsed.filters.get('parent_organization'),
            limit=100
        )
        
        providers = [r.provider for r in results]
        
        return self._build_result(
            success=True,
            path=ExecutionPath.DB_HIT,
            intent=parsed.intent,
            providers=providers,
            message=f"Found {len(providers)} providers matching filters",
            confidence=0.9,
            start_time=start_time,
            steps=steps,
            token_usage=token_usage,
            warnings=warnings
        )
    
    def _build_result(
        self,
        success: bool,
        path: ExecutionPath,
        intent: Intent,
        providers: List,
        message: str,
        confidence: float,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict,
        warnings: List[str] = None,
        clarification: str = None
    ) -> OrchestrationResult:
        """Build orchestration result."""
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        total_tokens = sum(token_usage.values())
        
        return OrchestrationResult(
            success=success,
            execution_path=path,
            intent=intent,
            providers=providers,
            message=message,
            confidence=confidence,
            token_usage={**token_usage, 'total': total_tokens},
            execution_time_ms=execution_time,
            steps_executed=steps,
            warnings=warnings or [],
            clarification_question=clarification,
            raw_data={
                'conversation_history': self.conversation_history[-3:],
                'user_context': self.user_context
            }
        )
    
    def _build_clarification_response(
        self,
        parsed: ParsedQuery,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict
    ) -> OrchestrationResult:
        """Build clarification response."""
        return self._build_result(
            success=False,
            path=ExecutionPath.CLARIFICATION,
            intent=parsed.intent,
            providers=[],
            message="Need clarification before proceeding",
            confidence=parsed.confidence,
            start_time=start_time,
            steps=steps,
            token_usage=token_usage,
            warnings=[],
            clarification=parsed.clarification_needed
        )
    
    def _build_error_response(
        self,
        error: str,
        start_time: datetime,
        steps: List[str],
        token_usage: Dict
    ) -> OrchestrationResult:
        """Build error response."""
        return self._build_result(
            success=False,
            path=ExecutionPath.CLARIFICATION,
            intent=Intent.CLARIFY,
            providers=[],
            message=f"Error processing query: {error}",
            confidence=0.0,
            start_time=start_time,
            steps=steps,
            token_usage=token_usage,
            warnings=[error]
        )
    
    def _update_conversation(self, user_query: str, parsed: ParsedQuery):
        """Update conversation history."""
        self.conversation_history.append({
            'role': 'user',
            'content': user_query,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_stats(self) -> Dict:
        """Get orchestrator statistics."""
        db_stats = self.database.get_stats()
        
        return {
            'database': db_stats,
            'token_usage': self.total_token_usage,
            'conversation_turns': len(self.conversation_history)
        }
    
    def reset(self):
        """Reset orchestrator state."""
        self.conversation_history = []
        self.user_context = {}
        self.last_result = None
        self.interpreter.clear_context()
    
    def close(self):
        """Clean up resources."""
        self.database.close()
