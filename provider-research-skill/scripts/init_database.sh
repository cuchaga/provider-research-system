#!/bin/bash
# Database initialization script for Provider Research Skill

set -e

echo "=================================================="
echo "Provider Research Skill - Database Setup"
echo "=================================================="

# Configuration
DB_NAME="${DB_NAME:-providers}"
DB_USER="${DB_USER:-provider_admin}"
DB_PASS="${DB_PASS:-provider123}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo ""
echo "Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST:$DB_PORT"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start it first."
    echo "   sudo service postgresql start"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database and user
echo ""
echo "Creating database and user..."

sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "✅ Database and user created"

# Create schema
echo ""
echo "Creating schema..."

PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'
-- Main providers table
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    npi VARCHAR(10) UNIQUE,
    legal_name TEXT NOT NULL,
    dba_names JSONB DEFAULT '[]',
    name_variations JSONB DEFAULT '[]',
    
    -- Location
    address_full TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state VARCHAR(2),
    address_zip VARCHAR(10),
    
    -- URLs
    location_website TEXT,
    parent_website TEXT,
    alternative_urls JSONB DEFAULT '[]',
    
    -- Organization
    parent_organization TEXT,
    franchise_status BOOLEAN DEFAULT FALSE,
    franchise_id TEXT,
    provider_type TEXT,
    
    -- NPI data
    npi_taxonomy_code TEXT,
    npi_taxonomy_desc TEXT,
    npi_status TEXT,
    npi_enumeration_date DATE,
    
    -- Contact
    phone VARCHAR(20),
    fax VARCHAR(20),
    email TEXT,
    
    -- Metadata
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Complete data (JSON storage)
    raw_search_data JSONB,
    raw_npi_data JSONB
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES providers(id),
    search_query TEXT,
    search_location TEXT,
    match_found BOOLEAN,
    match_score DECIMAL(3,2),
    match_method TEXT,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research sessions table
CREATE TABLE IF NOT EXISTS research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    state VARCHAR(2),
    city TEXT,
    claimed_count INTEGER,
    extracted_count INTEGER,
    unique_count INTEGER,
    duplicates_removed INTEGER,
    token_cost INTEGER,
    status TEXT DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_providers_npi ON providers(npi);
CREATE INDEX IF NOT EXISTS idx_providers_legal_name ON providers(legal_name);
CREATE INDEX IF NOT EXISTS idx_providers_legal_name_lower ON providers(LOWER(legal_name));
CREATE INDEX IF NOT EXISTS idx_providers_city_state ON providers(address_city, address_state);
CREATE INDEX IF NOT EXISTS idx_providers_state ON providers(address_state);
CREATE INDEX IF NOT EXISTS idx_providers_phone ON providers(phone);
CREATE INDEX IF NOT EXISTS idx_providers_parent_org ON providers(parent_organization);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_providers_name_fts ON providers USING GIN (to_tsvector('english', legal_name));

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO provider_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO provider_admin;
EOF

echo "✅ Schema created"

# Verify
echo ""
echo "Verifying setup..."

PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt"

echo ""
echo "=================================================="
echo "✅ Database setup complete!"
echo "=================================================="
echo ""
echo "Connection string:"
echo "  postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
