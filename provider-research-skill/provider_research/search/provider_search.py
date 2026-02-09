"""
Provider Database Search with Fuzzy Matching
Automatically falls back to fuzzy matching when exact matches aren't found
"""

import sqlite3
import json
from difflib import SequenceMatcher

DB_PATH = '/home/claude/providers_test.db'

def fuzzy_similarity(a, b):
    """Calculate similarity ratio between two strings using Levenshtein distance"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_providers(query, state=None, fuzzy_threshold=0.4, limit=10, verbose=True):
    """
    Search providers with automatic fuzzy matching fallback
    
    Args:
        query (str): Search term (provider name, keyword)
        state (str): Optional state filter (e.g., 'MA', 'CA')
        fuzzy_threshold (float): Minimum similarity score for fuzzy matches (0.0-1.0)
                                 Default: 0.4 (40% similarity)
        limit (int): Maximum number of results to return
        verbose (bool): Print informational messages
    
    Returns:
        List of tuples: (match_type, score, provider_data)
        - match_type: 'exact' or 'fuzzy'
        - score: 1.0 for exact, 0.0-1.0 for fuzzy
        - provider_data: tuple of all provider fields
    
    Examples:
        # Exact match
        results = search_providers("Home Instead", state="MA")
        
        # Handles typos automatically
        results = search_providers("Homestead", state="MA")  # Finds "Home Instead"
        
        # Multiple typos
        results = search_providers("Hme Insted", state="MA")
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Step 1: Try exact/partial SQL match first (fast)
    sql = """
        SELECT legal_name, address_full, address_city, address_state, 
               phone, provider_type, parent_organization, raw_search_data
        FROM providers 
        WHERE (legal_name LIKE ? 
               OR parent_organization LIKE ? 
               OR dba_names LIKE ?)
    """
    
    params = [f'%{query}%', f'%{query}%', f'%{query}%']
    
    if state:
        sql += " AND address_state = ?"
        params.append(state)
    
    cursor.execute(sql, params)
    exact_matches = cursor.fetchall()
    
    # If exact matches found, return them immediately
    if exact_matches:
        results = [('exact', 1.0, row) for row in exact_matches]
        conn.close()
        return results[:limit]
    
    # Step 2: No exact matches - try fuzzy matching (slower but thorough)
    if verbose:
        print(f"⚠️  No exact matches for '{query}'. Trying fuzzy matching (threshold: {fuzzy_threshold*100:.0f}%)...\n")
    
    sql_all = """
        SELECT legal_name, address_full, address_city, address_state, 
               phone, provider_type, parent_organization, raw_search_data
        FROM providers
    """
    
    if state:
        sql_all += " WHERE address_state = ?"
        cursor.execute(sql_all, [state])
    else:
        cursor.execute(sql_all)
    
    all_providers = cursor.fetchall()
    
    # Calculate fuzzy similarity scores
    fuzzy_matches = []
    for provider in all_providers:
        legal_name = provider[0]
        score = fuzzy_similarity(query, legal_name)
        
        if score >= fuzzy_threshold:
            fuzzy_matches.append(('fuzzy', score, provider))
    
    # Sort by score (highest first)
    fuzzy_matches.sort(reverse=True, key=lambda x: x[1])
    
    conn.close()
    return fuzzy_matches[:limit]


def display_results(results, show_full_details=False):
    """
    Display search results in a formatted table
    
    Args:
        results: Output from search_providers()
        show_full_details: If True, show all provider information
    """
    if not results:
        print("❌ No results found")
        return
    
    print(f"Found {len(results)} result(s)\n")
    print("=" * 100)
    
    for match_type, score, row in results:
        legal_name, address, city, state, phone, ptype, parent, raw = row
        score_display = f"{score*100:.1f}%"
        
        print(f"[{match_type.upper()}] {score_display} - {legal_name}")
        print(f"  Location: {city}, {state}")
        print(f"  Phone: {phone}")
        
        if show_full_details:
            print(f"  Address: {address}")
            print(f"  Type: {ptype}")
            if parent:
                print(f"  Parent Org: {parent}")
            
            # Parse and show owner info if available
            if raw:
                try:
                    data = json.loads(raw)
                    owner = data.get('franchise_owner') or data.get('franchise_owners')
                    if owner and 'Unknown' not in owner:
                        print(f"  Owner: {owner}")
                except:
                    pass
        
        print("-" * 100)


def quick_search(query, state="MA"):
    """
    Quick search with default settings and formatted output
    
    Args:
        query: Provider name to search
        state: State abbreviation (default: MA)
    
    Example:
        quick_search("homestead")
    """
    print(f"Searching for: '{query}' in {state}")
    print("=" * 100)
    
    results = search_providers(query, state=state, fuzzy_threshold=0.4, limit=10)
    display_results(results, show_full_details=True)
    
    return results


if __name__ == "__main__":
    # Example usage
    print("PROVIDER SEARCH MODULE - EXAMPLES\n")
    
    # Example 1: Exact match
    print("\n1. Exact Match:")
    quick_search("Home Instead", state="MA")
    
    # Example 2: Typo - fuzzy match
    print("\n2. Typo Correction:")
    quick_search("Homestead", state="MA")
