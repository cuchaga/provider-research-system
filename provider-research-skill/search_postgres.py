#!/usr/bin/env python3
"""
Search PostgreSQL Database
===========================
Interactive search for providers in PostgreSQL
"""

import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import RealDictCursor


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}


def search_providers(query: str, state: str = None, city: str = None, use_fulltext: bool = False):
    """Search for providers."""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        if use_fulltext:
            # Full-text search
            sql = """
                SELECT 
                    legal_name, dba_names, address_city, address_state, 
                    phone, parent_organization, franchise_id,
                    ts_rank(search_vector, plainto_tsquery('english', %s)) AS rank
                FROM providers
                WHERE search_vector @@ plainto_tsquery('english', %s)
            """
            params = [query, query]
            
            if state:
                sql += " AND address_state = %s"
                params.append(state.upper())
            
            if city:
                sql += " AND address_city ILIKE %s"
                params.append(f"%{city}%")
            
            sql += " ORDER BY rank DESC, legal_name"
            
        else:
            # Simple pattern matching
            sql = """
                SELECT 
                    legal_name, dba_names, address_city, address_state,
                    phone, parent_organization, franchise_id
                FROM providers
                WHERE legal_name ILIKE %s 
                   OR %s = ANY(dba_names)
                   OR parent_organization ILIKE %s
            """
            params = [f"%{query}%", query, f"%{query}%"]
            
            if state:
                sql += " AND address_state = %s"
                params.append(state.upper())
            
            if city:
                sql += " AND address_city ILIKE %s"
                params.append(f"%{city}%")
            
            sql += " ORDER BY legal_name"
        
        cur.execute(sql, params)
        results = cur.fetchall()
        
        conn.close()
        return results
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        print("\n💡 Make sure PostgreSQL is running and data is imported:")
        print("   1. brew services start postgresql@16")
        print("   2. python3 import_to_postgres.py")
        return []


def print_results(results):
    """Pretty print search results."""
    if not results:
        print("❌ No providers found")
        return
    
    print(f"\n✅ Found {len(results)} provider(s):\n")
    print("="*80)
    
    for i, row in enumerate(results, 1):
        print(f"\n{i}. {row['legal_name']}")
        print(f"   📍 Location: {row['address_city']}, {row['address_state']}")
        print(f"   📞 Phone: {row['phone'] or 'N/A'}")
        
        if row.get('dba_names'):
            print(f"   🏷️  DBAs: {', '.join(row['dba_names'])}")
        
        if row.get('parent_organization'):
            print(f"   🏢 Parent: {row['parent_organization']}")
        
        if row.get('franchise_id'):
            print(f"   🆔 Franchise ID: {row['franchise_id']}")
        
        if 'rank' in row:
            print(f"   ⭐ Relevance: {row['rank']:.3f}")
    
    print("\n" + "="*80)


def interactive_search():
    """Interactive search interface."""
    print("="*80)
    print("Provider Search - PostgreSQL")
    print("="*80)
    
    while True:
        print("\n🔍 Search Options:")
        print("   1. Search by name")
        print("   2. Search by name and state")
        print("   3. Search by name and city")
        print("   4. Full-text search (advanced)")
        print("   5. List all providers")
        print("   6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            query = input("Enter provider name: ").strip()
            if query:
                results = search_providers(query)
                print_results(results)
        
        elif choice == '2':
            query = input("Enter provider name: ").strip()
            state = input("Enter state (e.g., MA): ").strip()
            if query:
                results = search_providers(query, state=state)
                print_results(results)
        
        elif choice == '3':
            query = input("Enter provider name: ").strip()
            city = input("Enter city: ").strip()
            if query:
                results = search_providers(query, city=city)
                print_results(results)
        
        elif choice == '4':
            query = input("Enter search terms: ").strip()
            if query:
                results = search_providers(query, use_fulltext=True)
                print_results(results)
        
        elif choice == '5':
            try:
                conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
                cur = conn.cursor()
                cur.execute("""
                    SELECT legal_name, address_city, address_state, phone 
                    FROM providers 
                    ORDER BY legal_name
                """)
                results = cur.fetchall()
                conn.close()
                print_results(results)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")


def quick_search():
    """Quick search from command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python3 search_postgres.py <provider_name>")
        print("       python3 search_postgres.py <provider_name> <state>")
        print("       python3 search_postgres.py interactive")
        sys.exit(1)
    
    if sys.argv[1].lower() == 'interactive':
        interactive_search()
        return
    
    query = sys.argv[1]
    state = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"\n🔍 Searching for: {query}" + (f" in {state}" if state else ""))
    results = search_providers(query, state=state)
    print_results(results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        quick_search()
    else:
        interactive_search()
