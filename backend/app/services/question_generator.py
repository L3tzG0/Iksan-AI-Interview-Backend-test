import os
import json
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.schemas.interview_session import GeneratedQuestion
from app.core.config import settings # Assuming this provides a fully loaded API key


# --- Setup Logging ---
# You can set up logging here if needed, or rely on your worker's logging configuration.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Q_GEN - %(message)s')

# --- Internal LLM Output Wrapper ---
class QuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the Gemini API."""
    questions: List[GeneratedQuestion]

# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# --- Deferred Client Initialization ---
# We use a global variable, but we initialize it to None
# The initialization logic is now inside the function, where `settings.GEMINI_API_KEY` is safer to access.
global_client = None


# --- Detailed System Prompt (Unchanged) ---
SYSTEM_PROMPT = """
You are a highly analytical and experienced HR Manager conducting a preliminary interview screening. 
Your task is to generate exactly 10 structured interview questions for the candidate based on their provided CV/introduction text, 
**specifically focusing on the target role and field provided.**

RULES FOR QUESTION GENERATION:
1. Total Questions: Exactly 10 questions.
2. Structure: 
    - Questions 1-5 MUST be general, behavioral, or soft-skill based (e.g., Vision/Goals, Organizational Adaptability, Creativity, Problem Solving). These should be broad to assess personality and fit.
    - Questions 6-10 MUST be a deep dive into the candidate's experience. These questions MUST be specific, highly personalized, and resume-based. These must reference specific projects, internships, technologies, or achievements explicitly mentioned in the candidate's CV, and should relate them to the specified target role and field.
3. Flow: Questions must flow naturally, starting broad (Q1-5) and moving to detailed technical/experience probes (Q6-10).
4. Output: The response MUST be a single, valid JSON object matching the provided schema. The 'question_order' must be 1 to 10.
"""

def get_question_generation_schema() -> Dict[str, Any]:
    """
    Creates the response schema dictionary from the Pydantic model and prints the debug output.
    """
    schema_definition = QuestionGenerationResponse.model_json_schema()
    
    print("\n--- DEBUG: Generated Schema Sent to Gemini API ---")
    print(json.dumps(schema_definition, indent=2))
    print("--------------------------------------------------\n")
    
    return schema_definition


async def generate_interview_questions(
        cv_text: str,
        field: str,
        role: str,
        reference_questions: Optional[List[str]] = None
) -> List[GeneratedQuestion]:
    """
    Calls the Gemini API using the official SDK (AsyncClient) to generate 
    structured interview questions.
    """
    # Use the global declaration to modify the global variable
    global global_client 
    
    # Initialize the client lazily (on first call)
    if global_client is None:
        try:
            # Initialize the synchronous Client, then immediately access the 
            # asynchronous interface via the .aio property. This gives us the 
            # fully non-blocking client we need.
            sync_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            global_client = sync_client.aio
            
            logging.info("Gemini Native Async Client (.aio) successfully initialized.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize Gemini client: {e}")
            raise Exception("Gemini API Client initialization failed.")

    if global_client is None:
         raise Exception("Gemini API Client failed to initialize after attempt.")


    # 1. Get and print the correctly structured schema (for debug)
    get_question_generation_schema() 
    
    # 2. Incorporate RAG context into the User Query (Unchanged logic)
    rag_context_text = ""
    if reference_questions:
        rag_context_joined = "\n- ".join(reference_questions)
        rag_context_text = f"REFERENCE QUESTIONS (Use these for topic and style guidance, but do not repeat them exactly in your final output): - {rag_context_joined}"
    
    print(f"RAG Context Text:\n{rag_context_text}\n")
    
    # 3. Construct the final user query (Unchanged logic)
    user_query = (
        f"Generate the 10 questions for a candidate applying for the '{role}' role "
        f"in the '{field}' industry. Use the following student background as context:\n\n---\n{cv_text}\n---\n"
        f"{rag_context_text}"
    )

    # 4. Define the generation configuration using SDK types
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=QuestionGenerationResponse, 
        temperature=0.7 
    )

    try:
        # 5. Make the single, clean API call using the guaranteed-initialized client
        response = await global_client.models.generate_content( # <-- using global_client
            model=MODEL_NAME,
            contents=[user_query], 
            config=config
        )

        # 6. Response Parsing and Validation
        if not response.text:
            raise ValueError("Gemini returned an empty text response.")

        json_text = response.text.strip()
        
        parsed_json = json.loads(json_text)
        validated_response = QuestionGenerationResponse(**parsed_json)
            
        if len(validated_response.questions) != 10:
            print(f"Warning: AI returned {len(validated_response.questions)} questions, expected 10.")
            
        return validated_response.questions

    except APIError as e:
        # Catches persistent API errors (e.g., 400 Bad Request) after internal retries fail.
        logging.error(f"Gemini API Error (after retries): {e}")
        if hasattr(e, 'response') and e.response is not None:
             # Log the full response text if available for detailed error inspection
             logging.error(f"Full response detail: {e.response.text}") 
        raise Exception(f"Failed to generate questions due to persistent API error: {e}")
    except (ValueError, json.JSONDecodeError) as e:
        logging.error(f"Failed to parse AI response into structured JSON: {e}")
        raise Exception(f"Failed to generate questions due to response parsing error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise Exception(f"An unexpected error occurred during generation: {e}")