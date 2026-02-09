"""
Web Scraping Examples - Provider Web Researcher
================================================

Demonstrates real web scraping, HTML parsing, and historical data extraction.
"""

from provider_web_researcher import ProviderWebResearcher
from provider_database_manager import ProviderDatabaseManager

# Example LLM client (mock for demonstration)
class MockLLMClient:
    """Mock LLM client for testing."""
    def __init__(self):
        pass

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}


def example_1_basic_web_research():
    """Example: Basic web research with real HTTP fetching"""
    print("\n" + "="*60)
    print("Example 1: Real Web Scraping")
    print("="*60)
    
    # Initialize with real scraping enabled
    researcher = ProviderWebResearcher(
        use_real_scraping=True,  # Use actual HTTP requests
        llm_client=None  # Will use simulation for LLM
    )
    
    # Research a provider
    result = researcher.research(
        provider_name="Home Instead Senior Care",
        location="Boston, MA"
    )
    
    print(f"\nProvider: {result.provider_name}")
    print(f"Locations found: {len(result.locations)}")
    print(f"Historical records: {len(result.historical_data.get('previous_names', []))}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Sources: {len(result.source_urls)}")
    
    if result.warnings:
        print(f"Warnings: {result.warnings}")
    
    researcher.close()


def example_2_simulation_mode():
    """Example: Research with simulation mode (no real HTTP)"""
    print("\n" + "="*60)
    print("Example 2: Simulation Mode (No Real HTTP)")
    print("="*60)
    
    # Initialize with simulation
    researcher = ProviderWebResearcher(
        use_real_scraping=False  # Use simulated content
    )
    
    result = researcher.research(
        provider_name="Comfort Keepers",
        location="Detroit, MI"
    )
    
    print(f"\nProvider: {result.provider_name}")
    print(f"Locations found: {len(result.locations)}")
    
    for loc in result.locations:
        print(f"\n  Location:")
        print(f"    Name: {loc.get('name')}")
        print(f"    Address: {loc.get('address')}, {loc.get('city')}, {loc.get('state')}")
        print(f"    Phone: {loc.get('phone')}")


def example_3_historical_data_extraction():
    """Example: Extract historical information from web pages"""
    print("\n" + "="*60)
    print("Example 3: Historical Data Extraction")
    print("="*60)
    
    researcher = ProviderWebResearcher(use_real_scraping=False)
    
    result = researcher.research(
        provider_name="Sample Provider",
        location="Boston, MA"
    )
    
    historical = result.historical_data
    
    print(f"\nHistorical Data Found:")
    
    if historical.get('previous_names'):
        print(f"\nPrevious Names ({len(historical['previous_names'])}):")
        for name_record in historical['previous_names']:
            print(f"  • {name_record['name']}")
            print(f"    Date: {name_record.get('date', 'Unknown')}")
            print(f"    Type: {name_record.get('type')}")
            if name_record.get('notes'):
                print(f"    Notes: {name_record['notes']}")
    
    if historical.get('previous_owners'):
        print(f"\nPrevious Owners ({len(historical['previous_owners'])}):")
        for owner_record in historical['previous_owners']:
            print(f"  • {owner_record['owner']}")
            print(f"    Type: {owner_record.get('change_type')}")
            if owner_record.get('end_date'):
                print(f"    Until: {owner_record['end_date']}")
            if owner_record.get('notes'):
                print(f"    Notes: {owner_record['notes']}")
    
    if historical.get('company_history'):
        print(f"\nCompany History:")
        print(f"  {historical['company_history']}")


