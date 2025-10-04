"""
Utility functions for RPM users app.
"""

import re
import logging

logger = logging.getLogger('rpm_users.utils')


def clean_phone_number(phone_number: str) -> str:
    """
    Clean and standardize phone number format.
    
    Args:
        phone_number: Raw phone number string
        
    Returns:
        Cleaned phone number string in standard format
        
    Examples:
        "559-733-9756" -> "+15597339756"
        "(661) 392-7166" -> "+16613927166"
        "2106294509" -> "+12106294509"
        "+916304848105" -> "+916304848105"
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # If it starts with +, keep it as international
    if cleaned.startswith('+'):
        return cleaned
    else:
        # Handle domestic numbers
        if len(cleaned) == 10:
            # 10-digit US number: 1234567890 -> +11234567890
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            # 11-digit US number with country code: 11234567890 -> +11234567890
            return f"+{cleaned}"
        else:
            # For other lengths, assume it's international and needs country code
            if len(cleaned) >= 10:
                # Don't add +1 for international numbers, just add +
                return f"+{cleaned}"
            return cleaned
    
    return cleaned


def format_phone_for_display(phone_number: str) -> str:
    """
    Format phone number for display purposes.
    
    Args:
        phone_number: Phone number string
        
    Returns:
        Formatted phone number for display
    """
    if not phone_number:
        return "No phone"
    
    cleaned = clean_phone_number(phone_number)
    return cleaned


def get_phone_for_api(phone_number: str) -> str:
    """
    Get phone number in format suitable for API calls (E.164 format).
    
    Args:
        phone_number: Phone number string (may already be cleaned/formatted)
        
    Returns:
        Phone number in E.164 format (e.g., +15551234567)
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters except +
    digits_only = re.sub(r'[^\d+]', '', phone_number)
    
    # If it already starts with +, return as is (already in E.164 format)
    if digits_only.startswith('+'):
        return digits_only
    
    # Handle US numbers (10 digits) - add country code
    if len(digits_only) == 10:
        return f"+1{digits_only}"
    # Handle numbers with country code (11+ digits)
    elif len(digits_only) >= 11:
        # If it starts with 1 and has 11 digits, it's likely US with country code
        if digits_only.startswith('1') and len(digits_only) == 11:
            return f"+{digits_only}"
        else:
            # For other international numbers, assume they already include country code
            return f"+{digits_only}"
    
    return digits_only
