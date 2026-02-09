"""
Provider Database - PostgreSQL Implementation
Full-featured version with fuzzy matching, full-text search, and analytics
"""

import json
import re
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Installing psycopg2...")
    import subprocess
    subprocess.run(["pip", "install", "psycopg2-binary", "--break-system-packages"], check=True)
    import psycopg2
    from psycopg2.extras import RealDictCursor


class ProviderDatabasePostgres:
    """
    PostgreSQL-based provider database with fuzzy matching.
    Supports typo tolerance, full-text search, and DBA/legal name interchangeability.
    """
    
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'providers',
        'user': 'provider_admin',
        'password': 'provider123'
    }
    
    def __init__(self, config: Dict = None):
        """Initialize PostgreSQL database connection"""
        self.config = config or self.DEFAULT_CONFIG
        self.conn = psycopg2.connect(**self.config)
        self.conn.autocommit = True
    
    def add_provider(self, search_result: Dict) -> str:
        """Add provider from search results"""
        provider_id = str(uuid.uuid4())
        
        # Extract data
        npi_data = search_result.get('npi_data', {})
        npi_results = npi_data.get('results', [])
        npi_record = npi_results[0] if npi_results else {}
        
        # Prepare names
        legal_name = npi_record.get('name', '')
        if not legal_name:
            location_url = search_result.get('location_website', '')
            legal_name = location_url.split('/')[-2] if location_url else 'Unknown'
        
        dba_names = search_result.get('dba_names', [])
        
        # Parse address
        address_parts = self._parse_address(npi_record.get('address', ''))
        
        # Create name variations for fuzzy search
        name_variations = self._generate_name_variations(legal_name, dba_names)
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO providers (
                id, npi, legal_name, dba_names, name_variations,
                address_full, address_street, address_city, address_state, address_zip,
                location_website, parent_website, alternative_urls,
                parent_organization, franchise_status, franchise_id,
                npi_taxonomy_code, npi_taxonomy_desc, npi_status,
                phone, confidence_score, created_at, validated_at,
                raw_search_data, raw_npi_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (npi) DO UPDATE SET
                legal_name = EXCLUDED.legal_name,
                address_full = EXCLUDED.address_full,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            provider_id,
            npi_record.get('npi'),
            legal_name,
            json.dumps(dba_names),
            json.dumps(name_variations),
            npi_record.get('address'),
            address_parts['street'],
            address_parts['city'],
            address_parts['state'],
            address_parts['zip'],
            search_result.get('location_website'),
            search_result.get('parent_organization_website'),
            json.dumps(search_result.get('alternative_urls', [])),
            self._extract_parent_org(search_result),
            self._detect_franchise(search_result),
            search_result.get('franchise_id'),
            npi_record.get('taxonomy'),
            npi_record.get('taxonomy'),
            npi_record.get('status'),
            self._extract_phone(npi_record),
            search_result.get('confidence_score'),
            datetime.utcnow(),
            datetime.utcnow(),
            json.dumps(search_result),
            json.dumps(npi_data)
        ))
        
        result = cur.fetchone()
        return result[0] if result else provider_id
    
    def add_provider_simple(self, 
                           legal_name: str,
                           city: str,
                           state: str,
                           phone: str = None,
                           address: str = None,
                           npi: str = None,
                           franchise_id: str = None,
                           parent_organization: str = None,
                           website: str = None,
                           **kwargs) -> str:
        """
        Simplified method to add a provider with basic fields.
        Use this for quick insertions during web research.
        """
        provider_id = str(uuid.uuid4())
        name_variations = self._generate_name_variations(legal_name, [])
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO providers (
                id, npi, legal_name, name_variations,
                address_full, address_city, address_state,
                phone, franchise_id, parent_organization,
                location_website, created_at, validated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            provider_id, npi, legal_name, json.dumps(name_variations),
            address, city, state, phone, franchise_id, parent_organization,
            website, datetime.utcnow(), datetime.utcnow()
        ))
        
        result = cur.fetchone()
        return result[0] if result else provider_id
    
    def find_provider(
        self,
        name: str,
        location: Optional[str] = None,
        npi: Optional[str] = None,
        state: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find provider with multi-level fuzzy matching.
        """
        city, parsed_state = self._parse_location(location) if location else (None, None)
        state = state or parsed_state
        
        # Level 1: Exact NPI
        if npi:
            result = self._search_by_npi(npi)
            if result:
                self._log_search(name, location, True, 1.0, 'exact_npi', result['id'])
                return result
        
        # Level 2: Exact name + location
        result = self._search_exact_name(name, city, state)
        if result:
            self._log_search(name, location, True, 1.0, 'exact_name', result['id'])
            return result
        
        # Level 3: Full-text search
        result = self._search_fulltext(name, city, state)
        if result:
            self._log_search(name, location, True, 0.9, 'fulltext', result['id'])
            return result
        
        # Level 4: Fuzzy name matching
        result = self._search_fuzzy_name(name, city, state, threshold=0.5)
        if result:
            self._log_search(name, location, True, result['match_score'], 'fuzzy_name', result['id'])
            return result
        
        # Not found
        self._log_search(name, location, False, 0.0, 'not_found', None)
        return None
    
    def search_providers(self, query: str, state: str = None, 
                        fuzzy_threshold: float = 0.4, limit: int = 10) -> List[Tuple]:
        """
        Search providers with automatic fuzzy matching fallback.
        Compatible with SQLite version interface.
        
        Returns:
            List of tuples: (match_type, score, provider_data)
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Try exact/partial SQL match first
        sql = """
            SELECT legal_name, address_full, address_city, address_state,
                   phone, provider_type, parent_organization, raw_search_data
            FROM providers
            WHERE (legal_name ILIKE %s OR parent_organization ILIKE %s)
        """
        params = [f'%{query}%', f'%{query}%']
        
        if state:
            sql += " AND address_state = %s"
            params.append(state.upper())
        
        sql += f" LIMIT {limit}"
        
        cur.execute(sql, params)
        exact_matches = cur.fetchall()
        
        if exact_matches:
            return [('exact', 1.0, tuple(row.values())) for row in exact_matches]
        
        # Try full-text search
        sql_fts = """
            SELECT legal_name, address_full, address_city, address_state,
                   phone, provider_type, parent_organization, raw_search_data,
                   ts_rank(to_tsvector('english', legal_name), plainto_tsquery('english', %s)) as rank
            FROM providers
            WHERE to_tsvector('english', legal_name) @@ plainto_tsquery('english', %s)
        """
        params_fts = [query, query]
        
        if state:
            sql_fts += " AND address_state = %s"
            params_fts.append(state.upper())
        
        sql_fts += f" ORDER BY rank DESC LIMIT {limit}"
        
        cur.execute(sql_fts, params_fts)
        fts_matches = cur.fetchall()
        
        if fts_matches:
            return [('fulltext', float(row['rank']), tuple(list(row.values())[:-1])) 
                    for row in fts_matches]
        
        # Fall back to fuzzy matching
        sql_all = "SELECT * FROM providers"
        if state:
            sql_all += " WHERE address_state = %s"
            cur.execute(sql_all, [state.upper()])
        else:
            cur.execute(sql_all)
        
        all_providers = cur.fetchall()
        
        fuzzy_matches = []
        query_lower = query.lower()
        
        for provider in all_providers:
            legal_name = provider['legal_name'] or ''
            score = SequenceMatcher(None, query_lower, legal_name.lower()).ratio()
            
            if score >= fuzzy_threshold:
                row_tuple = (
                    provider['legal_name'],
                    provider['address_full'],
                    provider['address_city'],
                    provider['address_state'],
                    provider['phone'],
                    provider['provider_type'],
                    provider['parent_organization'],
                    provider['raw_search_data']
                )
                fuzzy_matches.append(('fuzzy', score, row_tuple))
        
        fuzzy_matches.sort(reverse=True, key=lambda x: x[1])
        return fuzzy_matches[:limit]
    
    def _search_by_npi(self, npi: str) -> Optional[Dict]:
        """Exact NPI lookup"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM providers WHERE npi = %s", [npi])
        row = cur.fetchone()
        return dict(row) if row else None
    
    def _search_exact_name(self, name: str, city: Optional[str], state: Optional[str]) -> Optional[Dict]:
        """Exact name match (case-insensitive)"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT * FROM providers
            WHERE LOWER(legal_name) = LOWER(%s)
        """
        params = [name]
        
        if city and state:
            sql += " AND LOWER(address_city) = LOWER(%s) AND UPPER(address_state) = UPPER(%s)"
            params.extend([city, state])
        elif state:
            sql += " AND UPPER(address_state) = UPPER(%s)"
            params.append(state)
        
        sql += " LIMIT 1"
        
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    
    def _search_fulltext(self, name: str, city: Optional[str], state: Optional[str]) -> Optional[Dict]:
        """PostgreSQL full-text search"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT *, ts_rank(to_tsvector('english', legal_name), 
                             plainto_tsquery('english', %s)) as rank
            FROM providers
            WHERE to_tsvector('english', legal_name) @@ plainto_tsquery('english', %s)
        """
        params = [name, name]
        
        if state:
            sql += " AND UPPER(address_state) = UPPER(%s)"
            params.append(state)
        
        sql += " ORDER BY rank DESC LIMIT 1"
        
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    
    def _search_fuzzy_name(
        self,
        name: str,
        city: Optional[str],
        state: Optional[str],
        threshold: float = 0.5
    ) -> Optional[Dict]:
        """Fuzzy text matching using SequenceMatcher"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = "SELECT * FROM providers"
        params = []
        
        if state:
            sql += " WHERE UPPER(address_state) = UPPER(%s)"
            params.append(state)
        
        cur.execute(sql, params)
        
        best_match = None
        best_score = 0.0
        name_lower = name.lower()
        
        for row in cur.fetchall():
            provider = dict(row)
            legal_name = provider.get('legal_name', '') or ''
            
            # Calculate similarity
            score = SequenceMatcher(None, name_lower, legal_name.lower()).ratio()
            
            # Check DBA names
            dba_names = provider.get('dba_names')
            if dba_names:
                if isinstance(dba_names, str):
                    dba_names = json.loads(dba_names)
                for dba in dba_names:
                    dba_score = SequenceMatcher(None, name_lower, dba.lower()).ratio()
                    score = max(score, dba_score)
            
            if score > best_score:
                best_score = score
                best_match = provider
        
        if best_match and best_score >= threshold:
            best_match['match_score'] = best_score
            return best_match
        
        return None
    
    def _log_search(self, query: str, location: Optional[str], found: bool,
                   score: float, method: str, provider_id: Optional[str]):
        """Log search to history"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO search_history (
                provider_id, search_query, search_location,
                match_found, match_score, match_method
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (provider_id, query, location, found, score, method))
    
    def start_research_session(self, provider_name: str, state: str, city: str = None) -> str:
        """Start a new research session for tracking"""
        session_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO research_sessions (id, provider_name, state, city)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (session_id, provider_name, state, city))
        return session_id
    
    def update_research_session(self, session_id: str, **kwargs):
        """Update research session with progress"""
        valid_fields = ['claimed_count', 'extracted_count', 'unique_count', 
                       'duplicates_removed', 'token_cost', 'status', 'notes']
        
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in valid_fields:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if kwargs.get('status') == 'completed':
            updates.append("completed_at = CURRENT_TIMESTAMP")
        
        if updates:
            values.append(session_id)
            cur = self.conn.cursor()
            cur.execute(f"""
                UPDATE research_sessions 
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                COUNT(*) as total_providers,
                COUNT(DISTINCT address_state) as states_covered,
                COUNT(CASE WHEN npi IS NOT NULL THEN 1 END) as with_npi,
                ROUND(AVG(confidence_score)::numeric, 2) as avg_confidence
            FROM providers
        """)
        return dict(cur.fetchone())
    
    def list_providers_by_state(self, state: str) -> List[Dict]:
        """List all providers in a state"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, legal_name, address_city, phone, parent_organization
            FROM providers 
            WHERE address_state = %s
            ORDER BY legal_name
        """, [state.upper()])
        return [dict(row) for row in cur.fetchall()]
    
    def list_all_providers(self) -> List[Dict]:
        """List all providers"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM providers ORDER BY legal_name")
        return [dict(row) for row in cur.fetchall()]
    
    def check_duplicate(self, phone: str = None, address: str = None) -> Optional[Dict]:
        """Check if provider already exists by phone OR address"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        if phone:
            # Normalize phone to digits only
            phone_digits = re.sub(r'\D', '', phone)
            cur.execute("""
                SELECT * FROM providers 
                WHERE REGEXP_REPLACE(phone, '[^0-9]', '', 'g') = %s
                LIMIT 1
            """, [phone_digits])
            row = cur.fetchone()
            if row:
                return dict(row)
        
        if address:
            # Normalize address for comparison
            addr_normalized = address.lower().replace('.', '').replace(',', '')
            cur.execute("""
                SELECT * FROM providers 
                WHERE LOWER(REPLACE(REPLACE(address_full, '.', ''), ',', '')) LIKE %s
                LIMIT 1
            """, [f'%{addr_normalized}%'])
            row = cur.fetchone()
            if row:
                return dict(row)
        
        return None
    
    def _parse_location(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse location into city and state"""
        if not location:
            return None, None
        
        parts = [p.strip() for p in location.split(',')]
        
        if len(parts) >= 2:
            city = parts[-2]
            state_part = parts[-1].split()[0]
            if len(state_part) == 2:
                return city, state_part.upper()
        
        words = location.split()
        if len(words) >= 2 and len(words[-1]) == 2:
            return ' '.join(words[:-1]), words[-1].upper()
        
        return None, None
    
    def _parse_address(self, address: str) -> Dict[str, Optional[str]]:
        """Parse full address"""
        if not address:
            return {'street': None, 'city': None, 'state': None, 'zip': None}
        
        parts = [p.strip() for p in address.split(',')]
        result = {
            'street': parts[0] if len(parts) > 0 else None,
            'city': parts[1] if len(parts) > 1 else None,
            'state': None,
            'zip': None
        }
        
        if len(parts) > 2:
            last_part = parts[-1].strip()
            tokens = last_part.split()
            if len(tokens) >= 2:
                result['state'] = tokens[0].upper()
                result['zip'] = tokens[1]
        
        return result
    
    def _generate_name_variations(self, legal_name: str, dba_names: List[str]) -> List[str]:
        """Generate name variations for fuzzy searching"""
        variations = set()
        
        variations.add(legal_name.lower())
        
        for dba in dba_names:
            variations.add(dba.lower())
        
        # Remove common suffixes
        for name in [legal_name] + dba_names:
            cleaned = re.sub(r'\s+(Inc\.?|LLC|Corp\.?|Corporation|Company|Co\.?)$', 
                           '', name, flags=re.IGNORECASE)
            variations.add(cleaned.lower())
        
        return list(variations)
    
    def _extract_parent_org(self, search_result: Dict) -> Optional[str]:
        """Extract parent organization"""
        parent_url = search_result.get('parent_organization_website')
        if parent_url:
            from urllib.parse import urlparse
            domain = urlparse(parent_url).netloc.replace('www.', '')
            return domain.split('.')[0].replace('-', ' ').title()
        return search_result.get('parent_organization')
    
    def _detect_franchise(self, search_result: Dict) -> bool:
        """Detect if franchise"""
        location_url = search_result.get('location_website', '')
        parent_url = search_result.get('parent_organization_website', '')
        return location_url != parent_url if (location_url and parent_url) else False
    
    def _extract_phone(self, npi_record: Dict) -> Optional[str]:
        """Extract phone from NPI record"""
        if npi_record.get('phone'):
            return npi_record['phone']
        address = npi_record.get('address', '')
        phone_match = re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', address)
        return phone_match.group() if phone_match else None
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def display_results(results, show_full_details=False):
    """Display search results in a formatted table"""
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
            if ptype:
                print(f"  Type: {ptype}")
            if parent:
                print(f"  Parent Org: {parent}")
        
        print("-" * 100)


if __name__ == "__main__":
    print("PROVIDER DATABASE - PostgreSQL")
    print("=" * 50)
    
    try:
        db = ProviderDatabasePostgres()
        print("✅ Connected to PostgreSQL database")
        
        stats = db.get_stats()
        print(f"\nDatabase Statistics:")
        print(f"  • Total providers: {stats['total_providers']}")
        print(f"  • States covered: {stats['states_covered']}")
        print(f"  • With NPI: {stats['with_npi']}")
        print(f"  • Avg confidence: {stats['avg_confidence']}")
        
        db.close()
        print("\n✅ Database ready for use")
        
    except Exception as e:
        print(f"❌ Error: {e}")
