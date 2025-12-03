import os
import json
import time
import httpx
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel

# NOTE: Importing core models from the existing schema file
from app.schemas.interview_session import GeneratedQuestion, QuestionGenerationRequest
from app.core.config import settings

# --- Internal LLM Output Wrapper (Required for schema validation) ---
# This model represents the direct JSON output structure from Gemini's API
class QuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the Gemini API for Call 1."""
    questions: List[GeneratedQuestion]

# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL_TEMPLATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key="
API_KEY = settings.GEMINI_API_KEY 

# --- Detailed System Prompt ---
SYSTEM_PROMPT = """
You are a highly analytical and experienced HR Manager conducting a preliminary interview screening. 
Your task is to generate exactly 10 structured interview questions for the candidate based on their provided CV/introduction text, 
**specifically focusing on the target role and field provided.**

RULES FOR QUESTION GENERATION:
1. Total Questions: Exactly 10 questions.
2. Structure: 
    - Questions 1-5 MUST be general, behavioral, or soft-skill based (e.g., Vision/Goals, Organizational Adaptability, Creativity, Problem Solving). These should be broad to assess personality and fit.
    - Questions 6-10 MUST be specific, highly personalized, and resume-based. These must reference specific projects, internships, technologies, or achievements explicitly mentioned in the candidate's CV, and should relate them to the specified target role and field.
3. Flow: Questions must flow naturally, starting broad (Q1-Q5) and moving to detailed technical/experience probes (Q6-Q10).
4. Output: The response MUST be a single, valid JSON object matching the provided schema. The 'question_order' must be 1 to 10.
"""

def get_question_generation_schema() -> Dict[str, Any]:
    """
    Creates the response schema based on the internal QuestionGenerationResponse model, 
    ensuring it is structured correctly for the Gemini API.
    """
    # 1. Get the JSON schema for the GeneratedQuestion (the array item)
    item_schema = GeneratedQuestion.model_json_schema()
    
    # Extract the properties needed for the 'items' part of the array
    item_properties = item_schema.get('properties', {})
    item_required = item_schema.get('required', [])

    # 2. Construct the final, compliant response schema manually
    schema_definition = {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "description": "A list containing exactly 10 interview questions.",
                "items": {
                    "type": "OBJECT",
                    "properties": item_properties,
                    "required": item_required
                }
            }
        },
        "required": ["questions"]
    }
    
    print("\n--- DEBUG: Generated Schema Sent to Gemini API ---")
    print(json.dumps(schema_definition, indent=2))
    print("--------------------------------------------------\n")
    
    return schema_definition


async def generate_interview_questions(cv_text: str, field: str, role: str) -> List[GeneratedQuestion]:
    """
    Calls the Gemini API to generate structured interview questions based on CV text, 
    guided by the target field and role.
    Implements exponential backoff for resilience.
    """
    if not API_KEY:
        raise Exception("API Key is missing. Ensure settings.GEMINI_API_KEY is configured.")

    # Get the correctly structured schema
    response_schema = get_question_generation_schema()

    # Incorporate field and role into the user query
    user_query = (
        f"Generate the 10 questions for a candidate applying for the '{role}' role "
        f"in the '{field}' industry. Use the following student background as context:\n\n---\n{cv_text}\n---"
    )
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
            "temperature": 0.7 
        },
    }

    headers = {'Content-Type': 'application/json'}
    api_url = API_URL_TEMPLATE + API_KEY 
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status() 
            
            result = response.json()
            
            candidate = result.get('candidates', [{}])[0]
            json_text = candidate.get('content', {}).get('parts', [{}])[0].get('text')
            
            if not json_text:
                raise ValueError("Gemini returned empty or malformed text response.")
            
            # Sanitization for common LLM output formats
            if json_text.strip().startswith('```') and json_text.strip().endswith('```'):
                json_text = json_text.strip().strip('`').lstrip('json').strip()
            
            parsed_json = json.loads(json_text)
            # Use QuestionGenerationResponse for validation
            validated_response = QuestionGenerationResponse(**parsed_json)
            
            if len(validated_response.questions) != 10:
                print(f"Warning: AI returned {len(validated_response.questions)} questions, expected 10.")
                
            return validated_response.questions

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 400:
                    print(f"\n--- FATAL 400 ERROR DETAIL ---")
                    print(e.response.text)
                    print("------------------------------\n")
                raise Exception(f"Failed to generate questions after {max_retries} attempts. Last Error: {e}")