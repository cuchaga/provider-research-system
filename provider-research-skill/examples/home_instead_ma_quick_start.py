#!/usr/bin/env python3
"""
Quick Start: Find All Home Instead Franchises in Massachusetts

This is the simplest way to use the FranchiseResearcher skill.
Run this script to research all Home Instead locations in MA with full historical tracking.

Usage:
    python examples/home_instead_ma_quick_start.py

What it does:
1. Researches all Home Instead franchises in Massachusetts
2. Searches for historical data (previous owners, name changes, transactions)
3. Validates and deduplicates results
4. Exports to JSON for review
5. Shows what would be imported to database (dry run)

Requirements:
- No database needed for research
- No API keys needed (runs in simulation mode)
- Results exported to: data/exports/home_instead_ma.json

Author: Provider Research System
Version: 2.0.0
Date: February 9, 2026
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from provider_research import FranchiseResearcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def main():
    """Find all Home Instead franchises in Massachusetts with historical tracking."""
    
    print("\n" + "="*80)
    print(" Home Instead Massachusetts - Franchise Research")
    print("="*80 + "\n")
    
    # Initialize researcher in simulation mode (no API keys needed)
    print("Initializing FranchiseResearcher...")
    researcher = FranchiseResearcher(
        db_config=None,       # No database needed for research
        llm_client=None,      # No LLM client needed in simulation
        simulation_mode=True  # Simulates LLM calls for testing
    )
    print("✓ Ready\n")
    
    # Research all Home Instead locations in Massachusetts
    print("Researching Home Instead franchises in Massachusetts...")
    print("  - Searching franchise locator websites")
    print("  - Querying NPI Registry")
    print("  - Checking business directories")
    print("  - Searching newspaper archives for historical data")
    print("  - Searching business journals for ownership changes")
    print()
    
    results = researcher.research_franchise_locations(
        franchise_name="Home Instead",
        location="Massachusetts",
        include_history=True  # Include previous owners, name changes, transactions
    )
    
    # Display summary
    print("\n" + "-"*80)
    print("RESEARCH SUMMARY")
    print("-"*80)
    print(f"Franchise: {results['franchise_name']}")
    print(f"Location: {results['location']}")
    print(f"Research Date: {results['research_date']}")
    print()
    print(f"Locations Found: {results['summary']['locations_found']}")
    print(f"Unique Locations: {results['summary']['unique_locations']}")
    print(f"Duplicates Removed: {results['summary']['duplicates_removed']}")
    print(f"Historical Events Found: {results['historical_events_found']}")
    print()
    print("Confidence Distribution:")
    print(f"  High (≥80%): {results['summary']['high_confidence']}")
    print(f"  Medium (50-79%): {results['summary']['medium_confidence']}")
    print(f"  Low (<50%): {results['summary']['low_confidence']}")
    
    # Display locations
    print("\n" + "-"*80)
    print("LOCATIONS FOUND")
    print("-"*80 + "\n")
    
    for i, location in enumerate(results['locations'], 1):
        print(f"{i}. {location.legal_name}")
        print(f"   📍 {location.address_line1}, {location.city}, {location.state} {location.zip_code}")
        print(f"   ☎  {location.phone}")
        
        if location.npi:
            print(f"   🏥 NPI: {location.npi}")
        
        print(f"   📊 Confidence: {location.confidence_score:.0%}")
        
        # Show historical data if available
        if location.previous_owners:
            print(f"   📜 Previous Owners: {len(location.previous_owners)}")
            for owner in location.previous_owners[:2]:  # Show first 2
                print(f"      • {owner['owner_name']} (until {owner['owned_until']})")
        
        if location.ownership_history:
            print(f"   📰 Historical Events: {len(location.ownership_history)}")
            for event in location.ownership_history[:2]:  # Show first 2
                print(f"      • {event.event_date}: {event.description}")
        
        print()
    
    # Export results
    print("-"*80)
    print("EXPORT")
    print("-"*80 + "\n")
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "home_instead_ma.json"
    researcher.export_results(results, str(output_file), format='json')
    
    print(f"✓ Results exported to: {output_file}")
    print(f"  {len(results['locations'])} locations")
    print(f"  {results['historical_events_found']} historical events")
    print()
    
    # Show what would be imported to database
    print("-"*80)
    print("DATABASE IMPORT PREVIEW (DRY RUN)")
    print("-"*80 + "\n")
    
    print("What would happen if you imported to database:")
    print()
    
    # Note: This requires database config
    print("⚠  Database not configured (simulation mode)")
    print("   To actually import, initialize with database config:")
    print()
    print("   db_config = {")
    print("       'host': 'localhost',")
    print("       'database': 'providers',")
    print("       'user': 'provider_admin',")
    print("       'password': 'provider123'")
    print("   }")
    print()
    print("   researcher = FranchiseResearcher(db_config=db_config)")
    print("   stats = researcher.import_results(results, dry_run=False)")
    print()
    
    print(f"Would import:")
    print(f"  • {len(results['locations'])} provider records")
    print(f"  • {results['historical_events_found']} historical events")
    print(f"  • Previous owners tracked: {sum(len(loc.previous_owners or []) for loc in results['locations'])}")
    print(f"  • Previous names tracked: {sum(len(loc.previous_names or []) for loc in results['locations'])}")
    
    # Next steps
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80 + "\n")
    
    print("1. Review the exported JSON file:")
    print(f"   cat {output_file}")
    print()
    print("2. Verify data quality:")
    print("   - Check addresses are correct")
    print("   - Verify phone numbers")
    print("   - Validate NPI numbers online")
    print()
    print("3. Review historical events:")
    print("   - Cross-reference ownership changes with news sources")
    print("   - Verify transaction dates and details")
    print()
    print("4. Set up database and import:")
    print("   - Configure PostgreSQL connection")
    print("   - Run dry_run=True first to preview")
    print("   - Then import with dry_run=False")
    print()
    print("5. Use the same process for other franchises:")
    print("   researcher.research_franchise_locations('Visiting Angels', 'Massachusetts')")
    print()
    
    print("="*80)
    print("✓ Research Complete!")
    print("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    results = main()
