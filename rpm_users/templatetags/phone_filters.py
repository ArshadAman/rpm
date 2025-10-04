"""
Template filters for phone number formatting.
"""

from django import template
from ..utils import format_phone_for_display

register = template.Library()


@register.filter
def format_phone(phone_number):
    """
    Format phone number for display in templates.
    
    Args:
        phone_number: Phone number string
        
    Returns:
        Formatted phone number for display
    """
    return format_phone_for_display(phone_number)


@register.filter
def phone_with_country_code(phone_number):
    """
    Format phone number with country code for display.
    
    Args:
        phone_number: Phone number string
        
    Returns:
        Phone number with country code if it's a US number
    """
    if not phone_number:
        return "No phone"
    
    # If it's a US number without country code, add +1
    cleaned = phone_number.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+1{cleaned}"
    
    return format_phone_for_display(phone_number)
