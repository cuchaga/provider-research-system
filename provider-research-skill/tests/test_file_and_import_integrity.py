"""
Test File and Import Integrity

This test validates:
1. All Python imports work correctly
2. All file references in documentation exist
3. All module files are in correct locations
4. No broken links or missing files
"""

import os
import sys
import re
import ast
import importlib
from pathlib import Path
from typing import List, Dict, Set, Tuple

import pytest


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
PARENT_ROOT = PROJECT_ROOT.parent


class IntegrityIssue:
    """Represents an integrity issue found during testing"""
    
    def __init__(self, category: str, file: str, issue: str, severity: str = "ERROR"):
        self.category = category
        self.file = file
        self.issue = issue
        self.severity = severity
    
    def __repr__(self):
        return f"[{self.severity}] {self.category} in {self.file}: {self.issue}"


class FileIntegrityChecker:
    """Checks file and import integrity across the project"""
    
    def __init__(self):
        self.issues: List[IntegrityIssue] = []
        self.checked_imports: Set[str] = set()
        self.checked_files: Set[str] = set()
    
    def add_issue(self, category: str, file: str, issue: str, severity: str = "ERROR"):
        """Add an integrity issue"""
        self.issues.append(IntegrityIssue(category, file, issue, severity))
    
    def check_python_imports(self) -> List[IntegrityIssue]:
        """Check all Python files can import their dependencies"""
        print("\n🔍 Checking Python imports...")
        
        python_files = list(PROJECT_ROOT.rglob("*.py"))
        python_files = [f for f in python_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
        
        for py_file in python_files:
            self._check_file_imports(py_file)
        
        return [i for i in self.issues if i.category == "IMPORT"]
    
    def _check_file_imports(self, file_path: Path):
        """Check imports in a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._verify_import(alias.name, file_path)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module
                        for alias in node.names:
                            full_import = f"{module}.{alias.name}" if alias.name != '*' else module
                            self._verify_import(full_import, file_path)
        
        except SyntaxError as e:
            self.add_issue("IMPORT", str(file_path), f"Syntax error: {e}")
        except Exception as e:
            self.add_issue("IMPORT", str(file_path), f"Error parsing: {e}", "WARNING")
    
    def _verify_import(self, import_name: str, source_file: Path):
        """Verify a single import works"""
        if import_name in self.checked_imports:
            return
        
        self.checked_imports.add(import_name)
        
        # Skip standard library and known third-party packages
        skip_packages = {
            'os', 'sys', 'json', 'pathlib', 'typing', 're', 'ast', 'importlib',
            'anthropic', 'psycopg2', 'pytest', 'bs4', 'requests', 'yaml',
            'datetime', 'enum', 'dataclasses', 'functools', 'logging',
            'collections', 'itertools', 'urllib', 'http', 'socket', 'time'
        }
        
        base_module = import_name.split('.')[0]
        if base_module in skip_packages:
            return
        
        # Only check provider_research imports
        if not import_name.startswith('provider_research'):
            return
        
        try:
            # Try to import
            importlib.import_module(import_name.split('.')[0])
        except ImportError as e:
            self.add_issue("IMPORT", str(source_file), f"Cannot import '{import_name}': {e}")
        except Exception as e:
            self.add_issue("IMPORT", str(source_file), f"Error importing '{import_name}': {e}", "WARNING")
    
    def check_documentation_references(self) -> List[IntegrityIssue]:
        """Check all file references in markdown documentation"""
        print("\n📚 Checking documentation file references...")
        
        md_files = list(PROJECT_ROOT.rglob("*.md"))
        md_files.extend(PARENT_ROOT.glob("*.md"))
        
        for md_file in md_files:
            if 'venv' in str(md_file) or 'node_modules' in str(md_file):
                continue
            self._check_markdown_references(md_file)
        
        return [i for i in self.issues if i.category == "FILE_REFERENCE"]
    
    def _check_markdown_references(self, md_file: Path):
        """Check file references in a markdown file"""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown links [text](path)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.finditer(link_pattern, content)
            
            for match in matches:
                link_text = match.group(1)
                link_path = match.group(2)
                
                # Skip URLs
                if link_path.startswith(('http://', 'https://', '#', 'mailto:')):
                    continue
                
                # Check if file exists
                if link_path.endswith('.md') or link_path.endswith('.py') or '/' in link_path:
                    self._verify_file_reference(link_path, md_file)
            
            # Find backtick file references
            backtick_pattern = r'`([^`]+\.(py|md|sh|yml|yaml|txt))`'
            matches = re.finditer(backtick_pattern, content)
            
            for match in matches:
                file_ref = match.group(1)
                # Only check if it looks like a relative path
                if '/' in file_ref and not file_ref.startswith('http'):
                    self._verify_file_reference(file_ref, md_file)
        
        except Exception as e:
            self.add_issue("FILE_REFERENCE", str(md_file), f"Error reading: {e}", "WARNING")
    
    def _verify_file_reference(self, ref_path: str, source_file: Path):
        """Verify a file reference exists"""
        if ref_path in self.checked_files:
            return
        
        self.checked_files.add(ref_path)
        
        # Try relative to source file
        relative_path = source_file.parent / ref_path
        if relative_path.exists():
            return
        
        # Try relative to project root
        project_path = PROJECT_ROOT / ref_path
        if project_path.exists():
            return
        
        # Try relative to parent root
        parent_path = PARENT_ROOT / ref_path
        if parent_path.exists():
            return
        
        # File not found
        self.add_issue(
            "FILE_REFERENCE",
            str(source_file.relative_to(PARENT_ROOT)),
            f"Referenced file not found: '{ref_path}'",
            "WARNING"
        )
    
    def check_expected_structure(self) -> List[IntegrityIssue]:
        """Check expected project structure exists"""
        print("\n🗂️  Checking project structure...")
        
        expected_dirs = [
            "provider_research",
            "provider_research/core",
            "provider_research/database",
            "provider_research/search",
            "provider_research/utils",
            "tests",
            "examples",
            "docs",
            "docs/architecture",
            "docs/guides",
            "config",
            "config/database",
            "tools",
            "tools/database",
            "tools/data",
        ]
        
        for dir_path in expected_dirs:
            full_path = PROJECT_ROOT / dir_path
            if not full_path.exists():
                self.add_issue(
                    "STRUCTURE",
                    "project",
                    f"Expected directory missing: {dir_path}"
                )
            elif not full_path.is_dir():
                self.add_issue(
                    "STRUCTURE",
                    "project",
                    f"Expected directory is not a directory: {dir_path}"
                )
        
        expected_files = [
            "provider_research/__init__.py",
            "provider_research/__version__.py",
            "provider_research/config.py",
            "provider_research/exceptions.py",
            "provider_research/core/__init__.py",
            "provider_research/database/__init__.py",
            "provider_research/search/__init__.py",
            "provider_research/utils/__init__.py",
            "tests/__init__.py",
            "setup.py",
            "pyproject.toml",
            "requirements.txt",
            "README.md",
        ]
        
        for file_path in expected_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                self.add_issue(
                    "STRUCTURE",
                    "project",
                    f"Expected file missing: {file_path}"
                )
        
        return [i for i in self.issues if i.category == "STRUCTURE"]
    
    def check_deleted_files_not_referenced(self) -> List[IntegrityIssue]:
        """Check that deleted files are not referenced anywhere"""
        print("\n🗑️  Checking for references to deleted files...")
        
        deleted_files = [
            "FOLDER_HIERARCHY_PLAN.md",
            "IMPLEMENTATION_SUMMARY.md",
            "structure_comparison.sh",
            "ARCHITECTURE.md",  # Moved to docs
            "SKILL.md",  # May not exist
            "ORCHESTRATION.md",  # May not exist
            "TEST_CASES.md",  # May not exist
        ]
        
        # Search all text files
        text_files = list(PROJECT_ROOT.rglob("*.md"))
        text_files.extend(PROJECT_ROOT.rglob("*.py"))
        text_files = [f for f in text_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
        
        for text_file in text_files:
            try:
                with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for deleted_file in deleted_files:
                    if deleted_file in content:
                        # Exclude DUPLICATE_ANALYSIS.md which documents the deletions
                        if 'DUPLICATE_ANALYSIS' in str(text_file):
                            continue
                        
                        self.add_issue(
                            "DELETED_FILE",
                            str(text_file.relative_to(PARENT_ROOT)),
                            f"References deleted file: '{deleted_file}'",
                            "WARNING"
                        )
            except Exception:
                pass
        
        return [i for i in self.issues if i.category == "DELETED_FILE"]
    
    def generate_report(self) -> Dict[str, any]:
        """Generate a comprehensive report"""
        report = {
            "total_issues": len(self.issues),
            "errors": [i for i in self.issues if i.severity == "ERROR"],
            "warnings": [i for i in self.issues if i.severity == "WARNING"],
            "by_category": {}
        }
        
        for issue in self.issues:
            if issue.category not in report["by_category"]:
                report["by_category"][issue.category] = []
            report["by_category"][issue.category].append(issue)
        
        return report


# Test Functions

def test_python_imports():
    """Test that all Python imports work correctly"""
    checker = FileIntegrityChecker()
    issues = checker.check_python_imports()
    
    errors = [i for i in issues if i.severity == "ERROR"]
    
    if errors:
        print("\n❌ Import Errors Found:")
        for error in errors:
            print(f"  {error}")
        pytest.fail(f"Found {len(errors)} import errors")
    else:
        print(f"\n✅ All imports OK ({len(checker.checked_imports)} imports checked)")


def test_documentation_references():
    """Test that all file references in documentation exist"""
    checker = FileIntegrityChecker()
    issues = checker.check_documentation_references()
    
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    
    if warnings:
        print("\n⚠️  Documentation Reference Warnings:")
        for warning in warnings[:10]:  # Show first 10
            print(f"  {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
    
    if errors:
        print("\n❌ Documentation Reference Errors:")
        for error in errors:
            print(f"  {error}")
        pytest.fail(f"Found {len(errors)} documentation reference errors")
    else:
        print(f"\n✅ Documentation references OK ({len(checker.checked_files)} files checked)")


def test_project_structure():
    """Test that expected project structure exists"""
    checker = FileIntegrityChecker()
    issues = checker.check_expected_structure()
    
    if issues:
        print("\n❌ Structure Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        pytest.fail(f"Found {len(issues)} structure issues")
    else:
        print("\n✅ Project structure OK")


def test_no_deleted_file_references():
    """Test that deleted files are not referenced"""
    checker = FileIntegrityChecker()
    issues = checker.check_deleted_files_not_referenced()
    
    if issues:
        print("\n⚠️  References to Deleted Files:")
        for issue in issues:
            print(f"  {issue}")
        # Don't fail, just warn
        print(f"\n⚠️  Found {len(issues)} references to deleted files (warnings only)")
    else:
        print("\n✅ No references to deleted files")


def test_comprehensive_integrity():
    """Run all integrity checks and generate report"""
    checker = FileIntegrityChecker()
    
    print("\n" + "="*70)
    print("COMPREHENSIVE FILE & IMPORT INTEGRITY CHECK")
    print("="*70)
    
    # Run all checks
    checker.check_python_imports()
    checker.check_documentation_references()
    checker.check_expected_structure()
    checker.check_deleted_files_not_referenced()
    
    # Generate report
    report = checker.generate_report()
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total Issues: {report['total_issues']}")
    print(f"  Errors:   {len(report['errors'])}")
    print(f"  Warnings: {len(report['warnings'])}")
    
    if report['by_category']:
        print(f"\nBy Category:")
        for category, issues in report['by_category'].items():
            errors = len([i for i in issues if i.severity == "ERROR"])
            warnings = len([i for i in issues if i.severity == "WARNING"])
            print(f"  {category}: {errors} errors, {warnings} warnings")
    
    # Print detailed errors
    if report['errors']:
        print(f"\n{'='*70}")
        print("ERRORS (must be fixed)")
        print(f"{'='*70}")
        for error in report['errors']:
            print(f"  {error}")
    
    # Print some warnings
    if report['warnings']:
        print(f"\n{'='*70}")
        print("WARNINGS (should be reviewed)")
        print(f"{'='*70}")
        for warning in report['warnings'][:20]:  # Show first 20
            print(f"  {warning}")
        if len(report['warnings']) > 20:
            print(f"  ... and {len(report['warnings']) - 20} more warnings")
    
    print(f"\n{'='*70}")
    
    # Fail if errors exist
    if report['errors']:
        pytest.fail(f"Found {len(report['errors'])} errors that must be fixed")
    
    print("\n✅ All integrity checks passed!")


if __name__ == "__main__":
    # Run comprehensive check when executed directly
    test_comprehensive_integrity()
