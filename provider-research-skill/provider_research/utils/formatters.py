"""Output formatting utilities."""

from typing import Dict, List, Any
import json


def format_provider(provider: Dict[str, Any], verbose: bool = False) -> str:
    """
    Format provider data for display.
    
    Args:
        provider: Provider dictionary
        verbose: Include all fields if True
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Header
    legal_name = provider.get('legal_name', 'Unknown')
    lines.append(f"Provider: {legal_name}")
    lines.append("=" * 60)
    
    # Basic info
    if 'npi' in provider:
        lines.append(f"NPI: {provider['npi']}")
    
    # Address
    if 'address_full' in provider:
        lines.append(f"Address: {provider['address_full']}")
    elif 'address_city' in provider and 'address_state' in provider:
        lines.append(f"Location: {provider['address_city']}, {provider['address_state']}")
    
    # Contact
    if 'phone' in provider:
        lines.append(f"Phone: {provider['phone']}")
    if 'email' in provider:
        lines.append(f"Email: {provider['email']}")
    
    # Organization
    if 'parent_organization' in provider:
        lines.append(f"Parent Org: {provider['parent_organization']}")
    
    if 'provider_type' in provider:
        lines.append(f"Type: {provider['provider_type']}")
    
    # Verbose mode - show everything
    if verbose:
        lines.append("\nAdditional Information:")
        lines.append("-" * 60)
        
        for key, value in provider.items():
            if key not in ['legal_name', 'npi', 'address_full', 'address_city', 
                          'address_state', 'phone', 'email', 'parent_organization', 
                          'provider_type', 'raw_search_data', 'raw_npi_data']:
                if value and value != 'null':
                    lines.append(f"{key}: {value}")
    
    return "\n".join(lines)


def format_address(provider: Dict[str, Any]) -> str:
    """
    Format address from provider data.
    
    Args:
        provider: Provider dictionary
        
    Returns:
        Formatted address string
    """
    if 'address_full' in provider:
        return provider['address_full']
    
    parts = []
    
    if 'address_street' in provider:
        parts.append(provider['address_street'])
    
    city_state_zip = []
    if 'address_city' in provider:
        city_state_zip.append(provider['address_city'])
    if 'address_state' in provider:
        city_state_zip.append(provider['address_state'])
    if 'address_zip' in provider:
        city_state_zip.append(provider['address_zip'])
    
    if city_state_zip:
        parts.append(', '.join(city_state_zip))
    
    return ', '.join(parts) if parts else 'Address not available'


def format_search_results(results: List[Dict[str, Any]], 
                          show_scores: bool = True,
                          max_results: int = None) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of search result dictionaries
        show_scores: Show match scores if available
        max_results: Limit number of results displayed
        
    Returns:
        Formatted string
    """
    if not results:
        return "No results found"
    
    display_results = results[:max_results] if max_results else results
    
    lines = []
    lines.append(f"\nFound {len(results)} result(s)")
    if max_results and len(results) > max_results:
        lines.append(f"(Showing first {max_results})")
    lines.append("=" * 80)
    
    for i, result in enumerate(display_results, 1):
        lines.append(f"\n{i}. {result.get('legal_name', 'Unknown')}")
        
        # Match score
        if show_scores and 'match_score' in result:
            score = result['match_score']
            lines.append(f"   Match: {score*100:.1f}%")
        
        # Location
        location = format_address(result)
        if location != 'Address not available':
            lines.append(f"   {location}")
        
        # Phone
        if 'phone' in result:
            lines.append(f"   Phone: {result['phone']}")
        
        # Parent org
        if 'parent_organization' in result:
            lines.append(f"   Parent: {result['parent_organization']}")
        
        lines.append("-" * 80)
    
    return "\n".join(lines)


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as pretty JSON.
    
    Args:
        data: Data to format
        indent: Indentation level
        
    Returns:
        JSON string
    """
    return json.dumps(data, indent=indent, default=str)


def format_table(data: List[Dict[str, Any]], columns: List[str] = None) -> str:
    """
    Format data as ASCII table.
    
    Args:
        data: List of dictionaries
        columns: Columns to include (None = all)
        
    Returns:
        ASCII table string
    """
    if not data:
        return "No data"
    
    # Determine columns
    if columns is None:
        columns = list(data[0].keys())
    
    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            value = str(row.get(col, ''))
            widths[col] = max(widths[col], len(value))
    
    # Build table
    lines = []
    
    # Header
    header = ' | '.join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append('-' * len(header))
    
    # Rows
    for row in data:
        line = ' | '.join(str(row.get(col, '')).ljust(widths[col]) for col in columns)
        lines.append(line)
    
    return '\n'.join(lines)
