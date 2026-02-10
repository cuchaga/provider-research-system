# Provider Research System - Examples

This directory contains example code demonstrating how to use the Provider Research System.

## Examples

### Basic Usage
- **[basic_usage.py](basic_usage.py)** - Simple provider search and lookup

### Advanced Examples
- **[advanced_orchestration.py](advanced_orchestration.py)** - Complex multi-step workflows

## Running Examples

### Python Scripts

```bash
# Activate virtual environment
source venv/bin/activate

# Run basic usage example
python examples/basic_usage.py

# Run advanced example
python examples/advanced_orchestration.py
```

### Jupyter Notebooks

```bash
# Install Jupyter if not already installed
pip install jupyter

# Start Jupyter
jupyter notebook examples/notebooks/
```

## Prerequisites

Make sure you have:
1. Installed the package: `pip install -e .`
2. Set up your environment variables (copy `config/.env.example` to `.env`)
3. Initialized the database by running:
   ```bash
   python3 tools/database/setup_postgres_schema.py
   ```

## Support

For more information, see the main [documentation](../docs/).
