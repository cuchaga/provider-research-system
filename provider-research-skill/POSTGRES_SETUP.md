# PostgreSQL Local Setup Guide

## Quick Start (3 Steps)

### Step 1: Install PostgreSQL

```bash
# Make setup script executable
chmod +x scripts/setup_postgres.sh

# Run setup (installs PostgreSQL if needed)
./scripts/setup_postgres.sh
```

This will:
- Install PostgreSQL via Homebrew (if not installed)
- Start PostgreSQL service
- Create database `providers`
- Create user `provider_admin` with password `provider123`

### Step 2: Create Schema

```bash
python3 setup_postgres_schema.py
```

This creates:
- `providers` table (main provider data)
- `search_history` table (search tracking)
- `provider_history` table (historical changes)
- Indexes for fast searching
- Full-text search capabilities

### Step 3: Import Data

```bash
python3 import_to_postgres.py
```

This imports all providers from `data/db_state_cleaned.json` into PostgreSQL.

---

## Using the Database

### Option 1: Interactive Search

```bash
python3 search_postgres.py
```

Interactive menu:
1. Search by name
2. Search by name and state
3. Search by name and city
4. Full-text search (advanced)
5. List all providers
6. Exit

### Option 2: Command Line Search

```bash
# Search by name
python3 search_postgres.py "Home Instead"

# Search by name and state
python3 search_postgres.py "Home Instead" MA

# Full-text search
python3 search_postgres.py "care senior" --fulltext
```

### Option 3: Direct SQL

```bash
# Connect to database
psql -U provider_admin -d providers

# Example queries
SELECT legal_name, address_city, address_state FROM providers;

SELECT * FROM providers WHERE address_state = 'MA';

SELECT legal_name, phone FROM providers 
WHERE legal_name ILIKE '%comfort%';
```

---

## Database Information

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `providers` |
| User | `provider_admin` |
| Password | `provider123` |

---

## PostgreSQL Service Management

```bash
# Start PostgreSQL
brew services start postgresql@16

# Stop PostgreSQL
brew services stop postgresql@16

# Restart PostgreSQL
brew services restart postgresql@16

# Check status
brew services list | grep postgresql

# Check if running
psql -U provider_admin -d providers -c "SELECT 1"
```

---

## Troubleshooting

### PostgreSQL won't start

```bash
# Check if already running
ps aux | grep postgres

# Check Homebrew services
brew services list

# View logs
tail -f /opt/homebrew/var/log/postgresql@16.log
```

### Can't connect to database

```bash
# Verify PostgreSQL is running
brew services list | grep postgresql

# Check if database exists
psql postgres -c "\l" | grep providers

# Recreate database if needed
./scripts/setup_postgres.sh
```

### Schema errors

```bash
# Drop and recreate schema
python3 setup_postgres_schema.py
```

---

## Python Code Examples

### Using ProviderDatabaseManager

```python
from provider_database_manager import ProviderDatabaseManager

# Connect to local PostgreSQL
db = ProviderDatabaseManager({
    'host': 'localhost',
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
})

# Search providers
results = db.search(
    query="Home Instead",
    state="MA",
    fuzzy=True
)

for result in results:
    print(f"{result.provider['legal_name']} - {result.match_score:.2f}")
```

### Direct psycopg2 Usage

```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    database='providers',
    user='provider_admin',
    password='provider123'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# Search
cur.execute("""
    SELECT legal_name, address_city, address_state, phone
    FROM providers
    WHERE legal_name ILIKE %s
    ORDER BY legal_name
""", ('%Home Instead%',))

for row in cur.fetchall():
    print(f"{row['legal_name']} - {row['address_city']}, {row['address_state']}")

conn.close()
```

---

## Advanced Features

### Full-Text Search

```sql
-- Search using full-text
SELECT legal_name, address_city, address_state,
       ts_rank(search_vector, plainto_tsquery('english', 'home care')) AS rank
FROM providers
WHERE search_vector @@ plainto_tsquery('english', 'home care')
ORDER BY rank DESC;
```

### Provider with History

```sql
-- Get provider and all historical changes
SELECT p.legal_name, h.change_type, h.old_value, h.new_value, h.effective_date
FROM providers p
LEFT JOIN provider_history h ON p.id = h.provider_id
WHERE p.legal_name ILIKE '%Home Instead%'
ORDER BY h.effective_date DESC;
```

### Search Analytics

```sql
-- Most searched providers
SELECT provider_id, COUNT(*) as search_count
FROM search_history
WHERE match_found = TRUE
GROUP BY provider_id
ORDER BY search_count DESC
LIMIT 10;
```

---

## Benefits of PostgreSQL vs SQLite

| Feature | PostgreSQL | SQLite |
|---------|-----------|--------|
| Performance | ⭐⭐⭐⭐⭐ Excellent for large datasets | ⭐⭐⭐ Good for small datasets |
| Full-text search | ✅ Built-in, powerful | ⚠️ Limited |
| Concurrent access | ✅ Multiple users | ❌ Single writer |
| JSON support | ✅ JSONB (indexed) | ⚠️ Basic |
| Array support | ✅ Native arrays | ❌ None |
| Triggers/Functions | ✅ Full PL/pgSQL | ⚠️ Limited |
| Deployment | ⚠️ Requires server | ✅ Single file |

---

## Data Backup

### Export Database

```bash
# Full database dump
pg_dump -U provider_admin providers > providers_backup.sql

# Data only (no schema)
pg_dump -U provider_admin --data-only providers > providers_data.sql

# Specific table
pg_dump -U provider_admin -t providers providers > providers_table.sql
```

### Restore Database

```bash
# Restore full backup
psql -U provider_admin providers < providers_backup.sql

# Restore data only
psql -U provider_admin providers < providers_data.sql
```

### Export to CSV

```sql
-- Export providers to CSV
COPY (SELECT * FROM providers) 
TO '/tmp/providers.csv' 
WITH (FORMAT CSV, HEADER);
```

---

## Next Steps

1. ✅ PostgreSQL installed and running
2. ✅ Schema created
3. ✅ Data imported
4. 🔄 Start searching and querying
5. 🔄 Integrate with provider research system
6. 🔄 Enable real web scraping for enrichment

**You now have a production-ready local PostgreSQL database for provider research!** 🎉
