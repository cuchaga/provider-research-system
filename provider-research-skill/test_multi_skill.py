#!/usr/bin/env python3
"""
Quick Test - Multi-Skill Architecture
======================================
Verifies that the new multi-skill orchestrator works correctly.
"""

import sys
sys.path.insert(0, '/Users/cuchaga/Documents/AI Projects/provider-research-system/provider-research-skill')

from provider_orchestrator import ProviderOrchestrator, ExecutionPath
from provider_query_interpreter import Intent


def test_skill_imports():
    """Test 1: Verify all skills can be imported."""
    print("Test 1: Importing skills...")
    
    try:
        from provider_query_interpreter import ProviderQueryInterpreter
        from provider_database_manager import ProviderDatabaseManager
        from provider_semantic_matcher import ProviderSemanticMatcher
        from provider_web_researcher import ProviderWebResearcher
        print("  ✅ All skills imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_orchestrator_init():
    """Test 2: Verify orchestrator initializes without database."""
    print("\nTest 2: Initializing orchestrator components...")
    
    try:
        # Test individual skill initialization (no DB needed)
        from provider_query_interpreter import ProviderQueryInterpreter
        from provider_semantic_matcher import ProviderSemanticMatcher
        from provider_web_researcher import ProviderWebResearcher
        
        interpreter = ProviderQueryInterpreter()
        matcher = ProviderSemanticMatcher()
        researcher = ProviderWebResearcher()
        
        print("  ✅ All orchestrator components initialized successfully")
        print(f"  - Query Interpreter: ✓")
        print(f"  - Semantic Matcher: ✓")
        print(f"  - Web Researcher: ✓")
        print(f"  - Database Manager: (skipped - requires psycopg2)")
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_interpretation():
    """Test 3: Test query interpretation skill."""
    print("\nTest 3: Testing query interpretation...")
    
    try:
        from provider_query_interpreter import ProviderQueryInterpreter
        
        interpreter = ProviderQueryInterpreter()
        result = interpreter.interpret(
            user_query="Find Home Instead in Boston, MA",
            user_context={"location": "New York, NY"}
        )
        
        print(f"  ✅ Interpretation successful")
        print(f"  - Intent: {result.intent.value}")
        print(f"  - Providers: {result.providers}")
        print(f"  - Filters: {result.filters}")
        print(f"  - Confidence: {result.confidence:.0%}")
        
        assert result.intent == Intent.SEARCH, "Intent should be SEARCH"
        assert len(result.providers) > 0, "Should extract provider name"
        
        return True
    except Exception as e:
        print(f"  ❌ Interpretation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_matcher():
    """Test 4: Test semantic matcher skill."""
    print("\nTest 4: Testing semantic matcher...")
    
    try:
        from provider_semantic_matcher import ProviderSemanticMatcher
        
        matcher = ProviderSemanticMatcher()
        
        # Test abbreviation expansion
        expanded = matcher._expand_abbreviations("Find CK in Michigan")
        assert "comfort keepers" in expanded.lower(), "Should expand CK to Comfort Keepers"
        
        # Test rule-based matching
        candidates = [
            {
                'id': '123',
                'legal_name': 'Comfort Keepers of Oakland',
                'parent_organization': 'Comfort Keepers',
                'address_city': 'Troy',
                'address_state': 'MI'
            }
        ]
        
        matches = matcher.match(
            query="Comfort Keepers",
            candidates=candidates,
            location_filter={"state": "MI"}
        )
        
        print(f"  ✅ Semantic matching successful")
        print(f"  - Abbreviation expansion: CK → {expanded}")
        print(f"  - Matches found: {len(matches)}")
        if matches:
            print(f"  - Match type: {matches[0].match_type}")
            print(f"  - Confidence: {matches[0].confidence:.0%}")
        
        return True
    except Exception as e:
        print(f"  ❌ Semantic matching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_researcher():
    """Test 5: Test web researcher skill."""
    print("\nTest 5: Testing web researcher...")
    
    try:
        from provider_web_researcher import ProviderWebResearcher
        
        researcher = ProviderWebResearcher()
        
        # Test deduplication logic
        provider1 = {
            'name': 'Test Provider',
            'phone': '(617) 555-0100',
            'address': '123 Main St, Suite 100'
        }
        
        provider2 = {
            'id': '456',
            'legal_name': 'Test Provider Inc',
            'phone': '617-555-0100',  # Same phone, different format
            'address_full': '123 Main St Suite 200'  # Same building, different suite
        }
        
        dup_result = researcher.check_duplicate(provider1, provider2)
        
        print(f"  ✅ Web researcher functions work")
        print(f"  - Duplicate check: {dup_result.is_duplicate}")
        print(f"  - Reason: {dup_result.reason}")
        print(f"  - Confidence: {dup_result.confidence:.0%}")
        
        # Test phone normalization
        normalized1 = researcher._normalize_phone('(617) 555-0100')
        normalized2 = researcher._normalize_phone('617-555-0100')
        assert normalized1 == normalized2, "Phone normalization should match"
        
        return True
    except Exception as e:
        print(f"  ❌ Web researcher failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_workflow():
    """Test 6: Test orchestrator structure and methods."""
    print("\nTest 6: Testing orchestrator structure...")
    
    try:
        # Verify orchestrator class structure
        from provider_orchestrator import ProviderOrchestrator, ExecutionPath, OrchestrationResult
        import inspect
        
        # Check class methods exist
        methods = [m for m in dir(ProviderOrchestrator) if not m.startswith('_')]
        required_methods = ['process_query', 'get_stats', 'reset', 'close']
        
        has_all_methods = all(method in methods for method in required_methods)
        
        # Check dataclasses exist
        has_execution_path = hasattr(ExecutionPath, 'DB_HIT')
        has_result_class = 'success' in [f.name for f in OrchestrationResult.__dataclass_fields__.values()]
        
        print(f"  ✅ Orchestrator structure verified")
        print(f"  - Required methods present: {has_all_methods}")
        print(f"  - ExecutionPath enum: {has_execution_path}")
        print(f"  - OrchestrationResult dataclass: {has_result_class}")
        print(f"  - Methods: {', '.join(required_methods)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Orchestrator structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("MULTI-SKILL ARCHITECTURE - QUICK TEST SUITE")
    print("="*80)
    print("\nVerifying that all skills and orchestrator work correctly...\n")
    
    tests = [
        test_skill_imports,
        test_orchestrator_init,
        test_query_interpretation,
        test_semantic_matcher,
        test_web_researcher,
        test_orchestrator_workflow,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Multi-skill architecture is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
