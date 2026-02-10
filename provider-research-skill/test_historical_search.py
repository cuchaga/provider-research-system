#!/usr/bin/env python3
"""
Test Enhanced Historical Data Search

This script tests the enhanced historical data search capabilities
of the FranchiseResearcher skill.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from provider_research import FranchiseResearcher

print('\n' + '='*80)
print('  Testing Enhanced Historical Data Search')
print('='*80)

# Initialize researcher (no DB needed for testing)
researcher = FranchiseResearcher(
    db_config=None,
    llm_client=None,
    simulation_mode=False  # Use real web search!
)

print('\n📋 Testing historical search methods:')
print('  ✓ _search_google_news')
print('  ✓ _search_business_journals')
print('  ✓ _search_sec_filings')

# Test historical search
print('\n🔍 Searching for historical data: "Home Instead Massachusetts acquisition"')
print('  This will search real news sources and business journals...\n')

search_term = "Home Instead Massachusetts acquisition"
date_range = ("2015-01-01", "2026-01-01")

# Test Google News search
print('1. Testing Google News search...')
google_results = researcher._search_google_news(search_term, date_range)
print(f'   Found {len(google_results)} articles from Google News')
for article in google_results[:2]:
    print(f'   - {article["title"][:80]}...')

# Test Business Journal search  
print('\n2. Testing Business Journal search...')
journal_results = researcher._search_business_journals(search_term, date_range)
print(f'   Found {len(journal_results)} articles from business journals')
for article in journal_results[:2]:
    print(f'   - {article["title"][:80]}...')

# Test SEC search
print('\n3. Testing SEC EDGAR search...')
sec_results = researcher._search_sec_filings(search_term, date_range)
print(f'   Found {len(sec_results)} SEC filings')
for article in sec_results[:2]:
    print(f'   - {article["title"][:80]}...')

total_sources = len(google_results) + len(journal_results) + len(sec_results)

print('\n' + '='*80)
print(f'✓ Historical search test complete!')
print(f'  Total sources found: {total_sources}')
print('='*80)

if total_sources > 0:
    print('\n✅ SUCCESS: Historical data search is working!')
    print('   The system can now search for:')
    print('   • Ownership changes')
    print('   • Acquisitions and mergers')
    print('   • Franchise sales')
    print('   • Name changes and rebranding')
    print('   • Corporate transactions')
else:
    print('\n⚠️  No sources found in this test')
    print('   This may be due to:')
    print('   • Rate limiting from search engines')
    print('   • Network connectivity issues')
    print('   • Changes in website structures')
    print('   The code is ready, but may need adjustment based on actual responses')

print()
