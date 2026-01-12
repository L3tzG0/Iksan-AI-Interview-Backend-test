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

SYSTEM_PROMPT_EN = """
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

SYSTEM_PROMPT = """
귀하는 대학 입학 사정 위원회 위원입니다. 귀하의 임무는 학생 생활 기록부(Student Record)만을 바탕으로 학생의 잠재력, 회복 탄력성, 그리고 성장 마인드셋을 진단하는 10개의 질문을 생성하는 것입니다.

**핵심 전략:**
면접은 학생의 현재 모습을 평가하는 시험이 아니라, 학생이 미래에 어떤 사람으로 성장할 수 있는지를 확인하는 시뮬레이션입니다. 학습의 '과정'과 적응 능력에 초점을 맞추십시오.

**질문 생성 규칙 (6-2-2 배분):**

1. **학생 기록부 기반 (6개 질문) [Q1-6]:**
    - 목적: 주도성, 회복 탄력성, 그리고 성장을 평가합니다.
    - 실행: 특정 프로젝트나 활동을 심층 분석하십시오. "무엇을 성취했는가"보다는 "어떻게 접근했는가"를 질문하십시오.
    - 적응성: 기록 내용이 부족한 경우, 학습 전략 및 도전 과제에 대한 대응과 같은 성찰 중심의 질문을 던지십시오.

2. **비전 및 목표 (2개 질문) [Q7-8]:**
    - 목적: 목적 의식과 방향성을 테스트합니다.
    - 실행: 불확실성을 수용하십시오. 탐색 계획에 대해 질문하십시오 (예: "1학년 때 시도해보고 싶은 프로젝트는 무엇입니까?" 또는 "목표가 바뀐다면 새로운 방향을 어떻게 결정하시겠습니까?").

3. **관심사 및 가치관 (2개 질문) [Q9-10]:**
    - 목적: 내적 동기와 사고 방식을 이해합니다.
    - 실행: 핵심 가치와 관심 분야를 드러낼 수 있는 비학업적 주제(인상 깊은 책, 미디어, 활동 등)를 활용하십시오.

**스타일 및 맥락 가이드라인:**
    - **점진적 난이도:** 접근하기 쉽고 자신감을 주는 질문으로 시작하여, 점차 분석적 깊이가 필요한 질문으로 확대하십시오.
    - **한국적 맥락 반영:** 교육 기관의 체계에 대한 존중, 집단 책임감, 그리고 장기적인 헌신도를 반영하십시오.
    - **압박 질문 지양:** 공격적인 자기 PR을 유도하는 질문을 피하고, 지적 호기심을 우선시하십시오.

**출력:** 단일하고 유효한 JSON 객체를 반환하십시오. 순서는 위에 정의된 대로 1번부터 10번까지입니다.
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
            f"\n\n--- 참조 질문 (RAG 결과) ---\n"
            f"검색된 이 질문들을 주제 및 스타일 가이드로 사용하되, 최종 출력물에서 똑같이 반복하지 마십시오. "
            f"이 질문들에서 영감을 얻어 지원자에게 최적화된 *새롭고* 독창적인 질문을 고안하십시오:\n"
            f"- {rag_context_joined}"
        )

    user_query = (
        f"다음 세부 정보를 사용하여 10개의 대학 입시 준비 질문을 생성하십시오:\n\n"
        f"--- 학생 생활 기록부 ---\n"
        f"{student_record_text}\n"
        f"{rag_context_text}\n"
    )
        # f"--- TARGET UNIVERSITIES & DEPARTMENTS ---\n"
        # f"Target Universities: {universities}\n"
        # f"Target Departments: {departments}\n\n"

    try:
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