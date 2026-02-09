#!/usr/bin/env python3
"""
Basic Usage Example - Provider Research System
=============================================

This example demonstrates basic usage of the Provider Research System v2.0.
"""

from provider_research import (
    ProviderOrchestrator,
    ProviderDatabaseManager,
    ProviderQueryInterpreter
)


def example_1_simple_search():
    """Example 1: Simple provider search."""
    print("=" * 80)
    print("Example 1: Simple Provider Search")
    print("=" * 80)
    
    # Initialize database manager
    db = ProviderDatabaseManager(auto_connect=False)
    
    # Note: In production, you would connect to your database
    # db.connect()
    
    print("\n✅ Database manager initialized")
    print("   (Use db.search() to search for providers)")
    print("   (Use db.add_provider() to add new providers)")


def example_2_query_interpretation():
    """Example 2: Natural language query interpretation."""
    print("\n" + "=" * 80)
    print("Example 2: Natural Language Query Interpretation")
    print("=" * 80)
    
    # Initialize interpreter
    interpreter = ProviderQueryInterpreter(llm_client=None)
    
    # Example query
    user_query = "Find Home Instead locations in Massachusetts"
    
    print(f"\nUser Query: '{user_query}'")
    print("\nThe interpreter will:")
    print("  1. Identify intent: SEARCH")
    print("  2. Extract entities: provider_name='Home Instead', state='MA'")
    print("  3. Generate search parameters")
    
    print("\n✅ Query interpreter ready")


def example_3_full_workflow():
    """Example 3: Complete workflow with orchestrator."""
    print("\n" + "=" * 80)
    print("Example 3: Complete Workflow with Orchestrator")
    print("=" * 80)
    
    # Initialize orchestrator
    # Note: Pass your database config and LLM client
    orchestrator = ProviderOrchestrator(
        db_config=None,  # Your config here
        llm_client=None,  # Your LLM client here
        auto_save=False
    )
    
    print("\n✅ Orchestrator initialized")
    print("\nWorkflow:")
    print("  1. User query → Query Interpreter (natural language understanding)")
    print("  2. Database search → Database Manager (fast lookup)")
    print("  3. Semantic matching → Semantic Matcher (if needed)")
    print("  4. Web research → Web Researcher (if database miss)")
    print("  5. Return results with confidence scores")
    
    # Example usage
    print("\n📝 Example Code:")
    print("""
    result = orchestrator.process_query(
        user_query="Find Home Instead near me",
        user_context={"location": "Boston, MA"}
    )
    
    print(f"Found {len(result.providers)} providers")
    print(f"Confidence: {result.confidence}")
    print(f"Execution path: {result.execution_path}")
    """)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PROVIDER RESEARCH SYSTEM v2.0" + " " * 29 + "║")
    print("║" + " " * 26 + "Basic Usage Examples" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    
    example_1_simple_search()
    example_2_query_interpretation()
    example_3_full_workflow()
    
    print("\n" + "=" * 80)
    print("💡 Next Steps:")
    print("=" * 80)
    print("\n1. Set up your database (see docs/guides/database-setup.md)")
    print("2. Configure your LLM client (Anthropic or OpenAI)")
    print("3. Try advanced examples (examples/advanced_orchestration.py)")
    print("4. Read the full documentation (docs/)")
    print("\n")


if __name__ == "__main__":
    main()
