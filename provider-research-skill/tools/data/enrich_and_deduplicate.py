#!/usr/bin/env python3
"""
Provider Data Enrichment and Deduplication
===========================================

Processes existing provider data to:
1. Use web researcher to fill missing information
2. Separate healthcare providers from real estate companies
3. Deduplicate providers at the same address
4. Consolidate related entities into proper fields

Usage:
    python3 enrich_and_deduplicate.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from provider_research.search.web_researcher import ProviderWebResearcher
from provider_research.database.manager import ProviderDatabaseManager


class ProviderEnrichmentPipeline:
    """Pipeline for enriching and deduplicating provider data."""
    
    def __init__(self, db_state_path: str = None):
        """Initialize the enrichment pipeline."""
        self.db_state_path = db_state_path or Path(__file__).parent / "data" / "db_state.json"
        self.researcher = ProviderWebResearcher(use_real_scraping=False)  # Use simulation mode
        self.providers = []
        self.healthcare_providers = []
        self.real_estate_companies = []
        
    def load_data(self):
        """Load provider data from db_state.json."""
        print(f"\n📂 Loading data from {self.db_state_path}")
        with open(self.db_state_path, 'r') as f:
            data = json.load(f)
            self.providers = data.get('providers', [])
        print(f"✅ Loaded {len(self.providers)} providers")
        return self
    
    def classify_providers(self):
        """Separate healthcare providers from real estate companies."""
        print("\n🏥 Classifying providers...")
        
        for provider in self.providers:
            provider_type = (provider.get('provider_type') or '').lower()
            legal_name = (provider.get('legal_name') or '').lower()
            raw_data = provider.get('raw_search_data', {}) or {}
            
            # Check if this is a real estate company
            is_real_estate = (
                'reit' in provider_type or
                'real estate' in provider_type or
                'reit' in legal_name or
                'property' in provider_type.lower() or
                raw_data.get('property_type') is not None or
                raw_data.get('listing_status') is not None
            )
            
            if is_real_estate:
                self.real_estate_companies.append(provider)
                print(f"  🏢 Real Estate: {provider['legal_name']}")
            else:
                self.healthcare_providers.append(provider)
                print(f"  🏥 Healthcare: {provider['legal_name']}")
        
        print(f"\n✅ Classified: {len(self.healthcare_providers)} healthcare, {len(self.real_estate_companies)} real estate")
        return self
    
    def enrich_provider(self, provider: Dict) -> Dict:
        """Use web researcher to fill missing information."""
        print(f"\n🔍 Enriching: {provider['legal_name']}")
        
        # Skip if all critical fields are filled
        has_npi = provider.get('npi') is not None
        has_full_address = all([
            provider.get('address_street'),
            provider.get('address_zip')
        ])
        has_contact = all([
            provider.get('phone'),
            provider.get('email')
        ])
        
        if has_npi and has_full_address and has_contact:
            print(f"  ✓ Already complete, skipping")
            return provider
        
        # Research the provider
        try:
            location = f"{provider.get('address_city', '')}, {provider.get('address_state', '')}"
            result = self.researcher.research(
                provider_name=provider['legal_name'],
                location=location
            )
            
            # Merge research results
            if result.locations:
                first_location = result.locations[0]
                
                # Fill missing fields
                if not provider.get('address_street') and first_location.get('address'):
                    provider['address_street'] = first_location['address']
                    print(f"  + Added address_street: {first_location['address']}")
                
                if not provider.get('address_zip') and first_location.get('zip'):
                    provider['address_zip'] = first_location['zip']
                    print(f"  + Added address_zip: {first_location['zip']}")
                
                if not provider.get('phone') and first_location.get('phone'):
                    provider['phone'] = first_location['phone']
                    print(f"  + Added phone: {first_location['phone']}")
                
                if not provider.get('email') and first_location.get('email'):
                    provider['email'] = first_location['email']
                    print(f"  + Added email: {first_location['email']}")
                
                if not provider.get('location_website') and first_location.get('website'):
                    provider['location_website'] = first_location['website']
                    print(f"  + Added website: {first_location['website']}")
                
                if not provider.get('npi') and first_location.get('npi'):
                    provider['npi'] = first_location['npi']
                    print(f"  + Added NPI: {first_location['npi']}")
                
                # Check for real estate owner
                if first_location.get('real_estate_owner'):
                    provider['real_estate_owner'] = first_location['real_estate_owner']
                    print(f"  + Added real estate owner: {first_location['real_estate_owner']}")
            
            # Add NPI data if found
            if result.npi_records:
                first_npi = result.npi_records[0]
                if not provider.get('npi'):
                    provider['npi'] = first_npi.get('npi')
                    provider['npi_taxonomy_code'] = first_npi.get('taxonomy_code')
                    provider['npi_taxonomy_desc'] = first_npi.get('taxonomy_description')
                    print(f"  + Added NPI data from registry")
            
        except Exception as e:
            print(f"  ⚠️  Research failed: {e}")
        
        return provider
    
    def enrich_all(self):
        """Enrich all healthcare providers."""
        print("\n📈 Enriching all healthcare providers...")
        
        enriched = []
        for provider in self.healthcare_providers:
            enriched_provider = self.enrich_provider(provider)
            enriched.append(enriched_provider)
        
        self.healthcare_providers = enriched
        print(f"\n✅ Enrichment complete")
        return self
    
    def group_by_address(self) -> Dict[str, List[Dict]]:
        """Group providers by normalized address."""
        groups = defaultdict(list)
        
        for provider in self.healthcare_providers:
            # Normalize address for comparison
            street = provider.get('address_street', '') or provider.get('address_full', '')
            city = provider.get('address_city', '')
            state = provider.get('address_state', '')
            
            # Create normalized key (ignore suite numbers)
            import re
            street_normalized = re.sub(r',?\s*(suite|ste|unit|#)\s*\d+', '', street, flags=re.IGNORECASE)
            address_key = f"{street_normalized.strip().lower()}|{city.lower()}|{state.upper()}"
            
            groups[address_key].append(provider)
        
        return groups
    
    def deduplicate(self):
        """Deduplicate providers at the same address."""
        print("\n🔄 Deduplicating providers...")
        
        address_groups = self.group_by_address()
        deduplicated = []
        
        for address_key, providers_at_address in address_groups.items():
            if len(providers_at_address) == 1:
                # No duplicates at this address
                deduplicated.append(providers_at_address[0])
                continue
            
            print(f"\n  📍 Found {len(providers_at_address)} providers at same address:")
            for p in providers_at_address:
                print(f"     - {p['legal_name']} (Phone: {p.get('phone', 'N/A')})")
            
            # Check if they should be merged (same phone or related entities)
            should_merge = self._should_merge_providers(providers_at_address)
            
            if not should_merge:
                print(f"  ⚠️  Different phone numbers - keeping as separate providers")
                deduplicated.extend(providers_at_address)
                continue
            
            # Determine the best primary record
            primary = self._select_primary_provider(providers_at_address)
            print(f"  ✓ Primary: {primary['legal_name']}")
            
            # Consolidate others into primary
            for other in providers_at_address:
                if other['id'] == primary['id']:
                    continue
                
                print(f"  → Merging: {other['legal_name']}")
                primary = self._merge_provider(primary, other)
            
            deduplicated.append(primary)
        
        self.healthcare_providers = deduplicated
        print(f"\n✅ Deduplication complete: {len(deduplicated)} unique providers")
        return self
    
    def _should_merge_providers(self, providers: List[Dict]) -> bool:
        """Determine if providers at same address should be merged."""
        # Get all unique phone numbers (excluding None)
        phones = set(p.get('phone') for p in providers if p.get('phone'))
        
        # If different phone numbers, don't merge (likely different businesses)
        if len(phones) > 1:
            return False
        
        # If same phone number, they're likely the same entity
        if len(phones) == 1:
            return True
        
        # If no phone numbers, check parent organizations
        parents = set(p.get('parent_organization') for p in providers if p.get('parent_organization'))
        
        # If same parent, might be related (franchising + location)
        if len(parents) == 1:
            return True
        
        # Default to not merging if uncertain
        return False
    
    def _select_primary_provider(self, providers: List[Dict]) -> Dict:
        """Select the best provider record to use as primary."""
        # Score each provider
        scored = []
        for provider in providers:
            score = 0
            
            # Prefer records with more complete data
            if provider.get('npi'):
                score += 10
            if provider.get('phone'):
                score += 5
            if provider.get('email'):
                score += 5
            if provider.get('location_website'):
                score += 5
            if provider.get('franchise_id'):
                score += 3
            
            # Prefer operational names over franchising/parent companies
            name = provider['legal_name'].lower()
            if 'franchising' in name or 'franchise' in name:
                score -= 20
            if 'inc' in name or 'llc' in name or 'corp' in name:
                score -= 5
            
            # Prefer names with location identifiers
            if ' of ' in name:
                score += 10
            
            scored.append((score, provider))
        
        # Return highest scoring provider
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]
    
    def _merge_provider(self, primary: Dict, other: Dict) -> Dict:
        """Merge another provider record into the primary."""
        # Add to DBAs if different name
        if other['legal_name'] != primary['legal_name']:
            if other['legal_name'] not in primary.get('dba_names', []):
                if not primary.get('dba_names'):
                    primary['dba_names'] = []
                primary['dba_names'].append(other['legal_name'])
        
        # Determine relationship and add to appropriate field
        other_name_lower = other['legal_name'].lower()
        
        if 'franchising' in other_name_lower or 'franchise' in other_name_lower:
            # This is the parent franchising company
            if not primary.get('parent_organization'):
                primary['parent_organization'] = other['legal_name']
        elif 'reit' in other_name_lower or 'properties' in other_name_lower:
            # This is a real estate company
            if not primary.get('real_estate_owner'):
                primary['real_estate_owner'] = other['legal_name']
        
        # Merge phone numbers if different
        if other.get('phone') and other['phone'] != primary.get('phone'):
            # Could add to alternative contacts in the future
            pass
        
        # Fill any missing fields from other record
        for field in ['npi', 'email', 'fax', 'location_website', 'franchise_id']:
            if not primary.get(field) and other.get(field):
                primary[field] = other[field]
        
        return primary
    
    def save_results(self, output_path: str = None):
        """Save the cleaned and enriched data."""
        if output_path is None:
            output_path = Path(__file__).parent / "data" / "db_state_cleaned.json"
        
        print(f"\n💾 Saving results to {output_path}")
        
        # Prepare output data
        output = {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "stats": {
                "total_providers": len(self.healthcare_providers),
                "real_estate_companies_removed": len(self.real_estate_companies),
                "states_covered": len(set(p.get('address_state') for p in self.healthcare_providers if p.get('address_state'))),
                "with_npi": sum(1 for p in self.healthcare_providers if p.get('npi')),
                "avg_confidence": None
            },
            "providers": self.healthcare_providers,
            "real_estate_companies": self.real_estate_companies  # Keep for reference
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"✅ Saved:")
        print(f"   - {len(self.healthcare_providers)} healthcare providers")
        print(f"   - {len(self.real_estate_companies)} real estate companies (separate)")
        
        return self
    
    def run(self):
        """Run the complete enrichment pipeline."""
        print("="*80)
        print("PROVIDER DATA ENRICHMENT & DEDUPLICATION PIPELINE")
        print("="*80)
        
        (self
            .load_data()
            .classify_providers()
            .enrich_all()
            .deduplicate()
            .save_results())
        
        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETE")
        print("="*80)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"   Original providers: {len(self.providers)}")
        print(f"   Healthcare providers: {len(self.healthcare_providers)}")
        print(f"   Real estate companies: {len(self.real_estate_companies)}")
        print(f"   Final cleaned records: {len(self.healthcare_providers)}")
        
        # Show sample of cleaned data
        print("\n📋 Sample cleaned provider:")
        if self.healthcare_providers:
            sample = self.healthcare_providers[0]
            print(f"   Name: {sample.get('legal_name')}")
            print(f"   DBAs: {sample.get('dba_names', [])}")
            print(f"   Parent: {sample.get('parent_organization')}")
            print(f"   Real Estate Owner: {sample.get('real_estate_owner')}")
            print(f"   Address: {sample.get('address_full')}")
            print(f"   Phone: {sample.get('phone')}")
            print(f"   NPI: {sample.get('npi')}")


def main():
    """Main entry point."""
    pipeline = ProviderEnrichmentPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
