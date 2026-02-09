"""
Provider Database Manager Skill
================================
Skill 2: Fast Rule-Based Database Operations

Purpose:
    Fast, token-free database operations using rule-based matching.
    Primary data store for validated provider records.

Capabilities:
    - Exact and fuzzy name matching
    - Full-text search
    - CRUD operations
    - Search history tracking
    - Analytics and stats

Usage:
    from provider_database_manager import ProviderDatabaseManager
    
    db = ProviderDatabaseManager(config)
    results = db.search(query="Home Instead", state="MA")
    provider_id = db.add_provider(provider_data)
"""

import json
import re
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import dataclass

# Lazy import psycopg2 to avoid dependency issues
psycopg2 = None
RealDictCursor = None


@dataclass
class SearchResult:
    """Result from database search"""
    match_type: str  # exact, fuzzy, fulltext
    match_score: float  # 0.0 - 1.0
    provider: Dict
    confidence: float


class ProviderDatabaseManager:
    """
    Skill 2: Database Management
    
    Fast rule-based search and CRUD operations.
    Zero tokens - all operations are deterministic.
    """
    
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'providers',
        'user': 'provider_admin',
        'password': 'provider123'
    }
    
    # Fuzzy matching thresholds
    EXACT_THRESHOLD = 1.0
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    LOW_CONFIDENCE_THRESHOLD = 0.50
    
    def __init__(self, config: Dict = None, auto_connect: bool = True):
        """
        Initialize database manager.
        
        Args:
            config: Database connection config
            auto_connect: Whether to connect immediately
        """
        self.config = config or self.DEFAULT_CONFIG
        self.conn = None
        if auto_connect:
            self.connect()
    
    def connect(self):
        """Establish database connection."""
        global psycopg2, RealDictCursor
        
        # Lazy import psycopg2
        if psycopg2 is None:
            try:
                import psycopg2 as pg
                from psycopg2.extras import RealDictCursor as RDC
                globals()['psycopg2'] = pg
                globals()['RealDictCursor'] = RDC
            except ImportError:
                raise ImportError(
                    "psycopg2 is required for database operations. "
                    "Install with: pip install psycopg2-binary"
                )
        
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = True
    
    def search(
        self,
        query: str = None,
        state: str = None,
        city: str = None,
        npi: str = None,
        phone: str = None,
        parent_organization: str = None,
        fuzzy: bool = True,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search providers with automatic fuzzy fallback.
        
        Args:
            query: Provider name or keyword
            state: State filter (2-letter code)
            city: City filter
            npi: NPI number (exact match only)
            phone: Phone number
            parent_organization: Parent company name
            fuzzy: Enable fuzzy matching fallback
            limit: Max results
        
        Returns:
            List of SearchResult objects sorted by match quality
        """
        self.connect()
        
        # Priority 1: Exact NPI match (highest priority)
        if npi:
            results = self._search_by_npi(npi)
            if results:
                return results[:limit]
        
        # Priority 2: Exact phone match
        if phone:
            results = self._search_by_phone(phone)
            if results:
                return results[:limit]
        
        # Priority 3: Exact name match
        if query:
            results = self._search_exact(query, state, city, parent_organization)
            if results:
                return results[:limit]
            
            # Priority 4: Full-text search
            results = self._search_fulltext(query, state, city)
            if results:
                return results[:limit]
            
            # Priority 5: Fuzzy matching
            if fuzzy:
                results = self._search_fuzzy(query, state, city, parent_organization)
                return results[:limit]
        
        # No query provided, list by filters
        return self._list_providers(state, city, parent_organization, limit)
    
    def _search_by_npi(self, npi: str) -> List[SearchResult]:
        """Exact NPI search."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM providers WHERE npi = %s
        """, (npi,))
        
        results = []
        for row in cur.fetchall():
            results.append(SearchResult(
                match_type='exact_npi',
                match_score=1.0,
                provider=dict(row),
                confidence=1.0
            ))
        return results
    
    def _search_by_phone(self, phone: str) -> List[SearchResult]:
        """Exact phone search."""
        # Normalize phone number (remove formatting)
        phone_normalized = re.sub(r'[^\d]', '', phone)
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM providers 
            WHERE regexp_replace(phone, '[^0-9]', '', 'g') = %s
        """, (phone_normalized,))
        
        results = []
        for row in cur.fetchall():
            results.append(SearchResult(
                match_type='exact_phone',
                match_score=1.0,
                provider=dict(row),
                confidence=0.95
            ))
        return results
    
    def _search_exact(
        self,
        query: str,
        state: str = None,
        city: str = None,
        parent_org: str = None
    ) -> List[SearchResult]:
        """Exact SQL LIKE matching."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT * FROM providers 
            WHERE (legal_name ILIKE %s 
                   OR parent_organization ILIKE %s
                   OR dba_names::text ILIKE %s)
        """
        params = [f'%{query}%', f'%{query}%', f'%{query}%']
        
        if state:
            sql += " AND address_state = %s"
            params.append(state)
        if city:
            sql += " AND address_city ILIKE %s"
            params.append(f'%{city}%')
        if parent_org:
            sql += " AND parent_organization ILIKE %s"
            params.append(f'%{parent_org}%')
        
        cur.execute(sql, params)
        
        results = []
        for row in cur.fetchall():
            results.append(SearchResult(
                match_type='exact',
                match_score=1.0,
                provider=dict(row),
                confidence=0.95
            ))
        return results
    
    def _search_fulltext(
        self,
        query: str,
        state: str = None,
        city: str = None
    ) -> List[SearchResult]:
        """PostgreSQL full-text search."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT *, 
                   ts_rank(to_tsvector('english', legal_name || ' ' || COALESCE(parent_organization, '')), 
                          plainto_tsquery('english', %s)) as rank
            FROM providers
            WHERE to_tsvector('english', legal_name || ' ' || COALESCE(parent_organization, ''))
                  @@ plainto_tsquery('english', %s)
        """
        params = [query, query]
        
        if state:
            sql += " AND address_state = %s"
            params.append(state)
        if city:
            sql += " AND address_city ILIKE %s"
            params.append(f'%{city}%')
        
        sql += " ORDER BY rank DESC"
        
        cur.execute(sql, params)
        
        results = []
        for row in cur.fetchall():
            row_dict = dict(row)
            rank = row_dict.pop('rank', 0)
            results.append(SearchResult(
                match_type='fulltext',
                match_score=min(rank * 2, 1.0),  # Normalize rank to 0-1
                provider=row_dict,
                confidence=0.85
            ))
        return results
    
    def _search_fuzzy(
        self,
        query: str,
        state: str = None,
        city: str = None,
        parent_org: str = None
    ) -> List[SearchResult]:
        """Fuzzy Levenshtein matching."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = "SELECT * FROM providers WHERE 1=1"
        params = []
        
        if state:
            sql += " AND address_state = %s"
            params.append(state)
        if city:
            sql += " AND address_city ILIKE %s"
            params.append(f'%{city}%')
        if parent_org:
            sql += " AND parent_organization ILIKE %s"
            params.append(f'%{parent_org}%')
        
        cur.execute(sql, params)
        
        results = []
        for row in cur.fetchall():
            row_dict = dict(row)
            legal_name = row_dict.get('legal_name', '')
            parent = row_dict.get('parent_organization', '')
            
            # Calculate similarity scores
            name_score = SequenceMatcher(None, query.lower(), legal_name.lower()).ratio()
            parent_score = SequenceMatcher(None, query.lower(), parent.lower()).ratio() if parent else 0
            
            max_score = max(name_score, parent_score)
            
            if max_score >= self.LOW_CONFIDENCE_THRESHOLD:
                confidence = self._score_to_confidence(max_score)
                results.append(SearchResult(
                    match_type='fuzzy',
                    match_score=max_score,
                    provider=row_dict,
                    confidence=confidence
                ))
        
        # Sort by score
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
    
    def _list_providers(
        self,
        state: str = None,
        city: str = None,
        parent_org: str = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """List providers by filters."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = "SELECT * FROM providers WHERE 1=1"
        params = []
        
        if state:
            sql += " AND address_state = %s"
            params.append(state)
        if city:
            sql += " AND address_city ILIKE %s"
            params.append(f'%{city}%')
        if parent_org:
            sql += " AND parent_organization ILIKE %s"
            params.append(f'%{parent_org}%')
        
        sql += f" LIMIT {limit}"
        
        cur.execute(sql, params)
        
        results = []
        for row in cur.fetchall():
            results.append(SearchResult(
                match_type='list',
                match_score=0.5,
                provider=dict(row),
                confidence=0.5
            ))
        return results
    
    def _score_to_confidence(self, score: float) -> float:
        """Convert match score to confidence level."""
        if score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return 0.9
        elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return 0.7
        else:
            return 0.5
    
    def add_provider(self, provider_data: Dict) -> str:
        """
        Add a new provider to the database.
        
        Args:
            provider_data: Dictionary with provider fields
        
        Returns:
            Provider ID (UUID)
        """
        self.connect()
        provider_id = str(uuid.uuid4())
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO providers (
                id, npi, legal_name, dba_names, name_variations,
                address_full, address_city, address_state, address_zip,
                phone, parent_organization, franchise_id,
                location_website, created_at, validated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (npi) DO UPDATE SET
                legal_name = EXCLUDED.legal_name,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            provider_id,
            provider_data.get('npi'),
            provider_data.get('legal_name'),
            json.dumps(provider_data.get('dba_names', [])),
            json.dumps(self._generate_name_variations(provider_data.get('legal_name', ''))),
            provider_data.get('address'),
            provider_data.get('city'),
            provider_data.get('state'),
            provider_data.get('zip'),
            provider_data.get('phone'),
            provider_data.get('parent_organization'),
            provider_data.get('franchise_id'),
            provider_data.get('website'),
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        result = cur.fetchone()
        return result[0] if result else provider_id
    
    def update_provider(self, provider_id: str, updates: Dict) -> bool:
        """Update an existing provider."""
        self.connect()
        
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        params.append(provider_id)
        
        cur = self.conn.cursor()
        cur.execute(f"""
            UPDATE providers 
            SET {', '.join(set_clauses)}, last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, params)
        
        return cur.rowcount > 0
    
    def delete_provider(self, provider_id: str) -> bool:
        """Delete a provider."""
        self.connect()
        
        cur = self.conn.cursor()
        cur.execute("DELETE FROM providers WHERE id = %s", (provider_id,))
        
        return cur.rowcount > 0
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        self.connect()
        
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*) as total_providers,
                COUNT(DISTINCT address_state) as states_covered,
                COUNT(*) FILTER (WHERE npi IS NOT NULL) as with_npi,
                AVG(confidence_score) as avg_confidence
            FROM providers
        """)
        
        row = cur.fetchone()
        return {
            'total_providers': row[0],
            'states_covered': row[1],
            'with_npi': row[2],
            'avg_confidence': float(row[3]) if row[3] else 0
        }
    
    def _generate_name_variations(self, legal_name: str) -> List[str]:
        """Generate searchable name variations."""
        variations = [legal_name.lower()]
        
        # Remove common suffixes
        for suffix in [' Inc', ' LLC', ' Corp', ' Corporation', ' Ltd']:
            if legal_name.endswith(suffix):
                variations.append(legal_name[:-len(suffix)].lower())
        
        return list(set(variations))
    
    def close(self):
        """Close database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
