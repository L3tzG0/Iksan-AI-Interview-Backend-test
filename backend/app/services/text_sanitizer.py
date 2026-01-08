import re
from typing import List
from app.schemas.interview_session import QuestionAnswerPair 

# Refined Regex: This pattern targets all ASCII control characters (0-31) 
# EXCEPT for standard, JSON-safe whitespace: horizontal tab (0x09, \t), 
# line feed (0x0a, \n), and carriage return (0x0d, \r).
# It also includes high-range non-printable characters (0x7f-0x9f).
# This prevents 'Invalid control character' errors while preserving essential formatting.
CONTROL_CHAR_REGEX = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')

def sanitize_json_string(text: str) -> str:
    """
    Removes strictly illegal, unescaped JSON control characters from a string.
    This preserves standard line breaks (\n, \r) and tabs (\t).
    """
    if not isinstance(text, str):
        return str(text)
    
    # 1. Strip illegal control characters
    sanitized_text = CONTROL_CHAR_REGEX.sub('', text)
    
    # 2. Normalize and strip non-breaking spaces (U+00A0) - common culprit from word processors
    sanitized_text = sanitized_text.replace('\xa0', ' ')
    
    return sanitized_text

def sanitize_qa_pairs(qa_pairs: List[QuestionAnswerPair]) -> List[QuestionAnswerPair]:
    """
    Applies sanitization to the answer_text field of each QuestionAnswerPair, 
    preserving the structure and returning a list of new, clean Pydantic objects.
    """
    sanitized_pairs = []
    for pair in qa_pairs:
        # Sanitize only the answer_text
        sanitized_answer = sanitize_json_string(pair.answer_text)
        
        # Create a new, sanitized instance
        sanitized_pair = pair.model_copy(update={'answer_text': sanitized_answer})
        sanitized_pairs.append(sanitized_pair)

    print("test")
    return sanitized_pairs