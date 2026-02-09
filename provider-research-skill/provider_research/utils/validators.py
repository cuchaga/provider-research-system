"""Validation utilities for provider data."""

import re
from typing import Optional
from ..exceptions import ValidationError


def validate_npi(npi: str) -> bool:
    """
    Validate NPI (National Provider Identifier).
    
    NPI must be exactly 10 digits.
    
    Args:
        npi: NPI string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If NPI is invalid
    """
    if not npi:
        raise ValidationError("NPI cannot be empty")
    
    # Remove any non-digit characters
    npi_clean = re.sub(r'\D', '', npi)
    
    if len(npi_clean) != 10:
        raise ValidationError(f"NPI must be exactly 10 digits, got {len(npi_clean)}")
    
    return True


def validate_phone(phone: str) -> bool:
    """
    Validate phone number.
    
    Accepts various formats:
    - (555) 123-4567
    - 555-123-4567
    - 5551234567
    
    Args:
        phone: Phone number string
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If phone is invalid
    """
    if not phone:
        raise ValidationError("Phone number cannot be empty")
    
    # Remove all non-digit characters
    phone_clean = re.sub(r'\D', '', phone)
    
    # Must be 10 or 11 digits (with or without country code)
    if len(phone_clean) not in [10, 11]:
        raise ValidationError(f"Phone must be 10-11 digits, got {len(phone_clean)}")
    
    return True


def validate_state(state: str) -> bool:
    """
    Validate US state abbreviation.
    
    Args:
        state: Two-letter state code
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If state is invalid
    """
    valid_states = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
    }
    
    if not state:
        raise ValidationError("State cannot be empty")
    
    state_upper = state.upper()
    
    if len(state_upper) != 2:
        raise ValidationError(f"State must be 2 characters, got {len(state_upper)}")
    
    if state_upper not in valid_states:
        raise ValidationError(f"Invalid state code: {state}")
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address.
    
    Args:
        email: Email address string
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    # Simple email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return True


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate ZIP code.
    
    Accepts:
    - 5 digit: 12345
    - ZIP+4: 12345-6789
    
    Args:
        zip_code: ZIP code string
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If ZIP code is invalid
    """
    if not zip_code:
        raise ValidationError("ZIP code cannot be empty")
    
    # Remove spaces
    zip_clean = zip_code.replace(' ', '')
    
    # Check formats
    if re.match(r'^\d{5}$', zip_clean):
        return True
    elif re.match(r'^\d{5}-\d{4}$', zip_clean):
        return True
    else:
        raise ValidationError(f"Invalid ZIP code format: {zip_code}")
