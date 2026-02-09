# Folder Hierarchy Plan - Provider Research System v2.0.0

## Executive Summary
This document outlines the recommended folder structure for the Provider Research System, following Python packaging best practices while maintaining clear separation of concerns.

---

## Current Structure Analysis

### ✅ What's Working Well
1. **Core package structure** (`provider_research/`) is well-organized with clear submodules
2. **Separation of concerns** between core, database, and search modules
3. **Tools directory** for CLI utilities is appropriate
4. **Documentation** in dedicated `docs/` folder

### ❌ Areas for Improvement
1. Test files mixed with source code (test_validation.py at root)
2. Documentation files scattered (ARCHITECTURE.md, POSTGRES_SETUP.md at root)
3. No examples/demos directory for users
4. No configuration templates directory
5. Scripts vs tools distinction unclear
6. Empty data directory

---

## Recommended Folder Hierarchy

```
provider-research-skill/
│
├── .github/                          # GitHub-specific files
│   ├── workflows/                    # CI/CD workflows
│   │   ├── tests.yml                 # Run tests on push/PR
│   │   └── publish.yml               # Publish to PyPI
│   └── ISSUE_TEMPLATE/               # Issue templates
│       ├── bug_report.md
│       └── feature_request.md
│
├── docs/                             # 📚 All documentation
│   ├── index.md                      # Main documentation index
│   ├── getting-started.md            # Quick start guide
│   ├── architecture/                 # Architecture documentation
│   │   ├── overview.md               # High-level architecture
│   │   ├── v2-multi-skill.md         # v2.0 architecture details
│   │   ├── diagrams/                 # Architecture diagrams
│   │   │   ├── architecture-complete.mermaid
│   │   │   ├── architecture-diagram.mermaid
│   │   │   └── architecture-diagram.html
│   │   └── migration-guide.md        # v1 to v2 migration
│   ├── api/                          # API reference
│   │   ├── orchestrator.md
│   │   ├── query-interpreter.md
│   │   ├── database-manager.md
│   │   ├── semantic-matcher.md
│   │   └── web-researcher.md
│   ├── guides/                       # How-to guides
│   │   ├── database-setup.md         # PostgreSQL/SQLite setup
│   │   ├── development.md            # Development guide
│   │   ├── deployment.md             # Deployment guide
│   │   └── troubleshooting.md        # Common issues
│   └── changelog.md                  # Version history
│
├── config/                           # 📋 Configuration templates
│   ├── database/
│   │   ├── postgres.example.yml      # PostgreSQL config template
│   │   └── sqlite.example.yml        # SQLite config template
│   ├── logging.example.yml           # Logging configuration
│   └── .env.example                  # Environment variables template
│
├── provider_research/                # 🎯 Main package (source code)
│   ├── __init__.py                   # Package initialization
│   ├── __version__.py                # Version info (NEW)
│   ├── config.py                     # Configuration loader (NEW)
│   ├── exceptions.py                 # Custom exceptions (NEW)
│   │
│   ├── core/                         # Core orchestration & AI
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Main orchestrator
│   │   ├── query_interpreter.py      # NLU skill
│   │   ├── semantic_matcher.py       # Semantic matching skill
│   │   └── research_llm.py           # Legacy LLM module
│   │
│   ├── database/                     # Data persistence
│   │   ├── __init__.py
│   │   ├── manager.py                # Database manager skill
│   │   ├── postgres.py               # PostgreSQL implementation
│   │   ├── sqlite.py                 # SQLite implementation
│   │   └── models.py                 # Data models (NEW)
│   │
│   ├── search/                       # Search & research
│   │   ├── __init__.py
│   │   ├── web_researcher.py         # Web research skill
│   │   ├── provider_search.py        # Legacy search
│   │   └── npi_registry.py           # NPI lookup (NEW)
│   │
│   └── utils/                        # 🛠️ Utilities (NEW)
│       ├── __init__.py
│       ├── validators.py             # Input validation
│       ├── formatters.py             # Output formatting
│       └── logger.py                 # Logging utilities
│
├── tools/                            # 🔧 CLI tools & utilities
│   ├── __init__.py
│   ├── cli.py                        # Main CLI entry point (NEW)
│   ├── database/                     # Database tools
│   │   ├── __init__.py
│   │   ├── setup_postgres_schema.py  # Schema setup
│   │   ├── import_to_postgres.py     # Data import
│   │   └── search_postgres.py        # Search CLI
│   └── data/                         # Data processing tools
│       ├── __init__.py
│       └── enrich_and_deduplicate.py # Data enrichment
│
├── tests/                            # 🧪 All tests (NEW location)
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── test_validation.py            # Import/smoke tests
│   │
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── test_orchestrator.py
│   │   ├── test_query_interpreter.py
│   │   ├── test_semantic_matcher.py
│   │   ├── test_database_manager.py
│   │   └── test_web_researcher.py
│   │
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── test_full_workflow.py
│   │   ├── test_database_ops.py
│   │   └── test_search_pipeline.py
│   │
│   └── fixtures/                     # Test data
│       ├── __init__.py
│       ├── sample_providers.json
│       └── mock_responses.py
│
├── examples/                         # 💡 Example code (NEW)
│   ├── README.md                     # Examples overview
│   ├── basic_usage.py                # Simple usage example
│   ├── advanced_orchestration.py    # Complex workflows
│   ├── custom_database.py            # Custom DB implementation
│   ├── web_scraping_demo.py          # Web research demo
│   └── notebooks/                    # Jupyter notebooks
│       ├── quick_start.ipynb
│       └── data_analysis.ipynb
│
├── scripts/                          # 🚀 Setup & deployment scripts
│   ├── setup_postgres.sh             # Database setup
│   ├── setup_dev_environment.sh      # Development environment (NEW)
│   ├── run_tests.sh                  # Test runner (NEW)
│   └── deploy.sh                     # Deployment script (NEW)
│
├── data/                             # 📊 Data files (runtime)
│   ├── .gitkeep                      # Keep directory in git
│   ├── providers.db                  # SQLite database (gitignored)
│   ├── cache/                        # LLM response cache (gitignored)
│   └── exports/                      # Data exports (gitignored)
│
├── .github/                          # GitHub configuration
├── .gitignore                        # Git ignore rules
├── .env.example                      # Environment template
├── README.md                         # Main readme
├── LICENSE                           # License file
├── setup.py                          # Package setup
├── setup.cfg                         # Setup configuration (NEW)
├── pyproject.toml                    # Modern Python project config (NEW)
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies (NEW)
├── MANIFEST.in                       # Package manifest (NEW)
├── CHANGELOG.md                      # Version history (moved from docs)
└── CONTRIBUTING.md                   # Contribution guidelines (NEW)
```

