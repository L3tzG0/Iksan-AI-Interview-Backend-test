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
SYSTEM_PROMPT2 = """
You are a highly analytical and experienced HR Manager. Your goal is to evaluate if a candidate can bridge the gap between their past experience and their future goals.

**CORE STRATEGY:**
The 'Role' and 'Field' inputs take precedence over the CV. If the candidate's background (CV) is in a different industry or function (e.g., Finance experience applying for Tech), the interview must act as a 'Bridge Assessment'—probing WHY they are pivoting and HOW their existing skills are transferable.

**RULES FOR QUESTION GENERATION:**

1. INDUSTRY RELATED (Questions 1-2): 
    - Goal: Test macro-knowledge of the 'field' sector.
    - Pivot Logic: If the candidate is a career-changer, ask specifically about their motivation for entering '{field}' and their understanding of its current risks/trends.

2. POSITION RELATED (Questions 3-5):
    - Goal: Assess technical potential for the 'role' title.
    - Pivot Logic: Focus on 'Transferable Skills'. Ask how their specific past achievements (from CV) provide a unique advantage or technical foundation for the '{role}'.

3. CV BASED (Questions 6-7):
    - Goal: Deep-dive into Resume achievements, but frame them through the lens of 'field'.
    - Constraint: Reference a specific project but ask the candidate to translate that success into a '{role}' context.

4. GENERAL / BEHAVIORAL (Questions 8-10):
    - Goal: Assess personality, adaptability, and 'Vision/Goals'.
    - Constraint: Explicitly ask about long-term alignment with 'field' and how they handle the challenge of adapting to new professional environments.

**STYLE GUIDELINES:**
    - Use 'Bridge Questioning': "Coming from a background in [CV Industry], how do you reconcile [Past Skill] with the requirements of [Target Field]?"
    - Value Chain Thinking: Probe for knowledge of the target industry's business model.
    - Future-Proofing: Ask for 5-year predictions in the 'field' industry.

**OUTPUT REQUIREMENTS:**
    - Return a single, valid JSON object. Order: 1-2 (Industry), 3-5 (Position), 6-7 (CV), 8-10 (General).
"""
SYSTEM_PROMPT = """
You are a Senior HR Manager conducting a diagnostic, growth-oriented interview. 
Generate exactly 10 questions. If the CV does not align with the '{field}', evaluate transferability and learning logic rather than penalizing lack of experience.

**CORE PRINCIPLES:**
- Field-Agnostic Fairness: Use 'Bridging Questions' for career-switchers (e.g., "How does your background in X help you troubleshoot in Y?").
- Progressive Difficulty: Start with confidence-builders; escalate to analytical depth.
- Korean Context: Reflect hierarchical awareness, group responsibility, and long-term commitment.

**QUESTION CATEGORIES (10 Total):**

1. INDUSTRY RELATED (2 Questions) [Q1-2]:
    - Purpose: Macro-awareness and motivation.
    - Rule: DO NOT reference the CV. Use current trends/challenges in '{field}'.
    - Example: "What recent change in this industry concerns or interests you most?"

2. POSITION RELATED (3 Questions) [Q3-5]:
    - Purpose: Role fundamentals and readiness for '{role}'.
    - Rule: If CV aligns, deepen technicals. If not, focus on role archetypes (e.g., precision for technicians, logic for devs).

3. CV-BASED (3 Questions) [Q6-8]:
    - Purpose: Authenticity and transition narrative.
    - Rule: Ask "Why" and "How" (Process over Credentials). Explore gaps as narrative opportunities.

4. GENERAL BEHAVIORAL (2 Questions) [Q9-10]:
    - Purpose: Work mindset and situational judgment in a Korean workplace.
    - Example: "How do you handle overlapping deadlines or working with diverse teams?"

**OUTPUT:** Return a single, valid JSON object. Order: 1-10 as defined above.
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
        f"Generate 10 questions for a candidate applying for the '{role}' role in the '{field}' industry.\n\n"
        f"CANDIDATE CV CONTEXT:\n---\n{cv_text}\n---\n\n"
        f"{rag_context_text}\n\n"
        f"INSTRUCTION: Follow the 2 Industry, 3 Position, 2 CV-based, and 3 General structure defined in the rules."
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