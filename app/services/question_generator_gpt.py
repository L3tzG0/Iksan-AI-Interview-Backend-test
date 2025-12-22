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
SYSTEM_PROMPT_EN = """
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
    - **MANDATORY PIVOT CHECK**: If the CV does not align with the '{field}', at least one question MUST explicitly ask: "Why do you want to enter this field despite the gap between your previous experience and this role?" Focus on the internal motivation for crossing fields.

4. GENERAL BEHAVIORAL (2 Questions) [Q9-10]:
    - Purpose: Work mindset and situational judgment in a Korean workplace.
    - Example: "How do you handle overlapping deadlines or working with diverse teams?"

**OUTPUT:** Return a single, valid JSON object. Order: 1-10 as defined above.
"""

SYSTEM_PROMPT = """
귀하는 진단적이고 성장 지향적인 면접을 진행하는 시니어 HR 관리자입니다.
정확히 10개의 질문을 생성하십시오. 만약 지원자의 CV가 '{field}'와 일치하지 않는 경우, 경험 부족을 지적하기보다는 전이 가능성과 학습 논리를 평가하십시오.

**핵심 원칙:**

* 산업 불문 공정성: 커리어 전환자를 위해 '가교 질문(Bridging Questions)'을 사용하십시오 (예: "X 분야에서의 배경이 Y 분야의 문제를 해결하는 데 어떻게 도움이 되겠습니까?").
* 점진적 난이도: 자신감을 높여주는 질문으로 시작하여 점차 분석적 깊이가 필요한 질문으로 확대하십시오.
* 한국적 맥락 반영: 조직 내 위계 질서에 대한 이해, 집단 책임감, 그리고 장기적 헌신도를 반영하십시오.

**질문 카테고리 (총 10개):**

1. 산업 관련 (2개 질문) [Q1-2]:
    - 목적: 거시적 인식 및 지원 동기 파악.
    - 규칙: CV를 참조하지 마십시오. '{field}' 분야의 최신 트렌드나 과제를 활용하십시오.
    - 예시: "이 산업에서 최근 발생한 변화 중 귀하가 가장 우려하거나 흥미롭게 지켜보는 점은 무엇입니까?"

2. 직무 관련 (3개 질문) [Q3-5]:
    - 목적: 직무 기본 역량 및 '{role}' 역할에 대한 준비도 평가.
    - 규칙: CV가 직무와 일치하면 기술적 심화 질문을 던지십시오. 일치하지 않는다면 해당 직무의 원형(예: 기술직의 정밀함, 개발자의 논리력 등)에 집중하십시오.

3. CV 기반 (3개 질문) [Q6-8]:
    - 목적: 경험의 진정성 및 커리어 전환 서사 확인.
    - 규칙: "왜"와 "어떻게"를 질문하십시오 (단순 자격 증명보다 과정 중심). 경력상의 공백이나 차이를 지원자의 서술 기회로 활용하십시오.
    - **필수 피벗 체크 (MANDATORY PIVOT CHECK)**: 만약 지원자의 CV가 '{field}' 분야와 일치하지 않는 경우, 최소한 한 개의 질문은 반드시 다음과 같이 명시적으로 질문해야 합니다: "이전의 경험과 본 직무 사이의 간극에도 불구하고, 왜 이 분야에 진입하고자 하십니까?" 이 질문을 통해 분야를 전환하려는 지원자의 내적 동기와 진정성에 집중하십시오.
    
4. 일반 행동 기반 (2개 질문) [Q9-10]:
    -  목적: 한국적 업무 환경에서의 마인드셋 및 상황 판단력 평가.
    - 예시: "업무 마감 기한이 겹치거나 다양한 성향의 팀원들과 협업해야 할 때 어떻게 대처하십니까?"

**출력:** 단일하고 유효한 JSON 객체를 반환하십시오. 순서는 위에 정의된 대로 1번부터 10번까지입니다.
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
        rag_context_text = f"참조 질문 (주제 및 스타일 가이드용으로 사용하되, 그대로 반복하지 마십시오: - {rag_context_joined}"
        # rag_context_text = f"REFERENCE QUESTIONS (Use these for topic and style guidance, but do not repeat them exactly): - {rag_context_joined}"
    

    user_query = (
        f"'{field}' 산업의 '{role}' 직무에 지원하는 후보자를 위한 10개의 질문을 생성하십시오.\n\n"
        f"후보자 CV 문맥:\n---\n{cv_text}\n---\n\n"
        f"{rag_context_text}\n\n"
        f"지침: 규칙에 정의된 산업 2개, 직무 3개, CV 기반 2개, 일반 3개 구조를 따르십시오."
    )
    # user_query = (
    #     f"Generate 10 questions for a candidate applying for the '{role}' role in the '{field}' industry.\n\n"
    #     f"CANDIDATE CV CONTEXT:\n---\n{cv_text}\n---\n\n"
    #     f"{rag_context_text}\n\n"
    #     f"INSTRUCTION: Follow the 2 Industry, 3 Position, 2 CV-based, and 3 General structure defined in the rules."
    # )

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