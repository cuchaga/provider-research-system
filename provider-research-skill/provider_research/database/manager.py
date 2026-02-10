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
    from provider_research import ProviderDatabaseManager
    
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
    
    def record_history(self,
                      provider_id: str,
                      change_type: str,
                      field_name: str,
                      old_value: str,
                      new_value: str,
                      effective_date: datetime = None,
                      source: str = 'user_input',
                      notes: str = None,
                      recorded_by: str = None) -> str:
        """
        Record a change to provider history.
        
        Args:
            provider_id: ID of the provider
            change_type: Type of change (name_change, ownership_change, dba_change, merger, acquisition)
            field_name: Field that changed (legal_name, parent_organization, dba_names)
            old_value: Previous value
            new_value: New value
            effective_date: When the change took effect
            source: Where the information came from
            notes: Additional context
            recorded_by: Who recorded the change
            
        Returns:
            history_id
        """
        if not self.conn:
            self.connect()
            
        history_id = str(uuid.uuid4())
        effective_date = effective_date or datetime.utcnow()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO provider_history (
                id, provider_id, change_type, field_name,
                old_value, new_value, effective_date,
                source, notes, recorded_at, recorded_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            history_id, provider_id, change_type, field_name,
            old_value, new_value, effective_date,
            source, notes, datetime.utcnow(), recorded_by
        ))
        
        result = cur.fetchone()
        return result[0] if result else history_id
    
    def get_provider_history(self, provider_id: str) -> List[Dict]:
        """
        Get complete history for a provider.
        
        Returns:
            List of history records, ordered by effective_date desc
        """
        if not self.conn:
            self.connect()
            
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                id, change_type, field_name,
                old_value, new_value, effective_date,
                source, notes, recorded_at, recorded_by
            FROM provider_history
            WHERE provider_id = %s
            ORDER BY effective_date DESC, recorded_at DESC
        """, (provider_id,))
        
        return [dict(row) for row in cur.fetchall()]
    
    def get_previous_names(self, provider_id: str) -> List[Dict]:
        """
        Get all previous legal names and DBAs for a provider.
        
        Returns:
            List of {name, type, effective_date, source}
        """
        if not self.conn:
            self.connect()
            
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                old_value as name,
                change_type as type,
                effective_date,
                source
            FROM provider_history
            WHERE provider_id = %s
              AND change_type IN ('name_change', 'dba_change')
            ORDER BY effective_date DESC
        """, (provider_id,))
        
        return [dict(row) for row in cur.fetchall()]
    
    def get_previous_owners(self, provider_id: str) -> List[Dict]:
        """
        Get all previous owners/parent organizations.
        
        Returns:
            List of {owner, effective_date, source, notes}
        """
        if not self.conn:
            self.connect()
            
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                old_value as owner,
                effective_date,
                source,
                notes
            FROM provider_history
            WHERE provider_id = %s
              AND change_type IN ('ownership_change', 'acquisition', 'merger')
            ORDER BY effective_date DESC
        """, (provider_id,))
        
        return [dict(row) for row in cur.fetchall()]
    
    def update_provider_with_history(self,
                                     provider_id: str,
                                     field_name: str,
                                     new_value: str,
                                     change_type: str,
                                     effective_date: datetime = None,
                                     source: str = 'user_input',
                                     notes: str = None) -> bool:
        """
        Update a provider field and automatically record the change to history.
        
        Args:
            provider_id: ID of provider to update
            field_name: Field to update (legal_name, parent_organization, etc.)
            new_value: New value for the field
            change_type: Type of change for history record
            effective_date: When change took effect
            source: Source of the information
            notes: Additional context
            
        Returns:
            True if successful
        """
        if not self.conn:
            self.connect()
            
        # Get current value first
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT {field_name} FROM providers WHERE id = %s", (provider_id,))
        row = cur.fetchone()
        if not row:
            return False
        
        old_value = row[field_name]
        
        # Record to history
        self.record_history(
            provider_id=provider_id,
            change_type=change_type,
            field_name=field_name,
            old_value=str(old_value) if old_value else None,
            new_value=new_value,
            effective_date=effective_date,
            source=source,
            notes=notes
        )
        
        # Update the provider
        cur.execute(f"""
            UPDATE providers 
            SET {field_name} = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_value, provider_id))
        
        return True
    
    def display_providers(self, fields: List[str] = None, provider_id: str = None) -> List[Dict]:
        """
        Display providers with specified fields or default comprehensive view.
        
        Args:
            fields: List of fields to display. If None, shows default comprehensive view:
                   - business_name (legal_name)
                   - dbas (dba_names)
                   - current_address
                   - previous_addresses (from history)
                   - current_phone
                   - previous_phones (from history)
                   - current_owner (parent_organization)
                   - previous_owners (from history)
            provider_id: Optional specific provider ID. If None, shows all providers.
            
        Returns:
            List of provider records with requested fields and historical data
        """
        if not self.conn:
            self.connect()
        
        # Default fields if none specified
        default_fields = [
            'business_name', 'dbas', 
            'current_address', 'previous_addresses',
            'current_phone', 'previous_phones',
            'current_owner', 'previous_owners'
        ]
        
        fields_to_show = fields or default_fields
        results = []
        
        # Get all providers or specific one
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        if provider_id:
            cur.execute("SELECT * FROM providers WHERE id = %s", (provider_id,))
        else:
            cur.execute("SELECT * FROM providers ORDER BY legal_name")
        
        providers = cur.fetchall()
        
        for provider in providers:
            provider_dict = dict(provider)
            display_record = {'id': provider_dict['id']}
            
            # Business name
            if 'business_name' in fields_to_show:
                display_record['business_name'] = provider_dict.get('legal_name')
            
            # DBAs
            if 'dbas' in fields_to_show:
                display_record['dbas'] = provider_dict.get('dba_names', [])
            
            # Current address
            if 'current_address' in fields_to_show:
                address_parts = []
                if provider_dict.get('address_line1'):
                    address_parts.append(provider_dict['address_line1'])
                if provider_dict.get('address_line2'):
                    address_parts.append(provider_dict['address_line2'])
                if provider_dict.get('city'):
                    city_state_zip = provider_dict['city']
                    if provider_dict.get('state'):
                        city_state_zip += f", {provider_dict['state']}"
                    if provider_dict.get('zip_code'):
                        city_state_zip += f" {provider_dict['zip_code']}"
                    address_parts.append(city_state_zip)
                display_record['current_address'] = ', '.join(address_parts) if address_parts else None
            
            # Previous addresses from history
            if 'previous_addresses' in fields_to_show:
                cur.execute("""
                    SELECT old_value, effective_date, source
                    FROM provider_history
                    WHERE provider_id = %s
                      AND field_name IN ('address_line1', 'city', 'state', 'zip_code')
                    ORDER BY effective_date DESC
                """, (provider_dict['id'],))
                prev_addresses = [dict(row) for row in cur.fetchall()]
                display_record['previous_addresses'] = prev_addresses
            
            # Current phone
            if 'current_phone' in fields_to_show:
                display_record['current_phone'] = provider_dict.get('phone')
            
            # Previous phones from history
            if 'previous_phones' in fields_to_show:
                cur.execute("""
                    SELECT old_value as phone, effective_date, source
                    FROM provider_history
                    WHERE provider_id = %s
                      AND field_name = 'phone'
                    ORDER BY effective_date DESC
                """, (provider_dict['id'],))
                prev_phones = [dict(row) for row in cur.fetchall()]
                display_record['previous_phones'] = prev_phones
            
            # Current owner
            if 'current_owner' in fields_to_show:
                display_record['current_owner'] = provider_dict.get('parent_organization')
            
            # Previous owners from history
            if 'previous_owners' in fields_to_show:
                prev_owners = self.get_previous_owners(provider_dict['id'])
                display_record['previous_owners'] = prev_owners
            
            # Data source URLs
            if 'data_source_urls' in fields_to_show:
                display_record['data_source_urls'] = provider_dict.get('data_source_urls', [])
            
            # Add any other directly requested fields
            for field in fields_to_show:
                if field not in display_record and field in provider_dict:
                    display_record[field] = provider_dict[field]
            
            results.append(display_record)
        
        return results
    
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
                - legal_name: Required
                - city, state: Required
                - npi, phone, address, zip: Optional
                - parent_organization: Business owner/parent company
                - real_estate_owner: Property owner/landlord
                - franchise_id, website, dba_names: Optional
                - data_source_urls: List of URLs where data was obtained
        
        Returns:
            Provider ID (UUID)
        """
        self.connect()
        provider_id = str(uuid.uuid4())
        
        # Helper function to convert list to PostgreSQL array format
        def to_pg_array(items):
            if not items or not isinstance(items, list):
                return None
            # Format as PostgreSQL array: '{"item1","item2"}'
            return '{' + ','.join([f'"{str(item).replace(chr(34), chr(34)+chr(34))}"' for item in items]) + '}'
        
        # Handle array fields
        dba_names_array = to_pg_array(provider_data.get('dba_names'))
        name_variations_array = to_pg_array(self._generate_name_variations(provider_data.get('legal_name', '')))
        data_source_urls_array = to_pg_array(provider_data.get('data_source_urls'))
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO providers (
                id, npi, legal_name, dba_names, name_variations,
                address_full, address_city, address_state, address_zip,
                phone, parent_organization, real_estate_owner, franchise_id,
                location_website, data_source_urls, created_at, validated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (npi) DO UPDATE SET
                legal_name = EXCLUDED.legal_name,
                data_source_urls = COALESCE(EXCLUDED.data_source_urls, providers.data_source_urls),
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            provider_id,
            provider_data.get('npi'),
            provider_data.get('legal_name'),
            dba_names_array,
            name_variations_array,
            provider_data.get('address'),
            provider_data.get('city'),
            provider_data.get('state'),
            provider_data.get('zip'),
            provider_data.get('phone'),
            provider_data.get('parent_organization'),
            provider_data.get('real_estate_owner'),
            provider_data.get('franchise_id'),
            provider_data.get('website'),
            data_source_urls_array,
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
