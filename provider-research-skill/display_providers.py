#!/usr/bin/env python3
"""
Display Providers with Flexible Field Selection
===============================================

Usage:
    # Show all providers with default fields
    python3 display_providers.py
    
    # Show specific fields only
    python3 display_providers.py business_name current_phone
    
    # Show all available fields
    python3 display_providers.py all

Default fields (if no arguments):
- business_name (legal_name)
- dbas (dba_names)
- current_address
- previous_addresses (from history)
- current_phone
- previous_phones (from history)
- current_owner (parent_organization)
- previous_owners (from history)
"""

import sys
import json
from provider_research.database.manager import ProviderDatabaseManager


def format_output(providers, fields_shown):
    """Format provider data for display."""
    if not providers:
        print("\n" + "="*80)
        print("  NO PROVIDERS FOUND IN DATABASE")
        print("="*80 + "\n")
        return
    
    print("\n" + "="*80)
    print(f"  PROVIDER DATABASE - Showing {len(providers)} provider(s)")
    print("="*80 + "\n")
    
    for i, provider in enumerate(providers, 1):
        print(f"Provider #{i}")
        print("-" * 80)
        
        # Business name
        if 'business_name' in provider:
            print(f"🏢 Business Name: {provider['business_name']}")
        
        # DBAs
        if 'dbas' in provider and provider['dbas']:
            dbas = provider['dbas']
            if isinstance(dbas, list):
                print(f"📋 DBAs: {', '.join(dbas)}")
            else:
                print(f"📋 DBAs: {dbas}")
        
        # Current address
        if 'current_address' in provider and provider['current_address']:
            print(f"📍 Current Address: {provider['current_address']}")
        
        # Previous addresses
        if 'previous_addresses' in provider and provider['previous_addresses']:
            print(f"📍 Previous Addresses:")
            for addr in provider['previous_addresses']:
                date = addr.get('effective_date', 'Unknown date')
                source = addr.get('source', 'Unknown source')
                print(f"   • {addr.get('old_value')} (Changed: {date}, Source: {source})")
        
        # Current phone
        if 'current_phone' in provider and provider['current_phone']:
            print(f"📞 Current Phone: {provider['current_phone']}")
        
        # Previous phones
        if 'previous_phones' in provider and provider['previous_phones']:
            print(f"📞 Previous Phones:")
            for phone in provider['previous_phones']:
                date = phone.get('effective_date', 'Unknown date')
                source = phone.get('source', 'Unknown source')
                print(f"   • {phone.get('phone')} (Changed: {date}, Source: {source})")
        
        # Current owner
        if 'current_owner' in provider and provider['current_owner']:
            print(f"👤 Current Owner: {provider['current_owner']}")
        
        # Previous owners
        if 'previous_owners' in provider and provider['previous_owners']:
            print(f"👤 Previous Owners:")
            for owner in provider['previous_owners']:
                date = owner.get('effective_date', 'Unknown date')
                source = owner.get('source', 'Unknown source')
                notes = owner.get('notes', '')
                owner_info = f"   • {owner.get('owner')} (Changed: {date}, Source: {source})"
                if notes:
                    owner_info += f"\n     Notes: {notes}"
                print(owner_info)
        
        # Any other fields
        skip_fields = {'id', 'business_name', 'dbas', 'current_address', 'previous_addresses',
                      'current_phone', 'previous_phones', 'current_owner', 'previous_owners'}
        other_fields = {k: v for k, v in provider.items() if k not in skip_fields}
        
        # Show data source URLs separately if present
        if 'data_source_urls' in provider and provider['data_source_urls']:
            print(f"\n🔗 Data Source URLs:")
            for url in provider['data_source_urls']:
                print(f"   • {url}")
            # Remove from other_fields to avoid duplication
            other_fields.pop('data_source_urls', None)
        
        if other_fields:
            print(f"\n📊 Additional Fields:")
            for field, value in other_fields.items():
                if value is not None:
                    print(f"   • {field}: {value}")
        
        print()
    
    print("="*80)
    print(f"✓ Displayed {len(providers)} provider(s)")
    print("="*80 + "\n")


def main():
    """Main execution."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            # Show all fields - pass None to get everything
            fields = None
        else:
            # Specific fields requested
            fields = sys.argv[1:]
    else:
        # Use default fields
        fields = None
    
    # Connect to database
    print("\nConnecting to database...")
    db = ProviderDatabaseManager()
    
    # Display providers
    providers = db.display_providers(fields=fields)
    
    # Format output
    format_output(providers, fields)


if __name__ == "__main__":
    main()
