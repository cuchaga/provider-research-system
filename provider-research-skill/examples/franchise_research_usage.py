"""
Example: Using FranchiseResearcher Skill

This demonstrates how to use the FranchiseResearcher skill to find and import
all franchise locations in a specified area with full historical tracking.

The skill is reusable for any franchise company in any location:
- Home Instead in Massachusetts
- Visiting Angels in California
- Comfort Keepers in Michigan
- Any franchise, any location

Features demonstrated:
1. Multi-source data collection (websites, NPI Registry, databases)
2. Historical data extraction (ownership changes, name changes, transactions)
3. Automated validation and deduplication
4. Batch database import with history tracking
5. Export results to JSON/CSV

Author: Provider Research System
Version: 2.0.0
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FranchiseResearcher skill
from provider_research import FranchiseResearcher, DataSource

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_research():
    """
    Example 1: Basic franchise research without database
    
    Perfect for initial research or when you don't have a database set up yet.
    """
    print("\n" + "="*80)
    print("Example 1: Basic Franchise Research (Simulation Mode)")
    print("="*80 + "\n")
    
    # Initialize in simulation mode (no LLM API calls needed)
    researcher = FranchiseResearcher(
        db_config=None,  # No database needed for research only
        llm_client=None,  # No LLM client needed in simulation mode
        simulation_mode=True
    )
    
    # Research all Home Instead locations in Massachusetts
    results = researcher.research_franchise_locations(
        franchise_name="Home Instead",
        location="Massachusetts",
        include_history=True  # Include historical data search
    )
    
    # Display summary
    print(f"Franchise: {results['franchise_name']}")
    print(f"Location: {results['location']}")
    print(f"Research Date: {results['research_date']}\n")
    
    print("Summary:")
    print(f"  Locations Found: {results['summary']['locations_found']}")
    print(f"  Unique Locations: {results['summary']['unique_locations']}")
    print(f"  Duplicates Removed: {results['summary']['duplicates_removed']}")
    print(f"  Historical Events: {results['historical_events_found']}")
    print(f"  High Confidence: {results['summary']['high_confidence']}")
    print(f"  Medium Confidence: {results['summary']['medium_confidence']}")
    print(f"  Low Confidence: {results['summary']['low_confidence']}\n")
    
    # Display locations
    print("Locations Found:")
    for i, location in enumerate(results['locations'], 1):
        print(f"\n{i}. {location.legal_name}")
        print(f"   Address: {location.address_line1}, {location.city}, {location.state} {location.zip_code}")
        print(f"   Phone: {location.phone}")
        print(f"   NPI: {location.npi}")
        print(f"   Confidence: {location.confidence_score:.2f}")
        
        if location.ownership_history:
            print(f"   Historical Events: {len(location.ownership_history)}")
            for event in location.ownership_history[:2]:  # Show first 2
                print(f"     - {event.event_date}: {event.description}")
    
    return results


def example_2_export_results():
    """
    Example 2: Research and export results to JSON
    
    Useful for review, sharing, or importing later.
    """
    print("\n" + "="*80)
    print("Example 2: Research and Export to JSON")
    print("="*80 + "\n")
    
    researcher = FranchiseResearcher(simulation_mode=True)
    
    # Research Visiting Angels in California
    results = researcher.research_franchise_locations(
        franchise_name="Visiting Angels",
        location="California",
        include_history=True
    )
    
    # Export to JSON
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "visiting_angels_ca.json"
    researcher.export_results(results, str(output_file), format='json')
    
    print(f"✓ Exported {len(results['locations'])} locations to {output_file}")
    
    # Show file preview
    with open(output_file, 'r') as f:
        data = json.load(f)
        print(f"\nFile preview:")
        print(f"  Franchise: {data['franchise_name']}")
        print(f"  Location: {data['location']}")
        print(f"  Total Locations: {len(data['locations'])}")
    
    return results


def example_3_with_database():
    """
    Example 3: Research and import to database
    
    Complete workflow: research → validate → deduplicate → import with history
    """
    print("\n" + "="*80)
    print("Example 3: Research and Import to Database")
    print("="*80 + "\n")
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'providers',
        'user': 'provider_admin',
        'password': 'provider123'
    }
    
    # Initialize with database
    researcher = FranchiseResearcher(
        db_config=db_config,
        simulation_mode=True  # Still in simulation for this example
    )
    
    # Research Comfort Keepers in Michigan
    results = researcher.research_franchise_locations(
        franchise_name="Comfort Keepers",
        location="Michigan",
        include_history=True
    )
    
    print(f"Found {len(results['locations'])} locations\n")
    
    # Import to database (dry run first)
    print("Performing dry run import...")
    dry_run_stats = researcher.import_results(
        results,
        dry_run=True,
        skip_duplicates=True
    )
    
    print("\nDry Run Results:")
    print(f"  Would Add: {dry_run_stats['providers_added']}")
    print(f"  Would Update: {dry_run_stats['providers_updated']}")
    print(f"  Would Skip: {dry_run_stats['providers_skipped']}")
    print(f"  Historical Events: {dry_run_stats['historical_events_added']}")
    if dry_run_stats['errors']:
        print(f"  Errors: {len(dry_run_stats['errors'])}")
    
    # Uncomment to actually import
    # print("\nPerforming actual import...")
    # import_stats = researcher.import_results(
    #     results,
    #     dry_run=False,
    #     skip_duplicates=True
    # )
    # print(f"✓ Imported {import_stats['providers_added']} locations")
    
    return results


def example_4_custom_sources():
    """
    Example 4: Research with specific data sources
    
    Control which sources are searched for maximum efficiency or coverage.
    """
    print("\n" + "="*80)
    print("Example 4: Research with Custom Data Sources")
    print("="*80 + "\n")
    
    researcher = FranchiseResearcher(simulation_mode=True)
    
    # Only search specific sources
    results = researcher.research_franchise_locations(
        franchise_name="Right at Home",
        location="Texas",
        include_history=True,
        sources=[
            DataSource.FRANCHISE_LOCATOR,
            DataSource.NPI_REGISTRY,
            # DataSource.NEWS_ARCHIVE,  # Skip news for faster research
            # DataSource.SEC_FILINGS,   # Skip SEC for private companies
        ]
    )
    
    print(f"Sources used: {[s.value for s in [DataSource.FRANCHISE_LOCATOR, DataSource.NPI_REGISTRY]]}")
    print(f"Locations found: {len(results['locations'])}\n")
    
    return results


def example_5_historical_deep_dive():
    """
    Example 5: Deep historical research with specific date range
    
    Focus on historical data for merger/acquisition analysis or ownership tracking.
    """
    print("\n" + "="*80)
    print("Example 5: Deep Historical Research")
    print("="*80 + "\n")
    
    researcher = FranchiseResearcher(simulation_mode=True)
    
    # Research with specific historical date range
    results = researcher.research_franchise_locations(
        franchise_name="Home Instead",
        location="Massachusetts",
        include_history=True,
        date_range=("2015-01-01", "2026-02-09")  # Last 11 years
    )
    
    print(f"Historical events found: {results['historical_events_found']}\n")
    
    # Analyze historical events
    event_types = {}
    for location in results['locations']:
        if location.ownership_history:
            for event in location.ownership_history:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
    
    print("Event type breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    # Show locations with most historical events
    locations_with_history = [
        (loc.legal_name, len(loc.ownership_history or []))
        for loc in results['locations']
        if loc.ownership_history
    ]
    
    if locations_with_history:
        locations_with_history.sort(key=lambda x: x[1], reverse=True)
        print("\nLocations with most historical events:")
        for name, count in locations_with_history[:5]:
            print(f"  {name}: {count} events")
    
    return results


def example_6_multi_franchise_batch():
    """
    Example 6: Research multiple franchises in batch
    
    Useful for comprehensive market research or competitor analysis.
    """
    print("\n" + "="*80)
    print("Example 6: Multi-Franchise Batch Research")
    print("="*80 + "\n")
    
    researcher = FranchiseResearcher(simulation_mode=True)
    
    # List of franchises to research
    franchises = [
        ("Home Instead", "Massachusetts"),
        ("Visiting Angels", "Massachusetts"),
        ("Comfort Keepers", "Massachusetts"),
        ("Right at Home", "Massachusetts"),
    ]
    
    all_results = []
    
    for franchise_name, location in franchises:
        print(f"\nResearching {franchise_name} in {location}...")
        
        results = researcher.research_franchise_locations(
            franchise_name=franchise_name,
            location=location,
            include_history=False  # Skip history for faster batch processing
        )
        
        all_results.append(results)
        print(f"  Found {len(results['locations'])} locations")
    
    # Summary
    print("\n" + "-"*80)
    print("Batch Research Summary:")
    total_locations = sum(len(r['locations']) for r in all_results)
    print(f"  Total Franchises Researched: {len(franchises)}")
    print(f"  Total Locations Found: {total_locations}")
    
    for results in all_results:
        print(f"  {results['franchise_name']}: {len(results['locations'])} locations")
    
    return all_results


def example_7_production_workflow():
    """
    Example 7: Complete production workflow
    
    End-to-end process: research → validate → export → review → import
    """
    print("\n" + "="*80)
    print("Example 7: Complete Production Workflow")
    print("="*80 + "\n")
    
    # Step 1: Research
    print("Step 1: Researching franchise locations...")
    researcher = FranchiseResearcher(simulation_mode=True)
    
    results = researcher.research_franchise_locations(
        franchise_name="Home Instead",
        location="Massachusetts",
        include_history=True
    )
    print(f"✓ Found {len(results['locations'])} locations\n")
    
    # Step 2: Review confidence scores
    print("Step 2: Reviewing confidence scores...")
    low_confidence = [
        loc for loc in results['locations'] 
        if loc.confidence_score < 0.7
    ]
    
    if low_confidence:
        print(f"⚠ {len(low_confidence)} locations with low confidence:")
        for loc in low_confidence:
            print(f"  - {loc.legal_name} (score: {loc.confidence_score:.2f})")
            print(f"    Missing: ", end="")
            missing = []
            if not loc.npi:
                missing.append("NPI")
            if not loc.phone:
                missing.append("phone")
            if not loc.address_line1:
                missing.append("address")
            print(", ".join(missing))
    else:
        print("✓ All locations have good confidence scores\n")
    
    # Step 3: Export for review
    print("\nStep 3: Exporting for manual review...")
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    review_file = output_dir / "home_instead_ma_review.json"
    researcher.export_results(results, str(review_file), format='json')
    print(f"✓ Exported to {review_file}\n")
    
    # Step 4: Dry run import
    print("Step 4: Simulating database import...")
    import_stats = researcher.import_results(results, dry_run=True)
    print(f"✓ Would import {import_stats['providers_added']} providers")
    print(f"✓ Would add {import_stats['historical_events_added']} historical events\n")
    
    # Step 5: Show what to do next
    print("Step 5: Next steps:")
    print("  1. Review exported JSON file manually")
    print("  2. Verify low-confidence locations online")
    print("  3. Update JSON with corrections if needed")
    print("  4. Run actual import with dry_run=False")
    print("  5. Verify database entries")
    
    return results


if __name__ == "__main__":
    """
    Run all examples to demonstrate FranchiseResearcher capabilities.
    
    Uncomment specific examples to run individually.
    """
    
    print("\n" + "="*80)
    print(" FranchiseResearcher Skill - Usage Examples")
    print("="*80)
    
    # Run examples
    example_1_basic_research()
    example_2_export_results()
    example_3_with_database()
    example_4_custom_sources()
    example_5_historical_deep_dive()
    example_6_multi_franchise_batch()
    example_7_production_workflow()
    
    print("\n" + "="*80)
    print(" All Examples Complete!")
    print("="*80 + "\n")
    
    print("Next steps:")
    print("  - Review the code to understand each example")
    print("  - Modify parameters for your specific franchise/location")
    print("  - Set simulation_mode=False and provide llm_client for production")
    print("  - Configure database and run actual imports")
    print("\nDocumentation: See provider-research-skill/README.md")