---

## File Organization Rules

### 📦 Package Code (`provider_research/`)
**Purpose**: Production code only  
**Rules**:
- One class per file (when possible)
- Clear module hierarchy
- All imports use absolute paths
- No test code in package

### 🧪 Tests (`tests/`)
**Purpose**: All testing code  
**Rules**:
- Mirror package structure in unit tests
- Integration tests for workflows
- Fixtures separate from tests
- Use pytest conventions

### 🔧 Tools (`tools/`)
**Purpose**: Standalone CLI utilities  
**Rules**:
- Can be run independently
- Each tool is self-contained
- Tools can import from package
- Include help text and examples

### 🚀 Scripts (`scripts/`)
**Purpose**: Setup, deployment, automation  
**Rules**:
- Shell scripts for environment setup
- Build and deployment automation
- Not imported by package code
- Should be executable

### 💡 Examples (`examples/`)
**Purpose**: Educational and demo code  
**Rules**:
- Show best practices
- Fully documented
- Can be copy-pasted by users
- Keep simple and focused

### 📚 Documentation (`docs/`)
**Purpose**: All documentation files  
**Rules**:
- Markdown format
- Organized by topic
- Include diagrams and examples
- Keep README.md in root minimal

---

## Migration Plan

### Phase 1: Create New Structure (No Breaking Changes)
```bash
# Create new directories
mkdir -p tests/{unit,integration,fixtures}
mkdir -p examples/notebooks
mkdir -p config/database
mkdir -p docs/{api,guides,architecture/diagrams}
mkdir -p tools/{database,data}
mkdir -p provider_research/utils
mkdir -p data/{cache,exports}
mkdir -p .github/workflows
```

