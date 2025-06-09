"""String manipulation utility functions."""

import re
from typing import Optional, List, Dict, Any
import json


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def safe_string(value: Any, default: str = "") -> str:
    """Safely convert any value to string."""
    if value is None:
        return default
    
    try:
        return str(value)
    except Exception:
        return default


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text (collapse multiple spaces, strip)."""
    return re.sub(r'\s+', ' ', text.strip())


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


def format_bytes(bytes_value: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string, returning default on error."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def mask_sensitive_data(text: str, patterns: Optional[List[str]] = None) -> str:
    """Mask sensitive data in text using regex patterns."""
    if patterns is None:
        patterns = [
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Credit card numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        ]
    
    masked_text = text
    for pattern in patterns:
        masked_text = re.sub(pattern, '***MASKED***', masked_text)
    
    return masked_text


def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate URL-friendly slug from text."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', text.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    return truncate_string(slug, max_length, suffix="")


def parse_key_value_pairs(text: str, delimiter: str = '=', separator: str = ',') -> Dict[str, str]:
    """Parse key=value pairs from text."""
    result = {}
    
    if not text.strip():
        return result
    
    pairs = text.split(separator)
    for pair in pairs:
        if delimiter in pair:
            key, value = pair.split(delimiter, 1)
            result[key.strip()] = value.strip()
    
    return result
