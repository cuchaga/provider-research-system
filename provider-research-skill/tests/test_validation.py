#!/usr/bin/env python3
"""
Validation Tests for Provider Research v2.0.0
Test all imports and basic functionality
"""

def test_core_module_imports():
    """Test 1: Core module imports"""
    from provider_research import (
        ProviderOrchestrator,
        ProviderQueryInterpreter,
        ProviderDatabaseManager,
        ProviderSemanticMatcher,
        ProviderWebResearcher
    )
    print("✅ Test 1: Core module imports - PASSED")


def test_legacy_module_imports():
    """Test 2: Legacy module imports"""
    from provider_research import (
        ProviderResearchLLM,
        ProviderDatabasePostgres,
        ProviderDatabaseSQLite
    )
    print("✅ Test 2: Legacy module imports - PASSED")


def test_data_classes_and_enums():
    """Test 3: Data classes and enums"""
    from provider_research import (
        OrchestrationResult,
        ExecutionPath,
        DatabaseSearchResult,
        SemanticMatch,
        ResearchResult,
        DeduplicationResult,
        ParsedQuery,
        Intent,
        MatchResult,
        ExtractionResult
    )
    print("✅ Test 3: Data classes and enums - PASSED")


def test_module_functions():
    """Test 4: Module functions"""
    from provider_research import search_providers, display_results
    print("✅ Test 4: Module functions - PASSED")


def test_submodule_structure():
    """Test 5: Submodule structure"""
    import provider_research.core
    import provider_research.database
    import provider_research.search
    print("✅ Test 5: Submodule structure - PASSED")


def test_intent_enum():
    """Test 6: Intent enum values"""
    from provider_research import Intent
    intents = [Intent.SEARCH, Intent.ADD, Intent.COMPARE, Intent.LIST]
    total = len([i for i in Intent])
    print(f"✅ Test 6: Intent enum ({total} values) - PASSED")


def test_execution_path_enum():
    """Test 7: ExecutionPath enum values"""
    from provider_research import ExecutionPath
    paths = [ExecutionPath.DB_HIT, ExecutionPath.SEMANTIC, ExecutionPath.WEB_RESEARCH]
    total = len([p for p in ExecutionPath])
    print(f"✅ Test 7: ExecutionPath enum ({total} values) - PASSED")


def test_class_instantiation():
    """Test 8: Basic class instantiation"""
    from provider_research import (
        ProviderQueryInterpreter,
        ProviderSemanticMatcher,
        ProviderWebResearcher,
        ProviderDatabaseSQLite
    )
    
    # These should instantiate without errors
    interpreter = ProviderQueryInterpreter(llm_client=None)
    matcher = ProviderSemanticMatcher(llm_client=None)
    researcher = ProviderWebResearcher(llm_client=None)
    
    print("✅ Test 8: Basic class instantiation - PASSED")


def test_package_metadata():
    """Test 9: Package metadata"""
    import provider_research
    assert hasattr(provider_research, '__version__')
    assert provider_research.__version__ == "2.0.0"
    print(f"✅ Test 9: Package metadata (v{provider_research.__version__}) - PASSED")


def main():
    print("=" * 80)
    print("VALIDATION TESTS - Provider Research v2.0.0")
    print("=" * 80)
    print()
    
    tests = [
        test_core_module_imports,
        test_legacy_module_imports,
        test_data_classes_and_enums,
        test_module_functions,
        test_submodule_structure,
        test_intent_enum,
        test_execution_path_enum,
        test_class_instantiation,
        test_package_metadata,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - FAILED: {e}")
            failed += 1
    
    print()
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
