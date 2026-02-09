# Getting Started with Provider Research System

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/cuchaga/provider-research-system.git
cd provider-research-system/provider-research-skill

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using pip (when published)

```bash
pip install provider-research
```

## Quick Start

### 1. Configuration

Copy the example environment file:

```bash
cp config/.env.example .env
```

Edit `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=your_key_here
DATABASE_TYPE=sqlite
```

### 2. Initialize Database

For SQLite (development):

```bash
# Database will be created automatically
```

For PostgreSQL (production):

```bash
# Setup schema
python tools/database/setup_postgres_schema.py

# Import sample data (optional)
python tools/database/import_to_postgres.py
```

### 3. Basic Usage

```python
from provider_research import ProviderOrchestrator

# Initialize
orchestrator = ProviderOrchestrator()

# Search for providers
result = orchestrator.process_query(
    user_query="Find Home Instead locations in Massachusetts"
)

# Display results
print(f"Found {len(result.providers)} providers")
for provider in result.providers:
    print(f"- {provider['legal_name']}")
```

## Configuration

### Database Configuration

Create `config/database/sqlite.yml`:

```yaml
database:
  type: sqlite
  sqlite:
    path: data/providers.db
```

Or `config/database/postgres.yml`:

```yaml
database:
  type: postgres
  postgres:
    host: localhost
    port: 5432
    database: providers
    user: provider_admin
    password: your_password
```

### LLM Configuration

Set environment variables:

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY=your_key

# For OpenAI
export OPENAI_API_KEY=your_key
```

## Next Steps

- [Read the Architecture Overview](architecture/overview.md)
- [Explore Example Code](../examples/)
- [Learn about the API](api/orchestrator.md)
- [Set up PostgreSQL](guides/database-setup.md)

## Common Issues

### Module Not Found

Make sure you've installed the package:
```bash
pip install -e .
```

### Database Connection Error

Check your database configuration in `.env` or config files.

### LLM API Error

Verify your API key is set correctly:
```bash
echo $ANTHROPIC_API_KEY
```

For more help, see [Troubleshooting Guide](guides/troubleshooting.md).