### Phase 2: Move Files
```bash
# Move documentation
mv ARCHITECTURE.md docs/architecture/overview.md
mv POSTGRES_SETUP.md docs/guides/database-setup.md
mv PROJECT_STRUCTURE.md docs/architecture/project-structure.md
mv docs/architecture-*.* docs/architecture/diagrams/

# Move tests
mv test_validation.py tests/

# Reorganize tools
mv tools/setup_postgres_schema.py tools/database/
mv tools/import_to_postgres.py tools/database/
mv tools/search_postgres.py tools/database/
mv tools/enrich_and_deduplicate.py tools/data/

# Create placeholders
touch data/.gitkeep
touch examples/README.md
```

### Phase 3: Create New Files
```bash
# Configuration
touch config/.env.example
touch config/database/postgres.example.yml
touch config/database/sqlite.example.yml

# Package improvements
touch provider_research/__version__.py
touch provider_research/config.py
touch provider_research/exceptions.py
touch provider_research/utils/{__init__.py,validators.py,formatters.py,logger.py}

# Testing infrastructure
touch tests/{conftest.py,__init__.py}
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/fixtures/__init__.py

# Examples
touch examples/{basic_usage.py,advanced_orchestration.py}

# Documentation
touch docs/index.md
touch docs/getting-started.md
touch docs/changelog.md
touch CONTRIBUTING.md

# Modern Python packaging
touch pyproject.toml
touch setup.cfg
touch requirements-dev.txt
touch MANIFEST.in
```

### Phase 4: Update References
- Update imports in all files
- Update documentation links
- Update CI/CD paths
- Update .gitignore

---

## Benefits of New Structure

### 🎯 For Developers
- **Clear separation** between source, tests, examples, and docs
- **Easy navigation** - predictable file locations
- **Better testing** - dedicated test structure
- **Modern tooling** - pyproject.toml support

### 👥 For Users
- **Better onboarding** - dedicated examples directory
- **Comprehensive docs** - organized by topic
- **Configuration templates** - easy setup
- **Clear versioning** - CHANGELOG.md

### 🔧 For Maintenance
- **Scalability** - room for growth
- **CI/CD ready** - standard structure
- **Package distribution** - follows Python standards
- **Tool integration** - works with standard tools

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Create backup** of current structure
3. **Execute Phase 1-2** (structural changes)
4. **Test thoroughly** after each phase
5. **Update documentation** as files move
6. **Commit incrementally** with clear messages

---

## Standard Python Package Files

### Essential Files to Add

#### `pyproject.toml` (Modern Python standard)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "provider-research"
version = "2.0.0"
description = "Multi-skill healthcare provider research system"
readme = "README.md"
requires-python = ">=3.9"
```

#### `setup.cfg` (Configuration)
```ini
[metadata]
name = provider-research
version = 2.0.0

[options]
packages = find:
python_requires = >=3.9
```

#### `requirements-dev.txt` (Development dependencies)
```
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

#### `MANIFEST.in` (Package data)
```
include README.md
include LICENSE
include requirements.txt
recursive-include provider_research *.py
recursive-include config *.yml *.example
```

---

## Conclusion

This folder hierarchy provides:
- ✅ Clear organization following Python best practices
- ✅ Separation of concerns (source/tests/docs/examples)
- ✅ Room for growth and scalability
- ✅ Better developer and user experience
- ✅ Modern Python packaging standards
- ✅ CI/CD integration ready

**Estimated Migration Time**: 2-4 hours  
**Breaking Changes**: Minimal (mostly import paths in examples)  
**Risk Level**: Low (incremental migration possible)
