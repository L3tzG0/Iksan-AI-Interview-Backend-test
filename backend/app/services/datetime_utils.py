import re
from typing import Optional

def pad_microseconds(timestamp_str: Optional[str]) -> Optional[str]:
    """
    Pads the fractional second component of an ISO 8601 string to 6 digits (microseconds) 
    to satisfy strict Pydantic/Python datetime parsing.
    
    Example: '2025-12-12T10:04:17.78192+00:00' -> '2025-12-12T10:04:17.781920+00:00'
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        return timestamp_str
    
    # Regex to find the fractional seconds part, if it exists, followed by timezone info or end of string.
    # We look for a decimal point followed by one or more digits (\.\d+).
    match = re.search(r'(\.\d+)(.*)', timestamp_str)
    
    if match:
        fractional_part = match.group(1) # e.g., ".78192"
        rest_of_string = match.group(2)  # e.g., "+00:00"
        
        # Check if padding is needed (length is period + 6 digits = 7)
        if len(fractional_part) < 7:
            # Calculate zeros needed (7 - current length)
            padding_needed = 7 - len(fractional_part)
            padded_fractional_part = fractional_part + '0' * padding_needed
            
            # Reconstruct the string
            return timestamp_str.replace(fractional_part + rest_of_string, padded_fractional_part + rest_of_string)

    return timestamp_str