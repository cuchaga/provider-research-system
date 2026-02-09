#!/usr/bin/env python3
"""
Database State Export/Import for Provider Research Skill

This script exports the current database state to JSON for portability.
Use this when moving to a new environment or sharing the project state.

Usage:
    Export: python3 db_state.py export
    Import: python3 db_state.py import
"""

import json
import sys
from datetime import datetime, date
from decimal import Decimal

# Add skill path
sys.path.insert(0, '/mnt/skills/user/provider-research')

def json_serializer(obj):
    """Handle non-JSON-serializable types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def export_database():
    """Export database state to JSON file."""
    try:
        from provider_database_postgres import ProviderDatabasePostgres
        db = ProviderDatabasePostgres()
        
        # Get all providers
        providers = db.list_all_providers()
        
        # Get stats
        stats = db.get_stats()
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "stats": stats,
            "providers": providers
        }
        
        with open("db_state.json", "w") as f:
            json.dump(export_data, f, indent=2, default=json_serializer)
        
        db.close()
        
        print(f"✅ Exported {len(providers)} providers to db_state.json")
        print(f"   States covered: {stats.get('states_covered', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False
    
    return True

def import_database():
    """Import database state from JSON file."""
    try:
        from provider_database_postgres import ProviderDatabasePostgres
        
        with open("db_state.json", "r") as f:
            data = json.load(f)
        
        db = ProviderDatabasePostgres()
        
        imported = 0
        for provider in data.get("providers", []):
            try:
                # Extract fields from tuple or dict
                if isinstance(provider, (list, tuple)):
                    # Assume order: name, address, city, state, phone, npi, parent_org, ...
                    db.add_provider_simple(
                        legal_name=provider[0] if len(provider) > 0 else None,
                        address=provider[1] if len(provider) > 1 else None,
                        city=provider[2] if len(provider) > 2 else None,
                        state=provider[3] if len(provider) > 3 else None,
                        phone=provider[4] if len(provider) > 4 else None,
                        npi=provider[5] if len(provider) > 5 else None,
                        parent_organization=provider[6] if len(provider) > 6 else None
                    )
                elif isinstance(provider, dict):
                    db.add_provider_simple(**provider)
                imported += 1
            except Exception as e:
                print(f"  ⚠️ Skipped: {e}")
        
        db.close()
        
        print(f"✅ Imported {imported} providers from db_state.json")
        
    except FileNotFoundError:
        print("❌ db_state.json not found. Run 'export' first.")
        return False
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    return True

def show_state():
    """Display current database state."""
    try:
        from provider_database_postgres import ProviderDatabasePostgres
        db = ProviderDatabasePostgres()
        
        stats = db.get_stats()
        providers = db.list_all_providers()
        
        print("=" * 60)
        print("DATABASE STATE")
        print("=" * 60)
        print(f"Total Providers: {stats.get('total_providers', 0)}")
        print(f"States Covered: {stats.get('states_covered', 0)}")
        print(f"With NPI: {stats.get('with_npi', 0)}")
        print()
        print("PROVIDERS:")
        for p in providers[:20]:  # Show first 20
            if isinstance(p, (list, tuple)):
                print(f"  • {p[0]} ({p[3] if len(p) > 3 else 'N/A'})")
            elif isinstance(p, dict):
                print(f"  • {p.get('legal_name', 'Unknown')} ({p.get('address_state', 'N/A')})")
        
        if len(providers) > 20:
            print(f"  ... and {len(providers) - 20} more")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Failed to read database: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 db_state.py [export|import|show]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "export":
        export_database()
    elif command == "import":
        import_database()
    elif command == "show":
        show_state()
    else:
        print(f"Unknown command: {command}")
        print("Use: export, import, or show")
