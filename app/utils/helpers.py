"""Helper utilities for Customer Matching POC"""

import re
from typing import Optional, Dict, Any
from datetime import datetime


def normalize_phone(phone: str) -> str:
    """Normalize phone number by removing non-digit characters"""
    if not phone:
        return ""
    return re.sub(r'\D', '', phone)


def normalize_email(email: str) -> str:
    """Normalize email address by converting to lowercase"""
    if not email:
        return ""
    return email.strip().lower()


def normalize_company_name(name: str) -> str:
    """Normalize company name by removing common suffixes and converting to lowercase"""
    if not name:
        return ""
    
    # Remove common business suffixes
    suffixes = [
        r'\s+inc\.?$', r'\s+corp\.?$', r'\s+llc$', r'\s+ltd\.?$', 
        r'\s+limited$', r'\s+company$', r'\s+co\.?$'
    ]
    
    normalized = name.strip().lower()
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    return normalized.strip()


def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two text strings"""
    if not text1 or not text2:
        return 0.0
    
    # Simple Jaccard similarity
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union


def format_currency(amount: Optional[float]) -> str:
    """Format currency amount"""
    if amount is None:
        return ""
    return f"${amount:,.2f}"


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display"""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_customer_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate customer data and return validation errors"""
    errors = {}
    
    # Required fields
    if not data.get('company_name'):
        errors['company_name'] = "Company name is required"
    
    # Email validation
    if data.get('email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors['email'] = "Invalid email format"
    
    # Phone validation
    if data.get('phone'):
        phone_digits = re.sub(r'\D', '', data['phone'])
        if len(phone_digits) < 10:
            errors['phone'] = "Phone number must have at least 10 digits"
    
    # Revenue validation
    if data.get('annual_revenue') is not None:
        try:
            revenue = float(data['annual_revenue'])
            if revenue < 0:
                errors['annual_revenue'] = "Annual revenue cannot be negative"
        except (ValueError, TypeError):
            errors['annual_revenue'] = "Annual revenue must be a valid number"
    
    # Employee count validation
    if data.get('employee_count') is not None:
        try:
            count = int(data['employee_count'])
            if count < 0:
                errors['employee_count'] = "Employee count cannot be negative"
        except (ValueError, TypeError):
            errors['employee_count'] = "Employee count must be a valid integer"
    
    return errors


def sanitize_text(text: str) -> str:
    """Sanitize text input by removing potentially harmful characters"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit length
    if len(text) > 10000:
        text = text[:10000]
    
    return text.strip() 