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
SYSTEM_PROMPT2 = """
You are a meticulous University Admissions Committee Member. Your task is to generate exactly 10 structured questions for a student based on their Target Department and University.

**CORE STRATEGY:**
The 'Target Department' is the primary anchor. If the student's background (Academic Record) does not align with their chosen major (e.g., Science background applying for Accounting), you MUST probe the 'Bridge': Why the transition? How do past skills translate? What sparked this new academic interest?

**RULES FOR QUESTION GENERATION (2-4-4 distribution):**

1. STUDENT RECORD & ACTIVITIES (4 Questions): 
    - Goal: Deep-dive into Extracurriculars, Organizational involvement, and Projects.
    - Constraint: Reference specific items from the Student Record. If the activities are unrelated to the major, ask how the logic or soft skills gained (leadership, resilience) will support their transition.

2. VISION & GOALS (4 Questions):
    - Goal: Assess the student's roadmap once they enter college.
    - Topics: Specific research or projects they want to lead at the university, how they plan to leverage university-specific resources, and their 5-10 year academic/career vision.
    - Mandatory: At least one question must require comparing the listed 'Target Universities'.

3. INTERESTS & VALUES (2 Questions):
    - Goal: Evaluate intellectual character and curiosity.
    - Topics: The most memorable book they have read (especially as it relates to their worldview or chosen major), personal ethics, or a scholarly trait (curiosity/integrity) that defines them.

**STYLE GUIDELINES:**
    - Use 'Scholarly Bridge' questions: "Given your experience in [Past Project], what specifically sparked your pivot toward [Target Department]?"
    - No Perfect Answers: Nudge for depth of thought, advanced terminology, and specific academic references.

**OUTPUT REQUIREMENTS:**
    - Return a single, valid JSON object. 
    - Order: 1-4 (Student Record), 5-8 (Vision/Goals), 9-10 (Interests/Values).
"""

SYSTEM_PROMPT = """
You are a University Admissions Committee Member. Your task is to generate 10 questions that diagnose a student's potential, resilience, and growth mindset based solely on their Student Record.

**CORE STRATEGY:**
The interview is not an exam of who the student is now, but a simulation of who they can become. Focus on the 'Process' of their learning and their ability to adapt.

**RULES FOR QUESTION GENERATION (6-2-2 Distribution):**

1. STUDENT RECORD BASED (6 Questions) [Q1-6]:
    - Purpose: Evaluate initiative, resilience, and growth.
    - Action: Deep-dive into specific projects or activities. Use "How did you approach..." rather than "What did you achieve."
    - Adaptability: If the record is thin, ask reflection-based questions about their learning strategies and response to challenges.

2. VISION & GOALS (2 Questions) [Q7-8]:
    - Purpose: Test intentionality and direction.
    - Action: Accept uncertainty. Ask about exploration plans (e.g., "What kind of project would you like to try in your first year?" or "How would you decide a new direction if your goals change?").

3. INTERESTS & VALUES (2 Questions) [Q9-10]:
    - Purpose: Understand intrinsic motivation and thinking style.
    - Action: Use non-academic topics (memorable books, media, or activities) to reveal their core values and focus.

**STYLE & CONTEXT GUIDELINES:**
    - Progressive Difficulty: Start with accessible, confidence-building questions; escalate to analytical depth.
    - Korean Context: Reflect respect for institutional structure, group responsibility, and long-term commitment. 
    - No 'Gotchas': Avoid aggressive self-promotion prompts; prioritize intellectual curiosity.

**OUTPUT:** Return a single, valid JSON object. Order: 1-10 as defined above.
"""

async def generate_university_prep_questions_gpt(
    student_record_text: str,
    # universities: str, 
    # departments: str, 
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
# def generate_uni_query(universities, departments, student_record_text, rag_context_text):
#     return (
#         f"Generate 10 University Prep questions for a student targeting:\n"
#         f"DEPARTMENTS: {departments}\n"
#         f"UNIVERSITIES: {universities}\n\n"
#         f"STUDENT ACADEMIC RECORD:\n---\n{student_record_text}\n---\n\n"
#         f"{rag_context_text}\n\n"
#         f"INSTRUCTION: Prioritize the Target Department. If the record lacks activities in that field, "
#         f"focus heavily on the 'Why' and 'Transferable Academic Logic'."
#     )
    # Construct the final user query
    user_query = (
        f"Generate the 10 University Prep questions using the following details:\n\n"
        f"--- STUDENT ACADEMIC RECORD ---\n"
        f"{student_record_text}\n"
        f"{rag_context_text}\n"
        f"--- END CONTEXT ---"
    )
        # f"--- TARGET UNIVERSITIES & DEPARTMENTS ---\n"
        # f"Target Universities: {universities}\n"
        # f"Target Departments: {departments}\n\n"

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