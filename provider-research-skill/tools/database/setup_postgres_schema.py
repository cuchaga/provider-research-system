#!/usr/bin/env python3
"""
PostgreSQL Schema Setup
=======================
Creates the database schema for the Provider Research System
"""

import sys

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}


def create_schema():
    """Create all database tables and indexes."""
    
    print("="*80)
    print("PostgreSQL Schema Setup")
    print("="*80)
    
    print(f"\n📡 Connecting to database...")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Database: {DB_CONFIG['database']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("✅ Connected")
        
        # Drop existing tables
        print("\n🗑️  Dropping existing tables (if any)...")
        cur.execute("DROP TABLE IF EXISTS search_history CASCADE")
        cur.execute("DROP TABLE IF EXISTS provider_history CASCADE")
        cur.execute("DROP TABLE IF EXISTS providers CASCADE")
        print("✅ Existing tables dropped")
        
        # Create providers table
        print("\n📊 Creating providers table...")
        cur.execute("""
            CREATE TABLE providers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                
                -- NPI and Names
                npi VARCHAR(10) UNIQUE,
                legal_name VARCHAR(500) NOT NULL,
                dba_names TEXT[],
                name_variations TEXT[],
                
                -- Address
                address_full TEXT,
                address_street VARCHAR(500),
                address_city VARCHAR(200),
                address_state VARCHAR(2),
                address_zip VARCHAR(10),
                
                -- URLs
                location_website TEXT,
                parent_website TEXT,
                alternative_urls TEXT[],
                data_source_urls TEXT[],  -- URLs where data was obtained (research sources)
                
                -- Organization
                parent_organization VARCHAR(500),
                real_estate_owner VARCHAR(500),
                franchise_status BOOLEAN DEFAULT FALSE,
                franchise_id VARCHAR(100),
                provider_type VARCHAR(200),
                
                -- NPI Data
                npi_taxonomy_code VARCHAR(20),
                npi_taxonomy_desc VARCHAR(500),
                npi_status VARCHAR(50),
                npi_enumeration_date DATE,
                
                -- Contact
                phone VARCHAR(20),
                fax VARCHAR(20),
                email VARCHAR(200),
                
                -- Metadata
                confidence_score DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Raw data (JSON)
                raw_search_data JSONB,
                raw_npi_data JSONB
            )
        """)
        print("✅ Providers table created")
        
        # Create search history table
        print("\n📊 Creating search_history table...")
        cur.execute("""
            CREATE TABLE search_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider_id UUID REFERENCES providers(id),
                search_query TEXT NOT NULL,
                search_location VARCHAR(200),
                match_found BOOLEAN,
                match_score DECIMAL(3,2),
                match_method VARCHAR(50),
                search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Search history table created")
        
        # Create provider history table
        print("\n📊 Creating provider_history table...")
        cur.execute("""
            CREATE TABLE provider_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider_id UUID REFERENCES providers(id),
                change_type VARCHAR(50) NOT NULL,
                field_name VARCHAR(100),
                old_value TEXT,
                new_value TEXT,
                effective_date DATE,
                source VARCHAR(200),
                notes TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Provider history table created")
        
        # Create indexes
        print("\n🔍 Creating indexes...")
        indexes = [
            "CREATE INDEX idx_providers_npi ON providers(npi)",
            "CREATE INDEX idx_providers_legal_name ON providers(legal_name)",
            "CREATE INDEX idx_providers_city_state ON providers(address_city, address_state)",
            "CREATE INDEX idx_providers_state ON providers(address_state)",
            "CREATE INDEX idx_providers_phone ON providers(phone)",
            "CREATE INDEX idx_providers_parent ON providers(parent_organization)",
            "CREATE INDEX idx_search_history_query ON search_history(search_query)",
            "CREATE INDEX idx_provider_history_provider ON provider_history(provider_id)"
        ]
        
        for idx_sql in indexes:
            cur.execute(idx_sql)
            print(f"   ✓ {idx_sql.split()[2]}")
        
        print("✅ All indexes created")
        
        # Create full-text search index
        print("\n🔍 Creating full-text search...")
        cur.execute("""
            ALTER TABLE providers 
            ADD COLUMN search_vector tsvector
        """)
        
        cur.execute("""
            CREATE INDEX idx_providers_search 
            ON providers 
            USING GIN(search_vector)
        """)
        
        # Create trigger to update search vector
        cur.execute("""
            CREATE OR REPLACE FUNCTION providers_search_trigger() 
            RETURNS trigger AS $$
            BEGIN
                NEW.search_vector := 
                    setweight(to_tsvector('english', COALESCE(NEW.legal_name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.dba_names, ' '), '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(NEW.address_city, '')), 'C') ||
                    setweight(to_tsvector('english', COALESCE(NEW.parent_organization, '')), 'C');
                RETURN NEW;
            END
            $$ LANGUAGE plpgsql
        """)
        
        cur.execute("""
            CREATE TRIGGER tsvector_update 
            BEFORE INSERT OR UPDATE ON providers
            FOR EACH ROW EXECUTE FUNCTION providers_search_trigger()
        """)
        
        print("✅ Full-text search configured")
        
        # Get table counts
        print("\n📊 Verifying schema...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Schema Setup Complete!")
        print("="*80)
        print("\n📝 Next Steps:")
        print("   1. Import data: python3 import_to_postgres.py")
        print("   2. Search providers: python3 search_postgres.py")
        print("")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        print("\n💡 Make sure PostgreSQL is running:")
        print("   brew services start postgresql@16")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_schema()
    sys.exit(0 if success else 1)
