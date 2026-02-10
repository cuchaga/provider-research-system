#!/usr/bin/env python3
"""Display all Home Instead franchises in the database"""

from provider_research.database import ProviderDatabaseManager

db = ProviderDatabaseManager({
    'host': 'localhost',
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
})

# Search for all Home Instead locations
results = db.search(query='Home Instead')

print('\n' + '='*80)
print(f'  HOME INSTEAD FRANCHISES IN DATABASE')
print('='*80)
print(f'\nTotal Locations: {len(results)}\n')

for i, result in enumerate(results, 1):
    p = result.provider
    print(f'{i}. {p["legal_name"]}')
    print(f'   📍 {p["address_full"]}')
    print(f'   ☎️  {p["phone"] or "N/A"}')
    
    if p.get('location_website'):
        print(f'   🌐 {p["location_website"]}')
    
    if p.get('parent_organization'):
        print(f'   🏢 Parent: {p["parent_organization"]}')
    
    dba_names = p.get('dba_names', [])
    if dba_names:
        print(f'   📝 Also known as: {", ".join(dba_names)}')
    
    if p.get('npi'):
        print(f'   🏥 NPI: {p["npi"]}')
    
    print(f'   📊 Match: {result.match_type} (score: {result.match_score:.2f})')
    print()

print('='*80)
print(f'\n✓ Displayed {len(results)} Home Instead franchise locations\n')
