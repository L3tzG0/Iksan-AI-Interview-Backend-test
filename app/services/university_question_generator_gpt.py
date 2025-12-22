import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.schemas.interview_session import GeneratedQuestion
from app.core.config import settings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - U_Q_GEN_GPT5 - %(message)s')

# --- Internal LLM Output Wrapper ---
class UniversityQuestionGenerationResponse(BaseModel):
    """The complete JSON structure expected from the GPT-4o API for academic questions."""
    questions: List[GeneratedQuestion]

# --- Configuration ---
# MODEL_NAME = "openai/gpt-5"
MODEL_NAME = "openai/gpt-4o"

# --- Deferred Client Initialization ---
global_client: Optional[AsyncOpenAI] = None

# --- Detailed System Prompt for University Prep ---
SYSTEM_PROMPT = """
You are a highly experienced and meticulous University Admissions Committee Member who has thoroughly researched the candidate and the targeted institutions. 
Your sole task is to generate exactly 10 structured interview questions for a candidate based on their academic record, 
specifically focusing on their choice of preferred universities and departments.

RULES FOR QUESTION GENERATION:
1. Total Questions: Exactly 10 questions.
2. Structure: 
    - Questions 1-5 (Deeply University-Specific): MUST be motivational, highly personalized, and focused on fit. These must act as a deep dive, referencing the candidate's student record (coursework, projects, grades) and directly connecting them to the specific research, academic challenges, or publicly known focus areas of the Preferred University and Department.
    - MANDATORY: You MUST include at least one question that requires the candidate to compare or contrast two or more of the listed institutions/departments, or to justify their preference or ranking.
    - Questions 6-10 (General Academic/Intellectual): MUST be general questions testing academic readiness, problem-solving, and critical thinking. These should cover: general academic goals, reaction to academic challenge, ethical scenarios relevant to their field, or broad conceptual questions to assess foundational knowledge and intellectual curiosity.
3. Flow: Questions must flow naturally, starting with specific motivation (Q1-Q5) and moving to general academic readiness probes (Q6-Q10).
4. Output: The response MUST be a single, valid JSON object matching the provided schema. The 'question_order' must be 1 to 10.
"""

async def generate_university_prep_questions_gpt(
    student_record_text: str,
    universities: str, 
    departments: str, 
    reference_questions: Optional[List[str]] = None
) -> List[GeneratedQuestion]:
    """
    Calls the GPT-4o Proxy API to generate structured academic interview questions.
    """
    global global_client 
    
    if global_client is None:
        try:
            global_client = AsyncOpenAI(
                base_url=f"{settings.GPT_API_BASE_URL}/v1",
                api_key=settings.ELICE_API_KEY
            )
            logging.info("GPT-4o Async Client for University Prep successfully initialized.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize GPT-4o client: {e}")
            raise Exception("GPT-4o API Client initialization failed.")

    # Incorporate RAG context
    rag_context_text = ""
    if reference_questions:
        rag_context_joined = "\n- ".join(reference_questions)
        rag_context_text += (
            f"\n\n--- REFERENCE QUESTIONS (RAG Result) ---\n"
            f"Use these retrieved questions for topic and style guidance, but DO NOT repeat them exactly in your final output. "
            f"Use them to inspire *new*, unique, and tailored questions:\n"
            f"- {rag_context_joined}"
        )

    # Construct the final user query
    user_query = (
        f"Generate the 10 University Prep questions using the following details:\n\n"
        f"--- TARGET UNIVERSITIES & DEPARTMENTS ---\n"
        f"Target Universities: {universities}\n"
        f"Target Departments: {departments}\n\n"
        f"--- STUDENT ACADEMIC RECORD ---\n"
        f"{student_record_text}\n"
        f"{rag_context_text}\n"
        f"--- END CONTEXT ---"
    )

    try:
        # Temperature removed for proxy compatibility
        response = await global_client.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            response_format=UniversityQuestionGenerationResponse
        )

        validated_response = response.choices[0].message.parsed
        
        if not validated_response or len(validated_response.questions) != 10:
            count = len(validated_response.questions) if validated_response else 0
            logging.warning(f"GPT-4o returned {count} academic questions, expected 10.")
            
        return validated_response.questions if validated_response else []

    except Exception as e:
        logging.error(f"GPT-4o Academic Generation Error: {e}")
        raise Exception(f"Failed to generate university prep questions via GPT-4o: {e}")