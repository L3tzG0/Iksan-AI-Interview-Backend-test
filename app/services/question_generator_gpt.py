import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.schemas.interview_session import GeneratedQuestion
from app.core.config import settings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Q_GEN_GPT5 - %(message)s')

# --- Internal LLM Output Wrapper ---
class QuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the GPT-4o API."""
    questions: List[GeneratedQuestion]

# --- Configuration ---
# MODEL_NAME = "openai/gpt-5"
MODEL_NAME = "openai/gpt-4o"


# --- Deferred Client Initialization ---
global_client: Optional[AsyncOpenAI] = None

# --- Detailed System Prompt ---
SYSTEM_PROMPT = """
You are a highly analytical and experienced HR Manager conducting a preliminary interview screening. 
Your task is to generate exactly 10 structured interview questions for the candidate based on their provided CV/introduction text, 
specifically focusing on the target role and field provided.

RULES FOR QUESTION GENERATION:
1. Total Questions: Exactly 10 questions.
2. Structure: 
    - Questions 1-5 MUST be general, behavioral, or soft-skill based (e.g., Vision/Goals, Organizational Adaptability, Creativity, Problem Solving). These should be broad to assess personality and fit.
    - Questions 6-10 MUST be a deep dive into the candidate's experience. These questions MUST be specific, highly personalized, and resume-based. These must reference specific projects, internships, technologies, or achievements explicitly mentioned in the candidate's CV, and should relate them to the specified target role and field.
3. Flow: Questions must flow naturally, starting broad (Q1-5) and moving to detailed technical/experience probes (Q6-10).
4. Output: The response MUST be a single, valid JSON object matching the provided schema. The 'question_order' must be 1 to 10.
"""

async def generate_interview_questions_gpt(
        cv_text: str,
        field: str,
        role: str,
        reference_questions: Optional[List[str]] = None
) -> List[GeneratedQuestion]:
    """
    Calls the GPT-4o Proxy API using the OpenAI SDK to generate 
    structured interview questions.
    """
    global global_client 
    
    # Initialize the AsyncOpenAI client lazily
    if global_client is None:
        try:
            # Using your company's custom endpoint and API key
            global_client = AsyncOpenAI(
                base_url=f"{settings.GPT_API_BASE_URL}/v1",
                api_key=settings.ELICE_API_KEY
            )
            logging.info("GPT-4o Async Client successfully initialized.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize GPT-4o client: {e}")
            raise Exception("GPT-4o API Client initialization failed.")

    # Incorporate RAG context
    rag_context_text = ""
    if reference_questions:
        rag_context_joined = "\n- ".join(reference_questions)
        rag_context_text = f"REFERENCE QUESTIONS (Use these for topic and style guidance, but do not repeat them exactly): - {rag_context_joined}"
    
    user_query = (
        f"Generate the 10 questions for a candidate applying for the '{role}' role "
        f"in the '{field}' industry. Use the following student background as context:\n\n---\n{cv_text}\n---\n"
        f"{rag_context_text}"
    )

    try:
        # Use structured output parsing (Beta Parse) supported by the proxy
        response = await global_client.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            response_format=QuestionGenerationResponse
        )

        validated_response = response.choices[0].message.parsed
        
        if not validated_response or len(validated_response.questions) != 10:
            count = len(validated_response.questions) if validated_response else 0
            logging.warning(f"GPT-4o returned {count} questions, expected 10.")
            
        return validated_response.questions if validated_response else []

    except Exception as e:
        logging.error(f"GPT-4o API Error: {e}")
        raise Exception(f"Failed to generate questions via GPT-4o: {e}")