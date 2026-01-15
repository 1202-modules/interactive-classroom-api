"""Query parameters utilities for API endpoints."""
from typing import Optional, Set, Dict, Any
from pydantic import BaseModel


def parse_fields(fields_param: Optional[str]) -> Optional[Set[str]]:
    """
    Parse fields query parameter.
    
    Args:
        fields_param: Comma-separated list of field names (e.g., "id,name,status")
    
    Returns:
        Set of field names to include, or None if all fields should be returned
    """
    if not fields_param:
        return None
    
    # Split by comma and strip whitespace
    fields = {field.strip() for field in fields_param.split(',') if field.strip()}
    
    return fields if fields else None


def filter_response_fields(
    response_data: Dict[str, Any],
    fields: Optional[Set[str]]
) -> Dict[str, Any]:
    """
    Filter response dictionary to include only specified fields.
    
    Args:
        response_data: Response data as dictionary
        fields: Set of field names to include, or None for all fields
    
    Returns:
        Filtered response dictionary
    """
    if not fields:
        return response_data
    
    # Filter to include only specified fields
    filtered = {key: value for key, value in response_data.items() if key in fields}
    
    return filtered


def filter_model_response(
    model_instance: BaseModel,
    fields: Optional[Set[str]]
) -> Dict[str, Any]:
    """
    Filter Pydantic model response to include only specified fields.
    
    Args:
        model_instance: Pydantic model instance
        fields: Set of field names to include, or None for all fields
    
    Returns:
        Filtered response dictionary
    """
    # Convert model to dict
    response_dict = model_instance.model_dump()
    
    # Filter if fields specified
    if fields:
        response_dict = filter_response_fields(response_dict, fields)
    
    return response_dict


def filter_list_response(
    items: list,
    fields: Optional[Set[str]]
) -> list:
    """
    Filter list of model responses to include only specified fields.
    
    Args:
        items: List of Pydantic model instances or dictionaries
        fields: Set of field names to include, or None for all fields
    
    Returns:
        List of filtered response dictionaries
    """
    if not fields:
        # Convert all items to dicts if they're models
        return [
            item.model_dump() if isinstance(item, BaseModel) else item
            for item in items
        ]
    
    # Filter each item
    filtered_items = []
    for item in items:
        if isinstance(item, BaseModel):
            item_dict = item.model_dump()
        else:
            item_dict = item
        
        filtered_dict = filter_response_fields(item_dict, fields)
        filtered_items.append(filtered_dict)
    
    return filtered_items

