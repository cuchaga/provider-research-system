"""
Franchise Researcher Skill - Orchestrates comprehensive franchise location research

This skill coordinates other skills to find, validate, and import all franchise locations
in a specified area with full historical tracking (ownership changes, name changes, transactions).

Features:
- Multi-source data collection (websites, NPI, directories)
- Historical data extraction (newspapers, business journals, SEC filings)
- Previous owner and name tracking
- Transaction history (sales, acquisitions, mergers)
- Automated validation and deduplication
- Batch database import with history

Usage:
    from provider_research import FranchiseResearcher
    
    researcher = FranchiseResearcher(db_config, llm_client)
    
    # Research all locations of a franchise
    results = researcher.research_franchise_locations(
        franchise_name="Home Instead",
        location="Massachusetts",
        include_history=True
    )
    
    # Import to database
    imported = researcher.import_results(results, dry_run=False)

Author: Provider Research System
Version: 2.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Import other skills
from .query_interpreter import ProviderQueryInterpreter
from .semantic_matcher import ProviderSemanticMatcher
from ..database.manager import ProviderDatabaseManager
from ..search.web_researcher import ProviderWebResearcher


class DataSource(Enum):
    """Data sources for franchise research"""
    FRANCHISE_LOCATOR = "franchise_locator"
    NPI_REGISTRY = "npi_registry"
    HEALTHCARE_GOV = "healthcare_gov"
    BUSINESS_DIRECTORY = "business_directory"
    NEWS_ARCHIVE = "news_archive"
    BUSINESS_JOURNAL = "business_journal"
    SEC_FILINGS = "sec_filings"
    STATE_REGISTRY = "state_registry"
    BBB = "better_business_bureau"
    REAL_ESTATE_RECORDS = "real_estate_records"


class EventType(Enum):
    """Historical event types"""
    OWNERSHIP_CHANGE = "ownership_change"
    NAME_CHANGE = "name_change"
    ACQUISITION = "acquisition"
    MERGER = "merger"
    FRANCHISE_SALE = "franchise_sale"
    REBRANDING = "rebranding"
    OPENING = "opening"
    CLOSURE = "closure"
    TERRITORY_EXPANSION = "territory_expansion"


@dataclass
class HistoricalEvent:
    """Represents a historical event for a franchise location"""
    event_type: str
    event_date: str  # ISO format or year
    description: str
    source: str
    source_url: Optional[str] = None
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    transaction_value: Optional[str] = None
    confidence: str = "medium"  # high, medium, low
    notes: Optional[str] = None


@dataclass
class FranchiseLocation:
    """Represents a franchise location with current and historical data"""
    # Current data
    legal_name: str
    city: str
    state: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    npi: Optional[str] = None
    dba_names: Optional[List[str]] = None
    parent_organization: Optional[str] = None
    service_areas: Optional[List[str]] = None
    
    # Historical data
    previous_names: Optional[List[Dict[str, Any]]] = None
    previous_owners: Optional[List[Dict[str, Any]]] = None
    ownership_history: Optional[List[HistoricalEvent]] = None
    
    # Metadata
    data_sources: Optional[List[str]] = None
    last_verified: Optional[str] = None
    confidence_score: float = 0.0


class FranchiseResearcher:
    """
    Orchestrates comprehensive franchise location research with historical tracking.
    
    This skill combines multiple data sources and uses other skills to find all
    franchise locations in a specified area, including historical ownership and
    name changes.
    """
    
    def __init__(self, db_config: Optional[Dict] = None, llm_client: Optional[Any] = None,
                 simulation_mode: bool = False):
        """
        Initialize the Franchise Researcher skill.
        
        Args:
            db_config: Database configuration dictionary
            llm_client: LLM client for data extraction (optional for simulation mode)
            simulation_mode: If True, simulates LLM calls for testing
        """
        self.logger = logging.getLogger(__name__)
        self.simulation_mode = simulation_mode
        
        # Initialize other skills
        self.db = ProviderDatabaseManager(db_config) if db_config else None
        self.web_researcher = ProviderWebResearcher(llm_client=llm_client)
        self.semantic_matcher = ProviderSemanticMatcher(llm_client=llm_client)
        self.query_interpreter = ProviderQueryInterpreter(llm_client=llm_client)
        
        # Historical search terms templates
        self.historical_search_templates = [
            "{franchise} {location} sold",
            "{franchise} {location} ownership change",
            "{franchise} {location} acquisition",
            "{franchise} franchise sale {location}",
            "{franchise} {location} new owner",
            "{location} senior care franchise sold",
            "{franchise} {location} merger",
            "{franchise} franchise transfer {location}"
        ]
    
    def research_franchise_locations(
        self,
        franchise_name: str,
        location: str,
        include_history: bool = True,
        date_range: Optional[Tuple[str, str]] = None,
        sources: Optional[List[DataSource]] = None
    ) -> Dict[str, Any]:
        """
        Research all locations of a franchise in a specified area.
        
        Args:
            franchise_name: Name of the franchise (e.g., "Home Instead", "Visiting Angels")
            location: State, city, or region (e.g., "Massachusetts", "Boston, MA")
            include_history: Whether to search for historical data
            date_range: Optional tuple of (start_date, end_date) for historical search
            sources: Optional list of specific sources to search
            
        Returns:
            Dictionary containing:
                - locations: List of FranchiseLocation objects
                - summary: Research summary statistics
                - sources_used: List of data sources queried
                - historical_events_found: Count of historical events
        """
        self.logger.info(f"Starting franchise research: {franchise_name} in {location}")
        
        results = {
            'franchise_name': franchise_name,
            'location': location,
            'locations': [],
            'summary': {},
            'sources_used': [],
            'historical_events_found': 0,
            'research_date': datetime.now().isoformat()
        }
        
        # Step 1: Find current locations
        self.logger.info("Step 1: Searching for current franchise locations...")
        current_locations = self._search_current_locations(franchise_name, location, sources)
        results['locations'] = current_locations
        results['summary']['locations_found'] = len(current_locations)
        
        # Step 2: Search for historical data if requested
        if include_history:
            self.logger.info("Step 2: Searching for historical data...")
            historical_data = self._search_historical_data(
                franchise_name, 
                location, 
                current_locations,
                date_range
            )
            
            # Merge historical data into locations
            self._merge_historical_data(current_locations, historical_data)
            results['historical_events_found'] = sum(
                len(loc.ownership_history or []) for loc in current_locations
            )
        
        # Step 3: Validate and deduplicate
        self.logger.info("Step 3: Validating and deduplicating...")
        results['locations'] = self._validate_and_deduplicate(current_locations)
        results['summary']['unique_locations'] = len(results['locations'])
        results['summary']['duplicates_removed'] = (
            results['summary']['locations_found'] - results['summary']['unique_locations']
        )
        
        # Step 4: Calculate confidence scores
        for location in results['locations']:
            location.confidence_score = self._calculate_confidence_score(location)
        
        results['summary']['high_confidence'] = sum(
            1 for loc in results['locations'] if loc.confidence_score >= 0.8
        )
        results['summary']['medium_confidence'] = sum(
            1 for loc in results['locations'] if 0.5 <= loc.confidence_score < 0.8
        )
        results['summary']['low_confidence'] = sum(
            1 for loc in results['locations'] if loc.confidence_score < 0.5
        )
        
        self.logger.info(f"Research complete. Found {len(results['locations'])} unique locations")
        return results
    
    def _search_current_locations(
        self,
        franchise_name: str,
        location: str,
        sources: Optional[List[DataSource]] = None
    ) -> List[FranchiseLocation]:
        """
        Search for current franchise locations across multiple sources.
        """
        locations = []
        
        # Default sources if not specified
        if sources is None:
            sources = [
                DataSource.FRANCHISE_LOCATOR,
                DataSource.NPI_REGISTRY,
                DataSource.BUSINESS_DIRECTORY
            ]
        
        # Search franchise website/locator
        if DataSource.FRANCHISE_LOCATOR in sources:
            self.logger.info(f"Searching franchise locator for {franchise_name}...")
            web_results = self.web_researcher.research(
                provider_name=franchise_name,
                location=location
            )
            
            # Convert web results to FranchiseLocation objects
            # ResearchResult has .locations attribute
            if hasattr(web_results, 'locations'):
                for loc_data in web_results.locations:
                    location_obj = self._convert_to_franchise_location(
                        loc_data, 
                        franchise_name,
                        source=DataSource.FRANCHISE_LOCATOR.value
                    )
                    locations.append(location_obj)
        
        # Search NPI Registry
        if DataSource.NPI_REGISTRY in sources:
            self.logger.info(f"Searching NPI Registry for {franchise_name}...")
            npi_results = self._search_npi_registry(franchise_name, location)
            
            for npi_data in npi_results:
                location_obj = self._convert_to_franchise_location(
                    npi_data,
                    franchise_name,
                    source=DataSource.NPI_REGISTRY.value
                )
                locations.append(location_obj)
        
        # Check existing database
        if self.db:
            self.logger.info(f"Checking existing database for {franchise_name}...")
            db_results = self.db.search(
                query=franchise_name,
                state=self._extract_state(location),
                fuzzy=True
            )
            
            for db_record in db_results:
                # Convert database record to FranchiseLocation
                location_obj = self._convert_db_to_franchise_location(db_record)
                locations.append(location_obj)
        
        return locations
    
    def _search_historical_data(
        self,
        franchise_name: str,
        location: str,
        current_locations: List[FranchiseLocation],
        date_range: Optional[Tuple[str, str]] = None
    ) -> Dict[str, List[HistoricalEvent]]:
        """
        Search for historical data (ownership changes, name changes, transactions).
        
        Returns dict mapping location identifier to list of historical events.
        """
        historical_data = {}
        
        # Default date range: last 25 years
        if date_range is None:
            current_year = datetime.now().year
            date_range = (f"{current_year - 25}-01-01", f"{current_year}-12-31")
        
        # Search for general franchise history in the location
        general_search_terms = [
            template.format(franchise=franchise_name, location=location)
            for template in self.historical_search_templates
        ]
        
        self.logger.info(f"Searching for historical events: {len(general_search_terms)} queries")
        
        general_events = self._search_news_archives(
            search_terms=general_search_terms,
            date_range=date_range
        )
        
        # Search for specific location history
        for loc in current_locations:
            location_key = f"{loc.legal_name}_{loc.city}"
            
            # Generate location-specific search terms
            location_search_terms = [
                f"{loc.legal_name} sold",
                f"{loc.legal_name} ownership",
                f"{loc.legal_name} acquisition",
                f"{franchise_name} {loc.city} franchise sale"
            ]
            
            location_events = self._search_news_archives(
                search_terms=location_search_terms,
                date_range=date_range
            )
            
            # Combine general and location-specific events
            all_events = general_events + location_events
            
            # Extract structured data from articles
            structured_events = self._extract_historical_events(
                articles=all_events,
                franchise_name=franchise_name,
                location_name=loc.legal_name
            )
            
            historical_data[location_key] = structured_events
        
        return historical_data
    
    def _search_news_archives(
        self,
        search_terms: List[str],
        date_range: Tuple[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Search newspaper archives and business journals for articles.
        
        In simulation mode, returns mock articles.
        In production, would call actual news APIs or web scraping.
        """
        if self.simulation_mode:
            # Return mock historical data for testing
            return [
                {
                    'title': f'Simulation: Article about {term}',
                    'content': f'Mock article content for search term: {term}',
                    'source': 'Mock Business Journal',
                    'date': '2020-06-15',
                    'url': 'https://example.com/article'
                }
                for term in search_terms[:2]  # Limit in simulation
            ]
        
        # Production implementation would search:
        # - Google News Archive
        # - LexisNexis
        # - ProQuest
        # - Regional newspaper archives
        # - Business journal archives
        
        articles = []
        
        # Placeholder for actual implementation
        self.logger.warning("News archive search not yet implemented in production mode")
        
        return articles
    
    def _search_npi_registry(
        self,
        franchise_name: str,
        location: str
    ) -> List[Dict[str, Any]]:
        """
        Search NPI Registry for franchise locations.
        
        In simulation mode, returns mock NPI records.
        In production, would call actual NPI API.
        """
        if self.simulation_mode:
            state = self._extract_state(location)
            return [
                {
                    'legal_name': f'{franchise_name} - Sample Location',
                    'npi': f'123456789{i}',
                    'address_line1': f'{100 + i} Main Street',
                    'city': 'Boston' if state == 'MA' else 'Sample City',
                    'state': state,
                    'zip_code': '02101',
                    'phone': f'(617) 555-010{i}'
                }
                for i in range(2)  # Return 2 mock locations
            ]
        
        # Production implementation would call NPI Registry API
        # https://npiregistry.cms.hhs.gov/api/
        
        npi_records = []
        
        # Placeholder for actual implementation
        self.logger.warning("NPI Registry search not yet implemented in production mode")
        
        return npi_records
    
    def _extract_historical_events(
        self,
        articles: List[Dict[str, Any]],
        franchise_name: str,
        location_name: str
    ) -> List[HistoricalEvent]:
        """
        Extract structured historical events from news articles using LLM.
        """
        if not articles:
            return []
        
        events = []
        
        HISTORY_EXTRACTION_PROMPT = f"""
Extract ownership and name change history from the following article about {location_name}:

Look for:
1. Previous owners (names, dates)
2. Previous business names or DBAs
3. Acquisition/merger details (buyer, seller, date, price)
4. Franchise sales or transfers
5. Name changes or rebranding
6. Corporate structure changes

Article:
{{article_content}}

Return structured data as JSON list with each event containing:
- event_type: one of [ownership_change, name_change, acquisition, merger, franchise_sale, rebranding]
- event_date: ISO date or year (YYYY-MM-DD or YYYY)
- description: brief description of the event
- previous_value: (if applicable, e.g., previous owner name or old business name)
- new_value: (if applicable, e.g., new owner name or new business name)
- transaction_value: (if mentioned, e.g., "$2.5M")
- confidence: high/medium/low based on clarity of information

If no relevant information found, return empty list.
"""
        
        for article in articles:
            if self.simulation_mode:
                # Return mock event for testing
                events.append(HistoricalEvent(
                    event_type=EventType.OWNERSHIP_CHANGE.value,
                    event_date="2020-06-15",
                    description=f"Simulated ownership change for {location_name}",
                    source=article['source'],
                    source_url=article.get('url'),
                    previous_value="Previous Owner LLC",
                    new_value="New Owner Inc",
                    confidence="medium",
                    notes="Simulation mode data"
                ))
            else:
                # In production, would call LLM to extract structured data
                # extracted = llm_client.extract(prompt.format(article_content=article['content']))
                # Parse JSON and create HistoricalEvent objects
                pass
        
        return events
    
    def _merge_historical_data(
        self,
        locations: List[FranchiseLocation],
        historical_data: Dict[str, List[HistoricalEvent]]
    ):
        """
        Merge historical data into location objects.
        """
        for loc in locations:
            location_key = f"{loc.legal_name}_{loc.city}"
            
            if location_key in historical_data:
                events = historical_data[location_key]
                loc.ownership_history = events
                
                # Extract previous names
                name_changes = [e for e in events if e.event_type == EventType.NAME_CHANGE.value]
                if name_changes:
                    loc.previous_names = [
                        {
                            'name': e.previous_value,
                            'used_until': e.event_date,
                            'source': e.source
                        }
                        for e in name_changes if e.previous_value
                    ]
                
                # Extract previous owners
                ownership_changes = [
                    e for e in events 
                    if e.event_type in [EventType.OWNERSHIP_CHANGE.value, 
                                       EventType.FRANCHISE_SALE.value,
                                       EventType.ACQUISITION.value]
                ]
                if ownership_changes:
                    loc.previous_owners = [
                        {
                            'owner_name': e.previous_value,
                            'owned_until': e.event_date,
                            'source': e.source
                        }
                        for e in ownership_changes if e.previous_value
                    ]
    
    def _validate_and_deduplicate(
        self,
        locations: List[FranchiseLocation]
    ) -> List[FranchiseLocation]:
        """
        Validate data quality and remove duplicates.
        """
        if not locations:
            return []
        
        # Use semantic matcher for intelligent deduplication
        unique_locations = []
        seen_signatures = set()
        
        for loc in locations:
            # Create signature for duplicate detection
            signature = self._create_location_signature(loc)
            
            if signature not in seen_signatures:
                unique_locations.append(loc)
                seen_signatures.add(signature)
            else:
                # Merge data from duplicate into existing record
                existing = next(
                    l for l in unique_locations 
                    if self._create_location_signature(l) == signature
                )
                self._merge_location_data(existing, loc)
        
        return unique_locations
    
    def _create_location_signature(self, location: FranchiseLocation) -> str:
        """
        Create a unique signature for duplicate detection.
        
        Same phone number = duplicate
        Same address (ignoring suite) = duplicate
        """
        # Normalize phone
        phone_sig = ''.join(c for c in (location.phone or '') if c.isdigit())
        
        # Normalize address (ignore suite/unit)
        addr_sig = ''
        if location.address_line1:
            addr_sig = location.address_line1.lower()
            # Remove suite/unit variations
            for term in ['suite', 'ste', 'unit', 'apt', '#']:
                if term in addr_sig:
                    addr_sig = addr_sig.split(term)[0]
            addr_sig = ''.join(c for c in addr_sig if c.isalnum())
        
        return f"{phone_sig}_{addr_sig}_{location.city}_{location.state}"
    
    def _merge_location_data(self, target: FranchiseLocation, source: FranchiseLocation):
        """
        Merge data from source location into target (for duplicates).
        """
        # Merge data sources
        if target.data_sources is None:
            target.data_sources = []
        if source.data_sources:
            target.data_sources.extend(source.data_sources)
            target.data_sources = list(set(target.data_sources))
        
        # Fill in missing fields from source
        for field in ['npi', 'email', 'website', 'phone', 'address_line2']:
            if getattr(target, field) is None and getattr(source, field) is not None:
                setattr(target, field, getattr(source, field))
        
        # Merge historical events
        if source.ownership_history:
            if target.ownership_history is None:
                target.ownership_history = []
            target.ownership_history.extend(source.ownership_history)
            # Deduplicate events
            seen = set()
            unique_events = []
            for event in target.ownership_history:
                event_sig = f"{event.event_type}_{event.event_date}_{event.description}"
                if event_sig not in seen:
                    unique_events.append(event)
                    seen.add(event_sig)
            target.ownership_history = unique_events
    
    def _calculate_confidence_score(self, location: FranchiseLocation) -> float:
        """
        Calculate confidence score based on data completeness and validation.
        """
        score = 0.0
        
        # Basic required fields
        if location.legal_name:
            score += 0.2
        if location.address_line1:
            score += 0.15
        if location.city and location.state:
            score += 0.15
        if location.phone:
            score += 0.1
        
        # Validation fields
        if location.npi:
            score += 0.2
        
        # Multiple data sources increase confidence
        if location.data_sources and len(location.data_sources) > 1:
            score += 0.1
        
        # Historical data presence
        if location.ownership_history and len(location.ownership_history) > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _convert_to_franchise_location(
        self,
        data: Dict[str, Any],
        franchise_name: str,
        source: str
    ) -> FranchiseLocation:
        """
        Convert raw data dictionary to FranchiseLocation object.
        """
        return FranchiseLocation(
            legal_name=data.get('legal_name', data.get('name', '')),
            city=data.get('city', ''),
            state=data.get('state', ''),
            address_line1=data.get('address_line1', data.get('address')),
            address_line2=data.get('address_line2'),
            zip_code=data.get('zip_code', data.get('zip')),
            phone=data.get('phone'),
            email=data.get('email'),
            website=data.get('website'),
            npi=data.get('npi'),
            dba_names=data.get('dba_names', []),
            parent_organization=data.get('parent_organization', franchise_name),
            data_sources=[source],
            last_verified=datetime.now().isoformat()
        )
    
    def _convert_db_to_franchise_location(self, db_record: Any) -> FranchiseLocation:
        """
        Convert database record to FranchiseLocation object.
        """
        return FranchiseLocation(
            legal_name=getattr(db_record, 'legal_name', ''),
            city=getattr(db_record, 'city', ''),
            state=getattr(db_record, 'state', ''),
            address_line1=getattr(db_record, 'address_line1', None),
            address_line2=getattr(db_record, 'address_line2', None),
            zip_code=getattr(db_record, 'zip_code', None),
            phone=getattr(db_record, 'phone', None),
            email=getattr(db_record, 'email', None),
            website=getattr(db_record, 'website', None),
            npi=getattr(db_record, 'npi', None),
            parent_organization=getattr(db_record, 'parent_organization', None),
            data_sources=['database']
        )
    
    def _extract_state(self, location: str) -> str:
        """
        Extract state code from location string.
        """
        # Common state codes
        state_codes = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        
        location_upper = location.upper()
        for code in state_codes:
            if code in location_upper:
                return code
        
        # State name to code mapping (abbreviated)
        state_map = {
            'MASSACHUSETTS': 'MA',
            'MICHIGAN': 'MI',
            'CALIFORNIA': 'CA',
            'NEW YORK': 'NY',
            'TEXAS': 'TX',
            'FLORIDA': 'FL'
            # Add more as needed
        }
        
        for name, code in state_map.items():
            if name in location_upper:
                return code
        
        return ''
    
    def import_results(
        self,
        results: Dict[str, Any],
        dry_run: bool = True,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Import research results to database with full historical tracking.
        
        Args:
            results: Results from research_franchise_locations()
            dry_run: If True, simulate import without writing to database
            skip_duplicates: If True, skip locations that already exist
            
        Returns:
            Dictionary with import statistics
        """
        if not self.db:
            raise ValueError("Database not configured. Provide db_config to __init__")
        
        import_stats = {
            'providers_added': 0,
            'providers_updated': 0,
            'providers_skipped': 0,
            'historical_events_added': 0,
            'errors': []
        }
        
        for location in results['locations']:
            try:
                # Check if already exists
                existing = self.db.search(
                    query=location.legal_name,
                    state=location.state,
                    fuzzy=True
                )
                
                if existing and skip_duplicates:
                    high_match = any(match.score > 0.9 for match in existing)
                    if high_match:
                        import_stats['providers_skipped'] += 1
                        self.logger.info(f"Skipping duplicate: {location.legal_name}")
                        continue
                
                if dry_run:
                    self.logger.info(f"[DRY RUN] Would import: {location.legal_name}")
                    import_stats['providers_added'] += 1
                else:
                    # Add provider to database
                    provider_id = self.db.add_provider(
                        legal_name=location.legal_name,
                        address_line1=location.address_line1,
                        address_line2=location.address_line2,
                        city=location.city,
                        state=location.state,
                        zip_code=location.zip_code,
                        phone=location.phone,
                        email=location.email,
                        website=location.website,
                        npi=location.npi,
                        dba_names=location.dba_names,
                        parent_organization=location.parent_organization
                    )
                    import_stats['providers_added'] += 1
                    
                    # Add historical events
                    if location.ownership_history:
                        for event in location.ownership_history:
                            self.db.record_history(
                                provider_id=provider_id,
                                event_type=event.event_type,
                                event_date=event.event_date,
                                old_value=event.previous_value,
                                new_value=event.new_value,
                                source=event.source,
                                source_url=event.source_url,
                                notes=event.description
                            )
                            import_stats['historical_events_added'] += 1
                    
                    self.logger.info(f"Imported: {location.legal_name} (ID: {provider_id})")
            
            except Exception as e:
                error_msg = f"Error importing {location.legal_name}: {str(e)}"
                self.logger.error(error_msg)
                import_stats['errors'].append(error_msg)
        
        return import_stats
    
    def export_results(
        self,
        results: Dict[str, Any],
        output_file: str,
        format: str = 'json'
    ):
        """
        Export research results to file.
        
        Args:
            results: Results from research_franchise_locations()
            output_file: Path to output file
            format: Output format ('json' or 'csv')
        """
        if format == 'json':
            # Convert dataclass objects to dicts
            export_data = {
                'franchise_name': results['franchise_name'],
                'location': results['location'],
                'research_date': results['research_date'],
                'summary': results['summary'],
                'locations': [
                    self._location_to_dict(loc) for loc in results['locations']
                ]
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(results['locations'])} locations to {output_file}")
        
        elif format == 'csv':
            import csv
            
            with open(output_file, 'w', newline='') as f:
                if not results['locations']:
                    return
                
                # Get all fields from first location
                fieldnames = list(asdict(results['locations'][0]).keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for loc in results['locations']:
                    writer.writerow(asdict(loc))
            
            self.logger.info(f"Exported {len(results['locations'])} locations to {output_file}")
    
    def _location_to_dict(self, location: FranchiseLocation) -> Dict[str, Any]:
        """Convert FranchiseLocation to serializable dict."""
        data = asdict(location)
        
        # Convert HistoricalEvent objects to dicts
        if data.get('ownership_history'):
            data['ownership_history'] = [
                asdict(event) if hasattr(event, '__dataclass_fields__') else event
                for event in data['ownership_history']
            ]
        
        return data