def example_4_save_with_history():
    """Example: Research provider and save with historical data"""
    print("\n" + "="*60)
    print("Example 4: Research and Save with History")
    print("="*60)
    
    # Initialize researcher and database
    researcher = ProviderWebResearcher(use_real_scraping=False)
    db = ProviderDatabaseManager(db_config)
    
    # Research provider
    result = researcher.research(
        provider_name="Example Home Care",
        location="Chicago, IL"
    )
    
    if result.locations:
        # Add first location to database
        location = result.locations[0]
        
        provider_id = db.add_provider(
            legal_name=location.get('name', 'Unknown'),
            city=location.get('city'),
            state=location.get('state'),
            phone=location.get('phone'),
            address=location.get('address'),
            npi=location.get('npi'),
            website=location.get('website')
        )
        
        print(f"\n✓ Provider added: {provider_id}")
        
        # Save historical data
        for prev_name in result.historical_data.get('previous_names', []):
            db.record_history(
                provider_id=provider_id,
                change_type='name_change',
                field_name='legal_name',
                old_value=prev_name['name'],
                new_value=location.get('name'),
                effective_date=prev_name.get('date'),
                source='web_research',
                notes=prev_name.get('notes')
            )
            print(f"  ✓ Recorded previous name: {prev_name['name']}")
        
        for prev_owner in result.historical_data.get('previous_owners', []):
            db.record_history(
                provider_id=provider_id,
                change_type=prev_owner.get('change_type', 'ownership_change'),
                field_name='parent_organization',
                old_value=prev_owner['owner'],
                new_value='Current Organization',
                effective_date=prev_owner.get('end_date'),
                source='web_research',
                notes=prev_owner.get('notes')
            )
            print(f"  ✓ Recorded previous owner: {prev_owner['owner']}")


def example_5_custom_search():
    """Example: Provide custom search function"""
    print("\n" + "="*60)
    print("Example 5: Custom Web Search Function")
    print("="*60)
    
    def custom_search(query: str) -> list:
        """Custom search function (would call real search API)"""
        print(f"  Searching for: {query}")
        return [
            f"https://example.com/provider1",
            f"https://example.com/provider2/about",
            f"https://example.com/provider3/history"
        ]
    
    researcher = ProviderWebResearcher(
        web_search_fn=custom_search,
        use_real_scraping=False
    )
    
    result = researcher.research(
        provider_name="Custom Provider",
        location="Seattle, WA"
    )
    
    print(f"\nSearch executed")
    print(f"URLs found: {len(result.source_urls)}")
    for url in result.source_urls:
        print(f"  - {url}")


def example_6_error_handling():
    """Example: Error handling for failed requests"""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    researcher = ProviderWebResearcher(use_real_scraping=True)
    
    # Try to fetch an invalid URL (will handle gracefully)
    content = researcher._fetch_content("https://invalid-url-that-doesnt-exist-12345.com")
    
    if content:
        print("Content fetched successfully")
    else:
        print("✓ Failed gracefully - No content returned (expected)")
    
    researcher.close()


def example_7_html_cleaning():
    """Example: HTML parsing and text extraction"""
    print("\n" + "="*60)
    print("Example 7: HTML Cleaning Demo")
    print("="*60)
    
    # Raw HTML with noise
    html_content = """
    <html>
    <head><title>Provider Page</title></head>
    <body>
        <script>console.log('tracking');</script>
        <nav>Menu items here</nav>
        <h1>About Our Home Care Services</h1>
        <p>We provide excellent care since 2010.</p>
        <p>Contact us at (555) 123-4567</p>
        <footer>Copyright 2024</footer>
    </body>
    </html>
    """
    
    # The BeautifulSoup cleaning removes script, nav, footer
    # In real implementation, this happens in _fetch_content_real()
    
    print("Raw HTML includes:")
    print("  - Scripts (removed)")
    print("  - Navigation (removed)")
    print("  - Footer (removed)")
    print("  - Main content (kept)")
    print("\nCleaned text would contain only:")
    print("  'About Our Home Care Services'")
    print("  'We provide excellent care since 2010.'")
    print("  'Contact us at (555) 123-4567'")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("WEB SCRAPING EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate:")
    print("  • Real HTTP requests with BeautifulSoup")
    print("  • HTML parsing and text extraction")
    print("  • Historical data extraction")
    print("  • Simulation mode for testing")
    print("  • Error handling")
    print("  • Integration with database")
    print("="*60)
    
    # Run examples (uncomment to test)
    # example_1_basic_web_research()
    example_2_simulation_mode()
    example_3_historical_data_extraction()
    # example_4_save_with_history()
    example_5_custom_search()
    # example_6_error_handling()
    example_7_html_cleaning()
