import os
import json
import time
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# NOTE: Importing core models from the existing schema file
from app.schemas.interview_session import GeneratedQuestion
from app.core.config import settings

# --- Internal LLM Output Wrapper (Required for schema validation) ---
class UniversityQuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the Gemini API for academic questions."""
    questions: List[GeneratedQuestion]

# --- Configuration (using same model for consistency) ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL_TEMPLATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key="
API_KEY = settings.GEMINI_API_KEY 

# --- Detailed System Prompt for University Prep (UPDATED) ---
SYSTEM_PROMPT = """
You are a highly experienced and meticulous University Admissions Committee Member. 
Your sole task is to generate exactly 10 structured interview questions for a candidate based on their academic record, 
**specifically focusing on their choice of preferred universities and departments.**

RULES FOR QUESTION GENERATION:
1. Total Questions: Exactly 10 questions.
2. Structure: 
    - **Questions 1-5 (University-Specific):** MUST be motivational, personalized, and focused on fit. These must reference the candidate's student record (coursework, projects, grades) and directly connect them to the specific research, curriculum, or reputation of the Preferred University and Department (e.g., 'Why do you want to study Law at Cambridge?', 'How will your specific project on X contribute to our department's focus on Y?').
    - **Questions 6-10 (General Admission):** MUST be general questions testing academic readiness, problem-solving, and critical thinking. These should cover: general academic goals, reaction to academic challenge, ethical scenarios relevant to their field, or broad conceptual questions to assess foundational knowledge and intellectual curiosity.
3. Flow: Questions must flow naturally, starting with specific motivation (Q1-Q5) and moving to general academic readiness probes (Q6-Q10).
4. Output: The response MUST be a single, valid JSON object matching the provided schema. The 'question_order' must be 1 to 10.
"""

def get_academic_question_generation_schema() -> Dict[str, Any]:
    """
    Creates the response schema based on the internal UniversityQuestionGenerationResponse model, 
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
                "description": "A list containing exactly 10 academic interview questions.",
                "items": {
                    "type": "OBJECT",
                    "properties": item_properties,
                    "required": item_required
                }
            }
        },
        "required": ["questions"]
    }
    
    return schema_definition


async def generate_university_prep_questions(
    student_record_text: str,
    universities: str, # Comma-separated list of universities
    departments: str, # Comma-separated list of departments
    # Placeholder for RAG if you implement one for academic papers/research
    reference_questions: Optional[List[str]] = None
) -> List[GeneratedQuestion]:
    """
    Calls the Gemini API to generate structured academic interview questions based on 
    the student record, preferred universities, and departments.
    """
    if not API_KEY:
        raise Exception("API Key is missing. Ensure settings.GEMINI_API_KEY is configured.")

    response_schema = get_academic_question_generation_schema()

    # Incorporate academic context into the User Query
    rag_context_text = f"Preferred Universities: {universities}\nPreferred Departments: {departments}\n\n"
    if reference_questions:
        rag_context_joined = "\n- ".join(reference_questions)
        rag_context_text += f"REFERENCE QUESTIONS (Use these for topic and style guidance, but do not repeat them exactly in your final output): - {rag_context_joined}\n"
    
    print("rag context:" + rag_context_text)

    # Incorporate all inputs into the user query
    user_query = (
        f"Generate the 10 University Prep questions using the following details:\n"
        f"--- TARGETS ---\n{rag_context_text}"
        f"--- STUDENT RECORD ---\n{student_record_text}\n---"
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
            
            # Critical type check (like the one we fixed earlier)
            if not isinstance(parsed_json, dict):
                raise TypeError(f"LLM Response Error: Expected a single JSON object (dict), but received type: {type(parsed_json).__name__}. Raw parsed content: {parsed_json}")

            # Use the new response model for validation
            validated_response = UniversityQuestionGenerationResponse(**parsed_json)
            
            if len(validated_response.questions) != 10:
                print(f"Warning: AI returned {len(validated_response.questions)} questions, expected 10.")
                
            return validated_response.questions

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError, json.JSONDecodeError, TypeError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 400:
                    print(f"\n--- FATAL 400 ERROR DETAIL ---")
                    print(e.response.text)
                    print("------------------------------\n")
                raise Exception(f"Failed to generate university prep questions after {max_retries} attempts. Last Error: {e}")