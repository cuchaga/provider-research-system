# Development Guide

## Setup Development Environment

### 1. Clone and Create Virtual Environment

```bash
cd provider-research-skill

# Create isolated Python environment
python3 -m venv venv

# Activate it (ALWAYS do this first!)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Verify activation (prompt should show (venv))
which python3  # Should output: /path/to/provider-research-skill/venv/bin/python3
```

### 2. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies (testing, linting, formatting)
pip install -r requirements-dev.txt

# Install package in editable/development mode
# This means code changes take effect immediately without reinstalling
pip install -e .
```

### 3. Verify Installation

```bash
# Test import
python3 -c "from provider_research import ProviderOrchestrator; print('✓ Installation successful')"

# Run quick tests
pytest tests/test_validation.py -v
```

## Daily Development Workflow

### Always Start Here

```bash
# Navigate to project
cd /path/to/provider-research-skill

# Activate virtual environment
source venv/bin/activate

# Confirm you're in venv (should see (venv) in prompt)
echo $VIRTUAL_ENV
```

### Making Changes

```bash
# Edit code in provider_research/
# Changes are immediately available (no reinstall needed)

# Run tests after changes
pytest tests/ -v

# Run specific test file
pytest tests/test_validation.py -v

# Run with coverage report
pytest tests/ -v --cov=provider_research --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# OR
xdg-open htmlcov/index.html  # Linux
```

### Testing Your Changes

```bash
# Quick validation
python3 -c "from provider_research import YourNewClass; print('OK')"

# Run examples
python3 examples/basic_usage.py
python3 examples/franchise_research_usage.py

# Interactive testing
python3
>>> from provider_research import ProviderOrchestrator
>>> orchestrator = ProviderOrchestrator()
>>> # Test your changes here
```

### When Done

```bash
# Deactivate virtual environment
deactivate

# Prompt should return to normal (no (venv))
```

## VS Code Integration

The project includes `.vscode/settings.json` that automatically:
- Uses the `venv/bin/python` interpreter
- Activates the virtual environment in integrated terminal
- Configures pytest for testing
- Sets up Python formatter and linter

### First Time in VS Code

1. Open Command Palette: `Cmd/Ctrl + Shift + P`
2. Type: `Python: Select Interpreter`
3. Choose: `./venv/bin/python3`

The settings file handles the rest automatically!

## Common Issues

### "Module not found" errors

**Problem:** Python can't find your package
**Solution:** Make sure you installed in editable mode and venv is active

```bash
source venv/bin/activate
pip install -e .
```

### Wrong Python version

**Problem:** Using system Python instead of venv
**Solution:** Always activate venv first

```bash
# Check current Python
which python3

# Should output: /path/to/project/venv/bin/python3
# If not, activate venv:
source venv/bin/activate
```

### Changes not reflecting

**Problem:** Code changes don't take effect
**Solution:** Verify editable install

```bash
pip list | grep provider-research
# Should show path to your code directory:
# provider-research 2.0.0  /path/to/provider-research-skill
```

### Tests failing after install

**Problem:** Import errors or outdated dependencies
**Solution:** Reinstall dependencies

```bash
pip install -r requirements.txt --upgrade
pip install -r requirements-dev.txt --upgrade
pip install -e . --force-reinstall --no-deps
```

## Best Practices

### ✅ DO

- **Always activate venv** before working
- Use `pip install -e .` for development
- Run tests before committing
- Keep requirements.txt updated
- Use relative imports within package

### ❌ DON'T

- Install packages globally (use venv!)
- Commit `venv/` directory
- Commit `__pycache__/` or `*.pyc` files
- Mix system Python with venv packages

## Package Structure

```
provider_research/
├── __init__.py           # Package exports
├── core/                 # Core skills
│   ├── orchestrator.py
│   ├── query_interpreter.py
│   ├── semantic_matcher.py
│   └── franchise_researcher.py
├── database/             # Database backends
│   ├── manager.py
│   ├── postgres.py
│   └── sqlite.py
└── search/               # Search and research
    ├── web_researcher.py
    └── provider_search.py
```

### Adding New Modules

1. Create file in appropriate directory
2. Add imports to `__init__.py` if public API
3. Write tests in `tests/`
4. No reinstall needed (editable mode!)

## Debugging

### Using pdb

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or Python 3.7+
breakpoint()
```

### Using pytest debugging

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -v -s
```

### Using VS Code debugger

1. Set breakpoints in code (click left margin)
2. Press F5 or Run > Start Debugging
3. Choose "Python File" or "Python Module"

## Contributing

### Before Committing

```bash
# Ensure venv is active
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=provider_research --cov-report=term-missing

# Format code (if black is installed)
black provider_research/ tests/

# Lint code (if flake8 is installed)
flake8 provider_research/ tests/
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, test, commit
git add .
git commit -m "feat: description of changes"

# Push and create PR
git push origin feature/your-feature-name
```

## Resources

- **Documentation:** `docs/`
- **Examples:** `examples/`
- **Architecture:** `docs/architecture/`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **Project Context:** `PROJECT_CONTEXT.md`

## Questions?

Check the documentation:
- [Getting Started](docs/getting-started.md)
- [Project Context](../PROJECT_CONTEXT.md)
- [Quick Reference](../QUICK_REFERENCE.md)
