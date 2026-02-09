"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_provider():
    """Sample provider data."""
    return {
        'id': '12345678-1234-1234-1234-123456789012',
        'npi': '1234567890',
        'legal_name': 'Home Instead Senior Care',
        'address_city': 'Boston',
        'address_state': 'MA',
        'address_zip': '02101',
        'phone': '555-123-4567',
        'provider_type': 'Home Care',
        'parent_organization': 'Home Instead Inc.'
    }


@pytest.fixture
def sample_providers_list():
    """List of sample providers."""
    return [
        {
            'id': '1',
            'legal_name': 'Home Instead - Boston',
            'address_city': 'Boston',
            'address_state': 'MA',
            'npi': '1111111111'
        },
        {
            'id': '2',
            'legal_name': 'Visiting Angels - Cambridge',
            'address_city': 'Cambridge',
            'address_state': 'MA',
            'npi': '2222222222'
        },
        {
            'id': '3',
            'legal_name': 'Comfort Keepers - Somerville',
            'address_city': 'Somerville',
            'address_state': 'MA',
            'npi': '3333333333'
        }
    ]


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    class MockLLMClient:
        def generate(self, prompt, **kwargs):
            return {
                'content': '{"intent": "search", "confidence": 0.9}',
                'usage': {'tokens': 100}
            }
    
    return MockLLMClient()


@pytest.fixture
def temp_db_path(tmp_path):
    """Temporary database path."""
    return str(tmp_path / "test_providers.db")
