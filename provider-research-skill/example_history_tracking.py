"""
Provider History Tracking Examples
===================================

Demonstrates how to track and query historical changes to provider data,
including previous business names, ownership changes, mergers, and acquisitions.
"""

from datetime import datetime, timedelta
from provider_database_manager import ProviderDatabaseManager
from provider_database_postgres import ProviderDatabasePostgres

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}


def example_1_name_change():
    """Example: Record a business name change"""
    print("\n" + "="*60)
    print("Example 1: Recording a Legal Name Change")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    # Scenario: Provider changed their legal name
    provider_id = "some-provider-id"  # Replace with actual provider ID
    
    # Update name and automatically record history
    db.update_provider_with_history(
        provider_id=provider_id,
        field_name='legal_name',
        new_value='Comfort Keepers Home Care LLC',
        change_type='name_change',
        effective_date=datetime(2024, 1, 15),
        source='state_registry',
        notes='Legal name change filed with state on 1/15/2024'
    )
    
    print("✓ Name change recorded to history")


def example_2_ownership_change():
    """Example: Record ownership/parent organization change"""
    print("\n" + "="*60)
    print("Example 2: Recording Ownership Change (Acquisition)")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Scenario: Provider was acquired by a larger organization
    db.update_provider_with_history(
        provider_id=provider_id,
        field_name='parent_organization',
        new_value='BrightSpring Health Services',
        change_type='acquisition',
        effective_date=datetime(2023, 6, 1),
        source='press_release',
        notes='Acquired by BrightSpring for $15M, announced June 2023'
    )
    
    print("✓ Acquisition recorded to history")


def example_3_dba_change():
    """Example: Record DBA (doing business as) name change"""
    print("\n" + "="*60)
    print("Example 3: Recording DBA Name Change")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Manually record history for DBA change
    db.record_history(
        provider_id=provider_id,
        change_type='dba_change',
        field_name='dba_names',
        old_value='CK Home Services',
        new_value='Comfort Keepers Senior Care',
        effective_date=datetime(2023, 3, 1),
        source='web_research',
        notes='Rebranded marketing name to align with parent company',
        recorded_by='research_assistant'
    )
    
    print("✓ DBA change recorded to history")


def example_4_merger():
    """Example: Record a merger between two organizations"""
    print("\n" + "="*60)
    print("Example 4: Recording Merger")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    db.record_history(
        provider_id=provider_id,
        change_type='merger',
        field_name='legal_name',
        old_value='All Care Home Services Inc',
        new_value='Unified Senior Care LLC',
        effective_date=datetime(2022, 11, 1),
        source='sec_filing',
        notes='Merger of All Care and Best Care completed Nov 2022',
        recorded_by='compliance_officer'
    )
    
    print("✓ Merger recorded to history")


def example_5_query_history():
    """Example: Query provider's complete history"""
    print("\n" + "="*60)
    print("Example 5: Querying Provider History")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Get all history
    history = db.get_provider_history(provider_id)
    
    print(f"\nFound {len(history)} historical changes:")
    for record in history:
        print(f"  • {record['effective_date']}: {record['change_type']}")
        print(f"    {record['old_value']} → {record['new_value']}")
        print(f"    Source: {record['source']}")
        if record['notes']:
            print(f"    Notes: {record['notes']}")
        print()


def example_6_query_previous_names():
    """Example: Get all previous business names"""
    print("\n" + "="*60)
    print("Example 6: Getting Previous Business Names")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Get all previous names (legal names and DBAs)
    previous_names = db.get_previous_names(provider_id)
    
    print(f"\nPrevious names ({len(previous_names)}):")
    for record in previous_names:
        print(f"  • {record['name']}")
        print(f"    Type: {record['type']}")
        print(f"    Used until: {record['effective_date']}")
        print(f"    Source: {record['source']}")
        print()


def example_7_query_previous_owners():
    """Example: Get ownership history"""
    print("\n" + "="*60)
    print("Example 7: Getting Previous Owners")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Get all previous owners
    previous_owners = db.get_previous_owners(provider_id)
    
    print(f"\nPrevious owners ({len(previous_owners)}):")
    for record in previous_owners:
        print(f"  • {record['owner']}")
        print(f"    Until: {record['effective_date']}")
        print(f"    Source: {record['source']}")
        if record['notes']:
            print(f"    Notes: {record['notes']}")
        print()


def example_8_complete_timeline():
    """Example: Create complete provider timeline"""
    print("\n" + "="*60)
    print("Example 8: Complete Provider Timeline")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    provider_id = "some-provider-id"
    
    # Get current provider info
    cur = db.conn.cursor(cursor_factory=globals()['RealDictCursor'])
    cur.execute("SELECT legal_name, parent_organization FROM providers WHERE id = %s", (provider_id,))
    current = cur.fetchone()
    
    # Get all history
    history = db.get_provider_history(provider_id)
    
    print(f"\nCurrent: {current['legal_name']}")
    if current['parent_organization']:
        print(f"Owner: {current['parent_organization']}")
    
    print("\n📅 Timeline:")
    for record in sorted(history, key=lambda x: x['effective_date']):
        date = record['effective_date'].strftime('%Y-%m-%d')
        change = record['change_type'].replace('_', ' ').title()
        print(f"  {date} - {change}")
        print(f"           {record['old_value']} → {record['new_value']}")


def example_9_batch_import_history():
    """Example: Import historical data from research"""
    print("\n" + "="*60)
    print("Example 9: Batch Importing Historical Data")
    print("="*60)
    
    db = ProviderDatabaseManager(db_config)
    
    # Scenario: You found historical data through research
    historical_changes = [
        {
            'provider_id': 'some-provider-id',
            'change_type': 'name_change',
            'field_name': 'legal_name',
            'old_value': 'Smith Family Home Care',
            'new_value': 'Smith Senior Services Inc',
            'effective_date': datetime(2019, 4, 1),
            'source': 'web_archive',
            'notes': 'Incorporated as LLC, found in web archive'
        },
        {
            'provider_id': 'some-provider-id',
            'change_type': 'ownership_change',
            'field_name': 'parent_organization',
            'old_value': 'Independent',
            'new_value': 'Regional Care Partners LLC',
            'effective_date': datetime(2021, 8, 15),
            'source': 'linkedin',
            'notes': 'Joined regional network per LinkedIn announcement'
        },
        {
            'provider_id': 'some-provider-id',
            'change_type': 'acquisition',
            'field_name': 'parent_organization',
            'old_value': 'Regional Care Partners LLC',
            'new_value': 'BrightSpring Health Services',
            'effective_date': datetime(2023, 6, 1),
            'source': 'press_release',
            'notes': 'BrightSpring acquired Regional Care Partners'
        }
    ]
    
    for change in historical_changes:
        db.record_history(**change)
        print(f"✓ Recorded: {change['change_type']} on {change['effective_date'].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PROVIDER HISTORY TRACKING EXAMPLES")
    print("="*60)
    print("\nThese examples show how to:")
    print("  • Record name changes, ownership changes, mergers")
    print("  • Query historical data")
    print("  • Build complete provider timelines")
    print("  • Import historical data from research")
    print("\nNote: Replace 'some-provider-id' with actual provider IDs")
    print("      from your database to run these examples.")
    print("="*60)
    
    # Uncomment to run specific examples:
    # example_1_name_change()
    # example_2_ownership_change()
    # example_3_dba_change()
    # example_4_merger()
    # example_5_query_history()
    # example_6_query_previous_names()
    # example_7_query_previous_owners()
    # example_8_complete_timeline()
    # example_9_batch_import_history()
