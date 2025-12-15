import os
import json
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel
# Note: httpx and asyncio are no longer needed for API calls/retries
from google import genai
from google.genai import types
from google.genai.errors import APIError

# NOTE: Importing core models from the existing schema file
from app.schemas.interview_session import GeneratedQuestion
from app.core.config import settings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - U_Q_GEN - %(message)s')

# --- Internal LLM Output Wrapper (Required for schema validation) ---
class UniversityQuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the Gemini API for academic questions."""
    questions: List[GeneratedQuestion]

# --- Configuration (using same model for consistency) ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# --- Deferred Client Initialization ---
# We use a global variable to hold the initialized asynchronous client
global_client = None

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
    Returns the JSON schema dictionary generated from the Pydantic model. 
    (Kept for consistency and potential debug printing, but the main function passes the Pydantic class.)
    """
    schema_definition = UniversityQuestionGenerationResponse.model_json_schema()
    
    print("\n--- DEBUG: Generated Schema Sent to Gemini API ---")
    print(json.dumps(schema_definition, indent=2))
    print("--------------------------------------------------\n")
    
    return schema_definition


async def generate_university_prep_questions(
    student_record_text: str,
    universities: str, # Comma-separated list of universities
    departments: str, # Comma-separated list of departments
    reference_questions: Optional[List[str]] = None
) -> List[GeneratedQuestion]:
    """
    Calls the Gemini API using the official SDK (Client.aio) to generate 
    structured academic interview questions.
    """
    global global_client 
    
    # 1. Initialize the Native Async Client lazily (on first call)
    if global_client is None:
        try:
            # FIX: Initialize the synchronous Client, then access the async interface via .aio
            sync_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            global_client = sync_client.aio
            logging.info("Gemini Native Async Client (.aio) successfully initialized.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize Gemini client: {e}")
            raise Exception("Gemini API Client initialization failed.")

    if global_client is None:
         raise Exception("Gemini API Client failed to initialize after attempt.")

    # Execute debug print of schema
    get_academic_question_generation_schema()

    # 2. Incorporate context into the User Query
    rag_context_text = f"Preferred Universities: {universities}\nPreferred Departments: {departments}\n\n"
    if reference_questions:
        rag_context_joined = "\n- ".join(reference_questions)
        rag_context_text += f"REFERENCE QUESTIONS (Use these for topic and style guidance, but do not repeat them exactly in your final output): - {rag_context_joined}\n"
    
    print("rag context:" + rag_context_text)

    # Construct the final user query
    user_query = (
        f"Generate the 10 University Prep questions using the following details:\n"
        f"--- TARGETS ---\n{rag_context_text}"
        f"--- STUDENT RECORD ---\n{student_record_text}\n---"
    )
    
    # 3. Define the generation configuration using SDK types
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        # Pass the Pydantic class directly for simplified schema definition
        response_schema=UniversityQuestionGenerationResponse, 
        temperature=0.7 
    )

    try:
        # 4. Make the single, native asynchronous API call. SDK handles retries/backoff.
        response = await global_client.models.generate_content(
            model=MODEL_NAME,
            contents=[user_query], 
            config=config
        )

        # 5. Response Parsing and Validation
        
        # The SDK response object contains the text property which holds the JSON string
        if not response.text:
            raise ValueError("Gemini returned an empty text response.")

        json_text = response.text.strip()
        
        # No need for manual sanitization, but keep robust JSON parsing
        parsed_json = json.loads(json_text)
        
        # Validate against the Pydantic model
        validated_response = UniversityQuestionGenerationResponse(**parsed_json)
            
        if len(validated_response.questions) != 10:
            logging.warning(f"AI returned {len(validated_response.questions)} questions, expected 10.")
            
        return validated_response.questions

    except APIError as e:
        # Catches persistent API errors (400, 429, etc.) after internal retries fail.
        logging.error(f"Gemini API Error (after retries): {e}")
        if hasattr(e, 'response') and e.response is not None:
             logging.error(f"Full response detail: {e.response.text}") 
        raise Exception(f"Failed to generate university prep questions due to persistent API error: {e}")
    except (ValueError, json.JSONDecodeError, TypeError) as e:
        # Catches JSON parsing or Pydantic validation errors
        logging.error(f"Failed to parse AI response into structured JSON: {e}")
        raise Exception(f"Failed to generate university prep questions due to response parsing error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise Exception(f"An unexpected error occurred during generation: {e}")