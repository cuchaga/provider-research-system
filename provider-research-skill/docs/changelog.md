# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-09

### Added
- **Multi-skill architecture** with centralized orchestrator
- **ProviderOrchestrator** - Main coordinator for all skills
- **ProviderQueryInterpreter** - Natural language understanding skill
- **ProviderDatabaseManager** - Fast database operations skill
- **ProviderSemanticMatcher** - Intelligent matching skill
- **ProviderWebResearcher** - Web research and data extraction skill
- **ExecutionPath** enum for tracking workflow paths
- **Configuration management** system with YAML support
- **Utilities module** with validators, formatters, and logging
- **Custom exceptions** for better error handling
- **Comprehensive documentation** structure
- **Example code** and Jupyter notebooks
- **Test infrastructure** with pytest
- **Configuration templates** for easy setup

### Changed
- **Reorganized package structure** following Python best practices
- **Moved documentation** to dedicated docs/ directory
- **Reorganized tools** into database/ and data/ subdirectories
- **Updated imports** to use new package structure
- **Improved test organization** with unit/integration separation

### Fixed
- **Import references** across all modules
- **PostgreSQL import** made optional to prevent import errors
- **Package metadata** now in dedicated __version__.py

### Deprecated
- Legacy single-class architecture (v1.0) - Still supported for backwards compatibility

## [1.0.0] - 2025-XX-XX

### Added
- Initial release
- Basic provider research functionality
- PostgreSQL and SQLite support
- Web scraping capabilities
- NPI registry integration

[2.0.0]: https://github.com/cuchaga/provider-research-system/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/cuchaga/provider-research-system/releases/tag/v1.0.0
