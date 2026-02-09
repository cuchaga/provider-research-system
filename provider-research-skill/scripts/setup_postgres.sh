#!/bin/bash
#
# PostgreSQL Local Setup - macOS
# ================================
# Sets up PostgreSQL locally for the Provider Research System
#

set -e  # Exit on error

echo "================================================================================"
echo "PostgreSQL Local Setup for Provider Research System"
echo "================================================================================"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo ""
    echo "📦 PostgreSQL not found. Installing via Homebrew..."
    echo ""
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install PostgreSQL
    echo "Installing PostgreSQL..."
    brew install postgresql@16
    
    # Add to PATH
    echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
    
    echo "✅ PostgreSQL installed"
else
    echo "✅ PostgreSQL already installed"
    psql --version
fi

echo ""
echo "🚀 Starting PostgreSQL service..."

# Start PostgreSQL service
brew services start postgresql@16 || brew services restart postgresql@16

# Wait for PostgreSQL to start
echo "⏳ Waiting for PostgreSQL to start..."
sleep 3

echo ""
echo "📊 Creating database and user..."

# Create database and user
psql postgres << EOF
-- Drop existing database if it exists (for clean setup)
DROP DATABASE IF EXISTS providers;
DROP USER IF EXISTS provider_admin;

-- Create user
CREATE USER provider_admin WITH PASSWORD 'provider123';

-- Create database
CREATE DATABASE providers OWNER provider_admin;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE providers TO provider_admin;

\c providers

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO provider_admin;

\q
EOF

echo "✅ Database 'providers' created"
echo "✅ User 'provider_admin' created"

echo ""
echo "================================================================================"
echo "✅ PostgreSQL Setup Complete!"
echo "================================================================================"
echo ""
echo "📊 Database Information:"
echo "   Host:     localhost"
echo "   Port:     5432"
echo "   Database: providers"
echo "   User:     provider_admin"
echo "   Password: provider123"
echo ""
echo "🔧 Useful Commands:"
echo "   Start:    brew services start postgresql@16"
echo "   Stop:     brew services stop postgresql@16"
echo "   Restart:  brew services restart postgresql@16"
echo "   Status:   brew services list | grep postgresql"
echo "   Connect:  psql -U provider_admin -d providers"
echo ""
echo "📝 Next Steps:"
echo "   1. Create tables: python3 setup_postgres_schema.py"
echo "   2. Import data:   python3 import_to_postgres.py"
echo "   3. Search:        python3 search_postgres.py"
echo ""
