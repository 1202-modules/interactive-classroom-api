"""Settings comparison and merging utilities."""
from typing import Dict, Any, Optional


def calculate_settings_diff(template: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively find differences between template and new settings.
    
    Returns dict with only changed/new values:
    - New keys not in template
    - Changed values (including nested)
    - Removed keys (if new dict doesn't have key from template) - NOT included
    
    Args:
        template: Template settings (workspace template)
        new: New settings to compare
    
    Returns:
        Dictionary with only differences
    """
    diff = {}
    all_keys = set(template.keys()) | set(new.keys())
    
    for key in all_keys:
        if key not in template:
            # New key in new settings
            diff[key] = new[key]
        elif key not in new:
            # Key removed - don't include (session uses template default)
            continue
        elif isinstance(template[key], dict) and isinstance(new[key], dict):
            # Recursive comparison for nested dicts
            nested_diff = calculate_settings_diff(template[key], new[key])
            if nested_diff:
                diff[key] = nested_diff
        elif template[key] != new[key]:
            # Value changed
            diff[key] = new[key]
    
    return diff


def merge_settings(template: Dict[str, Any], custom: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge template settings with custom overrides.
    
    Custom settings override template settings recursively.
    If custom is None or empty, returns template as-is.
    
    Args:
        template: Template settings (workspace template)
        custom: Custom settings overrides (can be None)
    
    Returns:
        Merged settings dictionary
    """
    if not custom:
        return template.copy() if template else {}
    
    merged = template.copy() if template else {}
    
    for key, value in custom.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursive merge for nested dicts
            merged[key] = merge_settings(merged[key], value)
        else:
            # Override with custom value
            merged[key] = value
    
    return merged

