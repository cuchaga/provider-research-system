#!/usr/bin/env python3
"""
Display detailed Home Instead franchise information including historical data
"""

import psycopg2
from datetime import datetime

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='providers',
    user='provider_admin',
    password='provider123'
)

cur = conn.cursor()

# Get all Home Instead providers with their history
cur.execute("""
    SELECT 
        p.id,
        p.legal_name,
        p.dba_names,
        p.address_full,
        p.address_street,
        p.address_city,
        p.address_state,
        p.address_zip,
        p.phone,
        p.parent_organization,
        p.real_estate_owner,
        p.location_website,
        p.created_at,
        p.last_updated
    FROM providers p
    WHERE p.legal_name LIKE '%Home Instead%'
    ORDER BY p.address_city, p.legal_name
""")

providers = cur.fetchall()

print('\n' + '='*90)
print('  HOME INSTEAD FRANCHISES - DETAILED BUSINESS INFORMATION')
print('='*90)
print(f'\nTotal Locations: {len(providers)}\n')

for i, provider in enumerate(providers, 1):
    (provider_id, legal_name, dba_names, address_full, address_street, 
     city, state, zip_code, phone, parent_org, real_estate_owner, 
     website, created_at, last_updated) = provider
    
    print('='*90)
    print(f'{i}. {legal_name}')
    print('='*90)
    
    # Business Names
    print('\n📋 BUSINESS NAMES:')
    print(f'  Legal Name:        {legal_name}')
    if dba_names:
        print(f'  DBA Names:         {", ".join(dba_names)}')
    else:
        print(f'  DBA Names:         (none on file)')
    
    # Current Address
    print('\n📍 CURRENT ADDRESS:')
    print(f'  Street:            {address_street or address_full}')
    print(f'  City:              {city}, {state} {zip_code}')
    print(f'  Full:              {address_full}')
    
    # Current Contact
    print('\n☎️  CURRENT CONTACT:')
    print(f'  Phone:             {phone or "N/A"}')
    if website:
        print(f'  Website:           {website}')
    
    # Current Ownership
    print('\n🏢 CURRENT OWNERSHIP:')
    print(f'  Parent Org:        {parent_org or "N/A"}')
    if real_estate_owner:
        print(f'  Property Owner:    {real_estate_owner}')
    else:
        print(f'  Property Owner:    (not tracked)')
    
    # Check for historical changes
    cur.execute("""
        SELECT 
            change_type,
            field_name,
            old_value,
            new_value,
            effective_date,
            source,
            notes
        FROM provider_history
        WHERE provider_id = %s
        ORDER BY effective_date DESC, recorded_at DESC
    """, (provider_id,))
    
    history = cur.fetchall()
    
    if history:
        print('\n📜 HISTORICAL CHANGES:')
        
        # Group by change type
        address_changes = [h for h in history if 'address' in h[1].lower()]
        phone_changes = [h for h in history if 'phone' in h[1].lower()]
        owner_changes = [h for h in history if 'owner' in h[1].lower() or 'parent' in h[1].lower()]
        name_changes = [h for h in history if 'name' in h[1].lower()]
        
        if address_changes:
            print('\n  Previous Addresses:')
            for change in address_changes:
                change_type, field, old_val, new_val, date, source, notes = change
                print(f'    • {old_val}')
                print(f'      → Changed to: {new_val}')
                print(f'      Date: {date}, Source: {source}')
        
        if phone_changes:
            print('\n  Previous Phone Numbers:')
            for change in phone_changes:
                change_type, field, old_val, new_val, date, source, notes = change
                print(f'    • {old_val} → {new_val}')
                print(f'      Date: {date}, Source: {source}')
        
        if owner_changes:
            print('\n  Previous Owners:')
            for change in owner_changes:
                change_type, field, old_val, new_val, date, source, notes = change
                print(f'    • {old_val}')
                print(f'      → Acquired by: {new_val}')
                print(f'      Date: {date}, Source: {source}')
                if notes:
                    print(f'      Notes: {notes}')
        
        if name_changes:
            print('\n  Previous Business Names:')
            for change in name_changes:
                change_type, field, old_val, new_val, date, source, notes = change
                print(f'    • {old_val} → {new_val}')
                print(f'      Date: {date}, Source: {source}')
    else:
        print('\n📜 HISTORICAL CHANGES:')
        print('  No historical changes recorded')
        print('  (This is current data as first entered in system)')
    
    # Metadata
    print(f'\n📊 RECORD METADATA:')
    print(f'  First Added:       {created_at.strftime("%Y-%m-%d %H:%M")}')
    print(f'  Last Updated:      {last_updated.strftime("%Y-%m-%d %H:%M")}')
    print(f'  Record ID:         {provider_id}')
    
    print()

print('='*90)
print('\n💡 NOTE: Historical data (previous addresses, phone numbers, owners) will appear')
print('   above when changes are tracked in the system. To add historical data:')
print()
print('   1. Use the FranchiseResearcher with include_history=True')
print('   2. Manually add via provider_history table')
print('   3. Web research will automatically track changes over time')
print()
print('='*90)

conn.close()
