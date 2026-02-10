#!/usr/bin/env python3
"""
Development Script: Research and Import Home Instead Franchises in Greater Boston

This script performs real web research (not simulation) to find all Home Instead
franchises in the greater Boston area and imports them to the database.

Usage:
    python3 dev_import_home_instead_boston.py

Requirements:
    - Virtual environment activated
    - PostgreSQL running with 'providers' database
    - Database credentials configured
    - Internet connection for web research

Author: Provider Research System
Date: February 9, 2026
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provider_research import FranchiseResearcher

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}

def main():
    """Research and import Home Instead franchises in greater Boston area."""
    
    print("\n" + "="*80)
    print(" Home Instead - Greater Boston Area Research & Import")
    print("="*80 + "\n")
    
    # Initialize researcher with database connection
    print("Initializing FranchiseResearcher with database connection...")
    try:
        researcher = FranchiseResearcher(
            db_config=DB_CONFIG,
            llm_client=None,  # Will use default Anthropic client if API key available
            simulation_mode=False  # Real web research!
        )
        print("✓ Connected to PostgreSQL database\n")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        print("\n⚠  Database connection failed!")
        print("   Make sure PostgreSQL is running:")
        print("   brew services start postgresql@16")
        print("   # OR")
        print("   pg_ctl -D /opt/homebrew/var/postgresql@16 start\n")
        
        # Offer to run in simulation mode
        response = input("Run in simulation mode instead? (y/n): ")
        if response.lower() == 'y':
            print("\nRunning in SIMULATION MODE (demo data)...")
            researcher = FranchiseResearcher(
                db_config=None,
                llm_client=None,
                simulation_mode=True
            )
        else:
            print("Exiting...")
            return 1
    
    # Research greater Boston area
    print("Researching Home Instead franchises in Greater Boston...")
    print("  📍 Search area: Boston, MA and surrounding communities")
    print("  🔍 Sources:")
    print("     - Home Instead franchise locator")
    print("     - NPI Registry (National Provider Identifier)")
    print("     - Business directories")
    print("     - News archives for ownership history")
    print()
    
    try:
        results = researcher.research_franchise_locations(
            franchise_name="Home Instead",
            location="Greater Boston, Massachusetts",  # Will search wider area
            include_history=True  # Include ownership changes
        )
    except Exception as e:
        logger.error(f"Research failed: {e}")
        print(f"\n❌ Research failed: {e}")
        return 1
    
    # Display summary
    print("\n" + "-"*80)
    print("RESEARCH RESULTS")
    print("-"*80)
    print(f"Franchise: {results['franchise_name']}")
    print(f"Location: {results['location']}")
    print(f"Research Date: {results['research_date']}")
    print()
    print(f"Locations Found: {results['summary']['locations_found']}")
    print(f"Unique Locations: {results['summary']['unique_locations']}")
    print(f"Duplicates Removed: {results['summary']['duplicates_removed']}")
    print(f"Historical Events: {len([e for loc in results['locations'] for e in loc.ownership_history])}")
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
        print(f"   📍 {location.address_line1}")
        if location.address_line2:
            print(f"      {location.address_line2}")
        print(f"      {location.city}, {location.state} {location.zip_code}")
        print(f"   ☎  {location.phone}")
        if location.npi:
            print(f"   🏥 NPI: {location.npi}")
        print(f"   📊 Confidence: {location.confidence_score:.0%}")
        
        if location.ownership_history:
            print(f"   📜 Historical Events: {len(location.ownership_history)}")
            for event in location.ownership_history[:2]:
                print(f"      • {event.event_date}: {event.description[:60]}...")
        print()
    
    # Export results
    export_file = f"data/exports/home_instead_boston_{datetime.now().strftime('%Y%m%d')}.json"
    Path(export_file).parent.mkdir(parents=True, exist_ok=True)
    
    print("-"*80)
    print("EXPORTING RESULTS")
    print("-"*80)
    researcher.export_results(results, export_file, format='json')
    print(f"✓ Exported to: {export_file}\n")
    
    # Import to database
    if DB_CONFIG and not researcher.simulation_mode:
        print("-"*80)
        print("DATABASE IMPORT")
        print("-"*80)
        
        # First, dry run to preview
        print("\n1. DRY RUN (preview what will be imported)...\n")
        dry_stats = researcher.import_results(results, dry_run=True)
        
        print(f"\nWould import:")
        print(f"  • {dry_stats['providers_imported']} provider records")
        print(f"  • {dry_stats['historical_events_imported']} historical events")
        print(f"  • {dry_stats['ownership_changes_tracked']} ownership changes")
        
        # Confirm import
        print("\n2. ACTUAL IMPORT")
        response = input("\nProceed with import to database? (y/n): ")
        
        if response.lower() == 'y':
            print("\nImporting to database...")
            
            try:
                actual_stats = researcher.import_results(results, dry_run=False)
                
                print("\n✓ Import successful!")
                print(f"  • Providers imported: {actual_stats['providers_imported']}")
                print(f"  • Providers updated: {actual_stats['providers_updated']}")
                print(f"  • Duplicates skipped: {actual_stats['duplicates_skipped']}")
                print(f"  • Historical events: {actual_stats['historical_events_imported']}")
                print(f"  • Ownership changes tracked: {actual_stats['ownership_changes_tracked']}")
                
            except Exception as e:
                logger.error(f"Import failed: {e}")
                print(f"\n❌ Import failed: {e}")
                return 1
        else:
            print("\n⏭  Import skipped")
    else:
        print("\n" + "-"*80)
        print("DATABASE IMPORT SKIPPED (Simulation Mode)")
        print("-"*80)
        print("To import to database:")
        print("1. Start PostgreSQL")
        print("2. Run this script again in non-simulation mode")
    
    print("\n" + "="*80)
    print("✓ COMPLETE!")
    print("="*80 + "\n")
    
    print("Next steps:")
    print("1. Review exported data:", export_file)
    print("2. Query database to verify:")
    print("   python3 -c \"from provider_research.database import ProviderDatabaseManager;")
    print("   db = ProviderDatabaseManager(%s);" % DB_CONFIG)
    print("   print(db.search(query='Home Instead', state='MA'))\"")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
