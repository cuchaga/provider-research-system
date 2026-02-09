#!/usr/bin/env python3
"""
Provider Research Orchestrator - Usage Examples
================================================
Demonstrates the multi-skill architecture with orchestrator.

Shows:
- Basic search workflow
- Conversation with context
- Different execution paths
- Token usage tracking
"""

from provider_orchestrator import ProviderOrchestrator, ExecutionPath


def print_result(result, query_num):
    """Pretty print orchestration result."""
    print(f"\n{'='*80}")
    print(f"QUERY {query_num} RESULT")
    print(f"{'='*80}")
    print(f"Success: {result.success}")
    print(f"Execution Path: {result.execution_path.value}")
    print(f"Intent: {result.intent.value}")
    print(f"Message: {result.message}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Execution Time: {result.execution_time_ms:.1f}ms")
    print(f"\nToken Usage:")
    for skill, tokens in result.token_usage.items():
        print(f"  {skill}: {tokens}")
    print(f"\nSteps Executed:")
    for step in result.steps_executed:
        print(f"  - {step}")
    print(f"\nProviders Found: {len(result.providers)}")
    if result.providers:
        for i, provider in enumerate(result.providers[:3], 1):
            print(f"\n  Provider {i}:")
            print(f"    Name: {provider.get('legal_name', provider.get('name', 'N/A'))}")
            print(f"    City: {provider.get('address_city', provider.get('city', 'N/A'))}")
            print(f"    State: {provider.get('address_state', provider.get('state', 'N/A'))}")
    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
    if result.clarification_question:
        print(f"\n❓ Clarification Needed: {result.clarification_question}")


def example_1_basic_search():
    """Example 1: Basic provider search."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Provider Search")
    print("="*80)
    
    # Initialize orchestrator
    orchestrator = ProviderOrchestrator()
    
    # Simple search
    result = orchestrator.process_query(
        user_query="Find Home Instead in Massachusetts",
        user_context={"location": "Boston, MA"}
    )
    
    print_result(result, 1)
    
    # Cleanup
    orchestrator.close()


def example_2_conversation_flow():
    """Example 2: Multi-turn conversation with context."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Conversation Flow with Pronoun Resolution")
    print("="*80)
    
    orchestrator = ProviderOrchestrator()
    
    # Turn 1: Initial search
    print("\n--- Turn 1: User asks about Home Instead ---")
    result1 = orchestrator.process_query(
        user_query="Find Home Instead in Boston",
        user_context={"location": "Boston, MA"}
    )
    print_result(result1, "1a")
    
    # Turn 2: Follow-up using "their" (should resolve to Home Instead)
    print("\n--- Turn 2: User asks about 'their other locations' ---")
    conversation = [
        {"role": "user", "content": "Find Home Instead in Boston"},
        {"role": "assistant", "content": "Found Home Instead - Metrowest in Wellesley, MA"}
    ]
    
    result2 = orchestrator.process_query(
        user_query="What about their other locations in Michigan?",
        conversation_history=conversation,
        user_context={"location": "Boston, MA"}
    )
    print_result(result2, "1b")
    
    orchestrator.close()


def example_3_different_paths():
    """Example 3: Demonstrate different execution paths."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Different Execution Paths")
    print("="*80)
    
    orchestrator = ProviderOrchestrator()
    
    # Path 1: Database hit (cheapest - ~800 tokens)
    print("\n--- Path 1: Database Hit (Exact Match) ---")
    result1 = orchestrator.process_query(
        user_query="Find Home Instead - Metrowest",
        user_context={"location": "Boston, MA"}
    )
    print(f"Execution Path: {result1.execution_path.value}")
    print(f"Total Tokens: {result1.token_usage['total']}")
    
    # Path 2: Semantic matching (~1,300 tokens)
    print("\n--- Path 2: Semantic Match (Abbreviation) ---")
    result2 = orchestrator.process_query(
        user_query="Find CK in Michigan",
        user_context={"location": "Detroit, MI"}
    )
    print(f"Execution Path: {result2.execution_path.value}")
    print(f"Total Tokens: {result2.token_usage['total']}")
    
    # Path 3: Web research (~5,800 tokens)
    print("\n--- Path 3: Web Research (Not in DB) ---")
    result3 = orchestrator.process_query(
        user_query="Find Synergy HomeCare in California",
        user_context={"location": "Los Angeles, CA"}
    )
    print(f"Execution Path: {result3.execution_path.value}")
    print(f"Total Tokens: {result3.token_usage['total']}")
    
    # Path 4: Clarification needed
    print("\n--- Path 4: Clarification Needed (Ambiguous Query) ---")
    result4 = orchestrator.process_query(
        user_query="Find them",
        user_context={}
    )
    print(f"Execution Path: {result4.execution_path.value}")
    print(f"Clarification: {result4.clarification_question}")
    
    orchestrator.close()


def example_4_add_provider():
    """Example 4: Add provider to database."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Add Provider Intent")
    print("="*80)
    
    orchestrator = ProviderOrchestrator(auto_save=True)
    
    result = orchestrator.process_query(
        user_query="Add Synergy HomeCare at 123 Main St, Los Angeles, CA 90001 phone (213) 555-0100"
    )
    
    print_result(result, 4)
    
    orchestrator.close()


def example_5_compare_providers():
    """Example 5: Compare multiple providers."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Compare Providers")
    print("="*80)
    
    orchestrator = ProviderOrchestrator()
    
    result = orchestrator.process_query(
        user_query="Compare Home Instead vs Visiting Angels in Massachusetts",
        user_context={"location": "Boston, MA"}
    )
    
    print_result(result, 5)
    
    orchestrator.close()


def example_6_orchestrator_stats():
    """Example 6: View orchestrator statistics."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Orchestrator Statistics")
    print("="*80)
    
    orchestrator = ProviderOrchestrator()
    
    # Run a few queries
    orchestrator.process_query("Find Home Instead in MA")
    orchestrator.process_query("Find Comfort Keepers in MI")
    orchestrator.process_query("List all providers in Boston")
    
    # Get stats
    stats = orchestrator.get_stats()
    
    print("\nDatabase Statistics:")
    print(f"  Total Providers: {stats['database']['total_providers']}")
    print(f"  States Covered: {stats['database']['states_covered']}")
    print(f"  With NPI: {stats['database']['with_npi']}")
    
    print("\nOrchestrator Statistics:")
    print(f"  Conversation Turns: {stats['conversation_turns']}")
    print(f"  Total Token Usage: {stats['token_usage']['total']}")
    
    orchestrator.close()


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("PROVIDER RESEARCH ORCHESTRATOR - USAGE EXAMPLES")
    print("="*80)
    print("\nDemonstrating multi-skill architecture with central orchestrator")
    print("Skills: Query Interpreter, Database Manager, Semantic Matcher, Web Researcher")
    
    try:
        # Run examples
        example_1_basic_search()
        example_2_conversation_flow()
        example_3_different_paths()
        example_4_add_provider()
        example_5_compare_providers()
        example_6_orchestrator_stats()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
