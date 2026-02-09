#!/usr/bin/env python3
"""
Import Cleaned Data to PostgreSQL
==================================
Imports providers from db_state_cleaned.json into PostgreSQL
"""

import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import execute_values


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}


def import_providers(json_path: str):
    """Import providers from JSON file to PostgreSQL."""
    
    print("="*80)
    print("Import Data to PostgreSQL")
    print("="*80)
    
    # Load JSON data
    print(f"\n📂 Loading data from: {json_path}")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    providers = data.get('providers', [])
    print(f"✅ Loaded {len(providers)} healthcare providers")
    
    # Connect to database
    print(f"\n📡 Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ Connected")
        
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        cur.execute("DELETE FROM search_history")
        cur.execute("DELETE FROM provider_history")
        cur.execute("DELETE FROM providers")
        conn.commit()
        print("✅ Existing data cleared")
        
        # Import providers
        print(f"\n📥 Importing {len(providers)} providers...")
        imported = 0
        errors = 0
        
        for provider in providers:
            try:
                # Skip placeholder NPIs from simulation mode
                npi = provider.get('npi')
                if npi == '1234567890':
                    npi = None  # Clear simulation placeholder
                
                # Convert Python types to PostgreSQL types
                cur.execute("""
                    INSERT INTO providers (
                        id, npi, legal_name, dba_names, name_variations,
                        address_full, address_street, address_city, address_state, address_zip,
                        location_website, parent_website, alternative_urls,
                        parent_organization, real_estate_owner,
                        franchise_status, franchise_id, provider_type,
                        npi_taxonomy_code, npi_taxonomy_desc, npi_status, npi_enumeration_date,
                        phone, fax, email,
                        confidence_score, created_at, validated_at, last_updated,
                        raw_search_data, raw_npi_data
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s
                    )
                """, (
                    provider.get('id'),
                    npi,  # Use filtered NPI
                    provider.get('legal_name'),
                    provider.get('dba_names', []),
                    provider.get('name_variations', []),
                    provider.get('address_full'),
                    provider.get('address_street'),
                    provider.get('address_city'),
                    provider.get('address_state'),
                    provider.get('address_zip'),
                    provider.get('location_website'),
                    provider.get('parent_website'),
                    provider.get('alternative_urls', []),
                    provider.get('parent_organization'),
                    provider.get('real_estate_owner'),
                    provider.get('franchise_status', False),
                    provider.get('franchise_id'),
                    provider.get('provider_type'),
                    provider.get('npi_taxonomy_code'),
                    provider.get('npi_taxonomy_desc'),
                    provider.get('npi_status'),
                    provider.get('npi_enumeration_date'),
                    provider.get('phone'),
                    provider.get('fax'),
                    provider.get('email'),
                    provider.get('confidence_score'),
                    provider.get('created_at'),
                    provider.get('validated_at'),
                    provider.get('last_updated'),
                    json.dumps(provider.get('raw_search_data')) if provider.get('raw_search_data') else None,
                    json.dumps(provider.get('raw_npi_data')) if provider.get('raw_npi_data') else None
                ))
                
                imported += 1
                print(f"   ✓ {provider['legal_name']}")
                
            except Exception as e:
                errors += 1
                print(f"   ✗ {provider.get('legal_name', 'Unknown')}: {e}")
        
        conn.commit()
        
        print(f"\n✅ Import complete:")
        print(f"   • Imported: {imported}")
        print(f"   • Errors: {errors}")
        
        # Verify import
        print("\n📊 Verifying database...")
        cur.execute("SELECT COUNT(*) FROM providers")
        count = cur.fetchone()[0]
        print(f"✅ Database contains {count} providers")
        
        # Show sample data
        print("\n📋 Sample providers:")
        cur.execute("""
            SELECT legal_name, address_city, address_state, phone 
            FROM providers 
            LIMIT 3
        """)
        for row in cur.fetchall():
            print(f"   • {row[0]} ({row[1]}, {row[2]}) - {row[3]}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Import Complete!")
        print("="*80)
        print("\n📝 Next Steps:")
        print("   • Search providers: python3 search_postgres.py")
        print("   • Connect directly: psql -U provider_admin -d providers")
        print("")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check PostgreSQL is running: brew services list | grep postgresql")
        print("   2. Verify schema exists: python3 setup_postgres_schema.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Default path to cleaned data
    json_path = Path(__file__).parent / "data" / "db_state_cleaned.json"
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        print("\n💡 Make sure you've run the enrichment pipeline:")
        print("   python3 enrich_and_deduplicate.py")
        sys.exit(1)
    
    success = import_providers(str(json_path))
    sys.exit(0 if success else 1)
