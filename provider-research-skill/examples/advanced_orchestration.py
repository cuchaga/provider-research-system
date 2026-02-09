#!/usr/bin/env python3
"""
Advanced Orchestration Example - Provider Research System
========================================================

This example demonstrates advanced multi-step workflows and custom configurations.
"""

from provider_research import (
    ProviderOrchestrator,
    ExecutionPath,
    Intent
)
from provider_research.utils import get_logger, format_search_results


# Setup logging
logger = get_logger(__name__, level='INFO')


def example_1_multi_step_query():
    """Example: Complex multi-step query."""
    print("=" * 80)
    print("Example 1: Multi-Step Query")
    print("=" * 80)
    
    query = """
    Find all Home Instead locations in Massachusetts, 
    then compare them with Visiting Angels in the same area
    """
    
    print(f"\nQuery: {query}")
    print("\nOrchestrator will:")
    print("  Step 1: Search for Home Instead in MA")
    print("  Step 2: Search for Visiting Angels in MA")
    print("  Step 3: Compare results")
    print("  Step 4: Return comparative analysis")
    
    logger.info("Multi-step query processed")


def example_2_custom_workflow():
    """Example: Custom workflow with specific execution path."""
    print("\n" + "=" * 80)
    print("Example 2: Custom Workflow")
    print("=" * 80)
    
    print("\nScenario: Force web research even if database has results")
    print("\n📝 Code:")
    print("""
    orchestrator = ProviderOrchestrator(
        db_config=db_config,
        llm_client=llm_client,
        auto_save=True  # Automatically save research results to DB
    )
    
    result = orchestrator.process_query(
        user_query="Research latest Home Instead acquisitions",
        force_web_research=True  # Skip database, go straight to web
    )
    """)
    
    logger.info("Custom workflow configured")


def example_3_error_handling():
    """Example: Robust error handling."""
    print("\n" + "=" * 80)
    print("Example 3: Error Handling")
    print("=" * 80)
    
    print("\n📝 Code:")
    print("""
    from provider_research.exceptions import (
        DatabaseError,
        LLMError,
        ValidationError
    )
    
    try:
        result = orchestrator.process_query(user_query)
        
        if result.success:
            print(f"Success: {result.message}")
            print(f"Found {len(result.providers)} providers")
        else:
            print(f"Failed: {result.message}")
            if result.clarification_question:
                # Ask user for clarification
                print(f"Clarification needed: {result.clarification_question}")
                
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
    except LLMError as e:
        logger.error(f"LLM error: {e}")
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
    """)


def example_4_monitoring_metrics():
    """Example: Monitoring and metrics."""
    print("\n" + "=" * 80)
    print("Example 4: Monitoring & Metrics")
    print("=" * 80)
    
    print("\nTrack performance metrics:")
    print("""
    result = orchestrator.process_query(user_query)
    
    # Performance metrics
    print(f"Execution time: {result.execution_time_ms}ms")
    print(f"Execution path: {result.execution_path}")
    print(f"Steps executed: {result.steps_executed}")
    print(f"Token usage: {result.token_usage}")
    
    # Cost estimation
    if result.execution_path == ExecutionPath.DB_HIT:
        print("Cost: $0 (database only, no LLM calls)")
    elif result.execution_path == ExecutionPath.SEMANTIC:
        print("Cost: ~$0.01 (1 LLM call for matching)")
    elif result.execution_path == ExecutionPath.WEB_RESEARCH:
        print("Cost: ~$0.05 (multiple LLM calls)")
    """)


def main():
    """Run all advanced examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PROVIDER RESEARCH SYSTEM v2.0" + " " * 29 + "║")
    print("║" + " " * 21 + "Advanced Orchestration Examples" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    
    example_1_multi_step_query()
    example_2_custom_workflow()
    example_3_error_handling()
    example_4_monitoring_metrics()
    
    print("\n" + "=" * 80)
    print("✅ All examples demonstrated")
    print("=" * 80)
    print("\n")


if __name__ == "__main__":
    main()
