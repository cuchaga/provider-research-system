"""
Provider Database - SQLite Implementation
Lightweight version with fuzzy matching capabilities
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher


class ProviderDatabaseSQLite:
    """
    SQLite-based provider database with fuzzy matching.
    Supports typo tolerance and DBA/legal name interchangeability.
    """
    
    def __init__(self, db_path: str = "/home/claude/providers.db"):
        """Initialize SQLite database"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._setup_database()
    
    def _setup_database(self):
        """Create tables and indexes"""
        cur = self.conn.cursor()
        
        # Main providers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id TEXT PRIMARY KEY,
                npi TEXT UNIQUE,
                legal_name TEXT NOT NULL,
                dba_names TEXT,  -- JSON array
                name_variations TEXT,  -- JSON array for searching
                
                -- Location
                address_full TEXT,
                address_street TEXT,
                address_city TEXT,
                address_state TEXT,
                address_zip TEXT,
                
                -- URLs
                location_website TEXT,
                parent_website TEXT,
                alternative_urls TEXT,  -- JSON array
                
                -- Organization
                parent_organization TEXT,
                franchise_status INTEGER,  -- 0 or 1
                provider_type TEXT,
                
                -- NPI data
                npi_taxonomy_code TEXT,
                npi_taxonomy_desc TEXT,
                npi_status TEXT,
                npi_enumeration_date TEXT,
                
                -- Contact
                phone TEXT,
                fax TEXT,
                email TEXT,
                
                -- Metadata
                confidence_score REAL,
                created_at TEXT,
                validated_at TEXT,
                last_updated TEXT,
                
                -- Complete data
                raw_search_data TEXT,  -- JSON
                raw_npi_data TEXT  -- JSON
            )
        """)
        
        # Search history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id TEXT PRIMARY KEY,
                provider_id TEXT,
                search_query TEXT,
                search_location TEXT,
                match_found INTEGER,
                match_score REAL,
                match_method TEXT,
                search_timestamp TEXT,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            )
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_npi ON providers(npi)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_legal_name ON providers(legal_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_city_state ON providers(address_city, address_state)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_state ON providers(address_state)")
        
        self.conn.commit()
    
    def add_provider(self, search_result: Dict) -> str:
        """Add provider from search results"""
        import uuid
        
        provider_id = str(uuid.uuid4())
        
        # Extract data
        npi_data = search_result.get('npi_data', {})
        npi_results = npi_data.get('results', [])
        npi_record = npi_results[0] if npi_results else {}
        
        # Prepare names
        legal_name = npi_record.get('name', '')
        if not legal_name:
            # Extract from website
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
                parent_organization, franchise_status,
                npi_taxonomy_code, npi_taxonomy_desc, npi_status,
                phone, confidence_score, created_at, validated_at,
                raw_search_data, raw_npi_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1 if self._detect_franchise(search_result) else 0,
            npi_record.get('taxonomy'),
            npi_record.get('taxonomy'),
            npi_record.get('status'),
            self._extract_phone(npi_record),
            search_result.get('confidence_score'),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            json.dumps(search_result),
            json.dumps(npi_data)
        ))
        
        self.conn.commit()
        return provider_id
    
    def find_provider(
        self,
        name: str,
        location: Optional[str] = None,
        npi: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find provider with multi-level fuzzy matching.
        """
        city, state = self._parse_location(location) if location else (None, None)
        
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
        
        # Level 3: Fuzzy name matching
        result = self._search_fuzzy_name(name, city, state, threshold=0.6)
        if result:
            self._log_search(name, location, True, result['match_score'], 'fuzzy_name', result['id'])
            return result
        
        # Not found
        self._log_search(name, location, False, 0.0, 'not_found', None)
        return None
    
    def _search_by_npi(self, npi: str) -> Optional[Dict]:
        """Exact NPI lookup"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM providers WHERE npi = ?", [npi])
        row = cur.fetchone()
        return dict(row) if row else None
    
    def _search_exact_name(self, name: str, city: Optional[str], state: Optional[str]) -> Optional[Dict]:
        """Exact name match (case-insensitive)"""
        cur = self.conn.cursor()
        
        # Search in legal name, dba_names, and name_variations
        query = """
            SELECT * FROM providers
            WHERE (
                LOWER(legal_name) = LOWER(?)
                OR LOWER(dba_names) LIKE LOWER(?)
                OR LOWER(name_variations) LIKE LOWER(?)
            )
        """
        params = [name, f'%"{name}"%', f'%"{name.lower()}"%']
        
        if city and state:
            query += " AND LOWER(address_city) = LOWER(?) AND UPPER(address_state) = UPPER(?)"
            params.extend([city, state])
        elif state:
            query += " AND UPPER(address_state) = UPPER(?)"
            params.append(state)
        
        query += " LIMIT 1"
        
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
    
    def _search_fuzzy_name(
        self,
        name: str,
        city: Optional[str],
        state: Optional[str],
        threshold: float = 0.6
    ) -> Optional[Dict]:
        """Fuzzy text matching using SequenceMatcher"""
        cur = self.conn.cursor()
        
        # Get all providers (optionally filtered by state)
        query = "SELECT * FROM providers"
        params = []
        
        if state:
            query += " WHERE UPPER(address_state) = UPPER(?)"
            params.append(state)
        
        cur.execute(query, params)
        
        best_match = None
        best_score = 0.0
        
        name_lower = name.lower()
        
        for row in cur.fetchall():
            provider = dict(row)
            
            # Calculate similarity with legal name
            legal_score = self._similarity(name_lower, provider['legal_name'].lower())
            
            # Calculate similarity with DBAs
            dba_score = 0.0
            if provider['dba_names']:
                dba_list = json.loads(provider['dba_names'])
                dba_score = max([self._similarity(name_lower, dba.lower()) for dba in dba_list], default=0.0)
            
            # Calculate similarity with name variations
            var_score = 0.0
            if provider['name_variations']:
                var_list = json.loads(provider['name_variations'])
                var_score = max([self._similarity(name_lower, var) for var in var_list], default=0.0)
            
            # Take best score
            score = max(legal_score, dba_score, var_score)
            
            # Apply city matching bonus if provided
            if city and provider['address_city']:
                city_sim = self._similarity(city.lower(), provider['address_city'].lower())
                if city_sim > 0.5:
                    score = (score * 0.7) + (city_sim * 0.3)  # Weight name more
            
            if score > best_score:
                best_score = score
                best_match = provider
        
        if best_match and best_score >= threshold:
            best_match['match_score'] = best_score
            return best_match
        
        return None
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate string similarity (0.0 to 1.0)"""
        return SequenceMatcher(None, a, b).ratio()
    
    def _log_search(self, query: str, location: Optional[str], found: bool, 
                   score: float, method: str, provider_id: Optional[str]):
        """Log search to history"""
        import uuid
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO search_history (
                id, provider_id, search_query, search_location,
                match_found, match_score, match_method, search_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            provider_id,
            query,
            location,
            1 if found else 0,
            score,
            method,
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
    
    def _parse_location(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse location into city and state"""
        if not location:
            return None, None
        
        # Remove address numbers
        cleaned = re.sub(r'\d+\s+[A-Za-z\s]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Ct|Court|Pl|Place|Crossing|Xing)[,\s]*', 
                        '', location, flags=re.IGNORECASE)
        
        parts = [p.strip() for p in cleaned.split(',')]
        
        if len(parts) >= 2:
            city = parts[-2]
            state_part = parts[-1].split()[0]
            if len(state_part) == 2:
                return city, state_part.upper()
        
        words = cleaned.split()
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
        
        # Add lowercase legal name
        variations.add(legal_name.lower())
        
        # Add DBAs
        for dba in dba_names:
            variations.add(dba.lower())
        
        # Add without common suffixes
        for name in [legal_name] + dba_names:
            cleaned = re.sub(r'\s+(Inc\.?|LLC|Corp\.?|Corporation|Company|Co\.?)$', '', name, flags=re.IGNORECASE)
            variations.add(cleaned.lower())
        
        return list(variations)
    
    def _extract_parent_org(self, search_result: Dict) -> Optional[str]:
        """Extract parent organization"""
        parent_url = search_result.get('parent_organization_website')
        if parent_url:
            from urllib.parse import urlparse
            domain = urlparse(parent_url).netloc.replace('www.', '')
            return domain.split('.')[0].replace('-', ' ').title()
        return None
    
    def _detect_franchise(self, search_result: Dict) -> bool:
        """Detect if franchise"""
        location_url = search_result.get('location_website', '')
        parent_url = search_result.get('parent_organization_website', '')
        return location_url != parent_url if (location_url and parent_url) else False
    
    def _extract_phone(self, npi_record: Dict) -> Optional[str]:
        """Extract phone from NPI record"""
        address = npi_record.get('address', '')
        phone_match = re.search(r'\d{3}-\d{3}-\d{4}', address)
        return phone_match.group() if phone_match else None
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_providers,
                COUNT(DISTINCT address_state) as states_covered,
                COUNT(CASE WHEN npi IS NOT NULL THEN 1 END) as with_npi,
                AVG(confidence_score) as avg_confidence
            FROM providers
        """)
        
        row = cur.fetchone()
        return dict(row) if row else {}
    
    def list_all_providers(self) -> List[Dict]:
        """List all providers"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM providers ORDER BY legal_name")
        return [dict(row) for row in cur.fetchall()]
    
    def close(self):
        """Close database"""
        self.conn.close()


if __name__ == "__main__":
    # Test the database
    db = ProviderDatabaseSQLite()
    print("✓ Database initialized")
    
    stats = db.get_stats()
    print(f"✓ Stats: {stats}")
