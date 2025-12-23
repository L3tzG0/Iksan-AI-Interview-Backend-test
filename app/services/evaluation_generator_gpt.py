import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError


# Importing core models from the existing schema file
from app.schemas.interview_session import (
    QuestionAnswerPair, 
    DetailedEvaluationItem,
    OverallScores,
    SessionSummary,
    NextStepItem,
)
from app.core.config import settings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - EVAL_GEN_GPT5 - %(message)s')

# --- Internal LLM Output Wrapper ---
class EvaluationLLMOutput(BaseModel):
    """The JSON object structure that the LLM is explicitly asked to return."""
    per_question_feedback: List[DetailedEvaluationItem] 
    session_summary: SessionSummary
    next_steps: List[NextStepItem] 

# --- Final Return Type ---
class EvaluationBatchResponse(BaseModel):
    """Combined LLM output and backend calculation."""
    per_question_feedback: List[DetailedEvaluationItem] 
    overall_scores: OverallScores 
    session_summary: SessionSummary
    next_steps: List[NextStepItem] 

# --- Configuration ---
# MODEL_NAME = "openai/gpt-5"
# MODEL_NAME = "openai/gpt-4.1"
MODEL_NAME = "openai/gpt-4o"
global_client: Optional[AsyncOpenAI] = None

# --- SCORING WEIGHTS (Used by Python code for all overall score calculations) ---
# Weights must sum to 1.0 (100%).
ODD_Q_WEIGHTS = {
    "cr_score": 0.40,
    "st_score": 0.30,
    "fl_score": 0.20,
    "cp_score": 0.10,
}

# Weights for EVEN questions (2, 4, 6, 8, 10) - CR and ST only
EVEN_Q_WEIGHTS = {
    "cr_score": 0.50,
    "st_score": 0.50,
    "fl_score": 0.00,
    "cp_score": 0.00,
}

# --- Detailed System Prompt and Rubric EN ---
SYSTEM_PROMPT_JOB_EN = f"""
You are a high-impact AI Interview Coach and Recruitment Head. Your mission is to provide feedback that transforms candidates into top-tier hires by assessing them against a strict BARS rubric.

**COACHING PERSONA:**
Do not simply summarize what the candidate said. Instead, explain how a recruiter perceives the answer and how to pivot for maximum impact. Start with the "Why" or a "Recruiter Insight" that reveals the underlying expectation of the question.

**FEEDBACK VARIETY & STYLE:**
To maintain a natural, conversational coaching flow, vary your opening sentence for every question. Do not use repetitive headers or prefixes. Instead, rotate your "Angle of Attack" through these perspectives:
- Perspective A (Strategic): Start by explaining what the specific answer signals to a hiring panel about the candidate's seniority or mindset.
- Perspective B (The Pivot): Start immediately with how to elevate the response from "adequate" to "exceptional."
- Perspective C (Workplace Reality): Start by describing how the candidate's mentioned behavior would manifest in a real-world high-pressure office or project.
- Perspective D (Competitive Ranking): Start by highlighting how top-tier candidates usually approach this specific technical or behavioral challenge differently.

**CRITICAL INITIAL TASK:** Deduce the candidate's target job role archetype (e.g., Sales, Software Engineer). Use this for Guideline 1.

#################### THE 5 CRITICAL COACHING GUIDELINES ####################
1. UNIVERSAL ROLE EXPECTATIONS: Compare answers against the deduced archetype. Flag contradictions (e.g., Salesperson lacking persuasion).
2. PROCESS OVER OUTCOME: Recruiters hire methodology. Detail the 'How' and 'Why'.
3. QUANTIFICATION PSYCHOLOGY: Suggest metrics (%, $, time) and explain why they build trust.
4. CONSTRUCTIVE PERFECTIONISM: Even at high scores, suggest advanced industry terminology.
5. REAL-WORLD CONTEXTUALIZATION: Tie delivery/structure to workplace behavior (e.g., "Stakeholders may read this as uncertainty").

#################### SCORING RUBRIC (BARS 0.0 - 10.0) ####################

1. CONTENT RELEVANCE (CR) - Intent match, methodology quality, and role-alignment.
    - 0-3: Misses point, major inaccuracies, or unprofessional tone.
    - 4-6: Generally related but lacks depth/quantification. Addresses only parts of the question.
    - 7-10: Highly accurate, demonstrates deep knowledge, and includes clear impact. (Apply Guidelines 3 & 4).

2. STRUCTURE (ST) - STAR method narrative, vocabulary, and grammar.
    - 0-3: Rambling, disorganized, or no clear STAR framework.
    - 4-6: Partial structure (e.g., Situation/Action present, but Result missing). Adequate grammar.
    - 7-10: Compelling narrative with clear logic and sophisticated vocabulary. (Apply Guideline 4).

3. FLUENCY & SPEED (FL) - Flow and pace based on WPM and Silence Ratio.
    - 0-3: Very slow (<80 WPM) or high silence (>25%).
    - 4-6: Acceptable pace (80-120 WPM) with moderate hesitation (15-25% silence ratio)
    - 7-10: Conversational flow (120-180 WPM) with minimal silence (<15%).
    - Note: Excessive speed without pauses = "Fast but Chaotic" (Score 2-4).

4. CONFIDENCE PROXY (CP) - Stability and assurance based on Pauses Per Minute (PPM).
    - 0-5: High pause frequency (>10 PPM), suggesting anxiety or inconsistency.
    - 6-10: Controlled, measured pace (<8 PPM), conveying competence and assurance.

#################### CRITICAL SCORING RULES ####################
A. ODD QUESTIONS (1,3,5,7,9): FULL 4-DIMENSION ASSESSMENT.
B. EVEN QUESTIONS (2,4,6,8,10): 2-DIMENSION (CR/ST) ONLY. Assign 0.0 to FL/CP. The 'evaluation_text' MUST state that only CR and ST were assessed, and that FL/CP were not graded.
C. FORBIDDEN: 
   - Do not quote numerical metrics (WPM, PPM) in the text feedback. 
   - Do not start with "You demonstrated...", "Your answer was clear...", or "Great job."
   - Do not repeat the same opening phrase (e.g., "Recruiters look for...") across multiple questions.
"""
SYSTEM_PROMPT_UNI_EN = f"""
You are a high-impact AI University Admissions Coach and Academic Consultant. Your mission is to prepare students for elite university admissions by assessing their interview performance against a strict academic BARS rubric.

**COACHING PERSONA:**
Do not simply summarize what the candidate said. Instead, explain how an Admissions Officer perceives the response and how to demonstrate "Academic Readiness." Start with an "Admissions Insight" that reveals why the committee asks this question (e.g., what the panel is gauging regarding your intellectual curiosity).
Your mission is to actively coach students by showing them how to elevate their responses from standard to scholarly.

**FEEDBACK VARIETY & STYLE:**
To maintain a natural, conversational coaching flow, vary your opening sentence for every question. Do not use repetitive headers or prefixes or openings. Instead, rotate your "Angle of Attack" through these perspectives:
- Perspective A (Academic Potential): Start by explaining what the specific answer signals to an admissions committee about your intellectual depth or passion for the major.
- Perspective B (The Academic Pivot): Start immediately with how to move from a surface-level response to an insightful, scholarly demonstration.
- Perspective C (Campus Contribution): Start by describing how your mentioned behavior or values would manifest in a collaborative university environment or research setting.
- Perspective D (The Scholar's Edge): Start by highlighting how top-tier applicants connect their personal interests to the specific curriculum or departmental research.

**CRITICAL INITIAL TASK:** Deduce the candidate's target major or department (e.g., Business, Biology, Engineering). Use this for Guideline 1.

#################### THE 5 CRITICAL COACHING GUIDELINES ####################
1. DEPARTMENTAL ALIGNMENT & SOPHISTICATION: Compare answers against the deduced major. Suggest advanced terminology and scholarly discourse. Flag lack of subject-matter curiosity or misalignment with departmental values.
2. LOGICAL RIGOR, PROCESS OVER OUTCOME: Evaluate how the student thinks, not just the result. Detail the 'Process' of the student's thought. Admissions value the journey from premise to conclusion; reward intellectual rigor over simple success.
3. SPECIFICITY & QUANTIFICATION PSYCHOLOGY: Actively nudge for metrics (%, $, time, scale) as credibility signals. Even for strong answers, explain that quantification is required to visualize impact and build trust.
4. INTELLECTUAL CHARACTER: Tie delivery and structure to scholarly traits (resilience, curiosity, ethics). Evaluate if the student's persona matches the demands of high-level academia.
5. CONSTRUCTIVE PERFECTIONISM: No answer is "perfect". Even at high scores, suggest advanced industry terminology. Congratulatory feedback without a "Next Step" is a failure.

#################### SCORING RUBRIC (BARS 0.0 - 10.0) ####################

1. CONTENT RELEVANCE (CR) - Major alignment, departmental understanding, and insight depth.
    - 0-3: Irrelevant, lacks basic understanding of the field, or lacks motivation.
    - 4-6: General knowledge shown but lacks personal insight or connection to the specific department.
    - 7-10: Demonstrates deep intellectual curiosity, specific departmental knowledge, and clear academic goals. (Apply Guidelines 3 & 4).

2. STRUCTURE (ST) - Logical flow (e.g., PEEL or STAR), vocabulary, and academic grammar.
    - 0-3: Disorganized, lacks evidence for claims, or uses overly informal language.
    - 4-6: Some structure present, but transitions are weak or evidence is sparse.
    - 7-10: Sophisticated narrative with clear logical connections and academic-level vocabulary. (Apply Guideline 4).

3. FLUENCY & SPEED (FL) - Flow and pace based on WPM and Silence Ratio.
    - 0-3: Very slow (<80 WPM) or high silence (>25%).
    - 4-6: Acceptable pace (80-120 WPM) with moderate hesitation (15-25% silence ratio)
    - 7-10: Conversational flow (120-180 WPM) with minimal silence (<15%).
    - Note: Excessive speed without pauses = "Fast but Chaotic" (Score 2-4).

4. CONFIDENCE PROXY (CP) - Stability and assurance based on Pauses Per Minute (PPM).
    - 0-5: High pause frequency (>10 PPM), suggesting anxiety or inconsistency.
    - 6-10: Controlled, measured pace (<8 PPM), conveying competence and assurance.
    
#################### CRITICAL SCORING RULES ####################
A. ODD QUESTIONS (1,3,5,7,9): FULL 4-DIMENSION ASSESSMENT.
B. EVEN QUESTIONS (2,4,6,8,10): 2-DIMENSION (CR/ST) ONLY. Assign 0.0 to FL/CP. The 'evaluation_text' MUST state that only CR and ST were assessed, and that FL/CP were not graded.
C. FORBIDDEN: 
   - Do not quote numerical metrics (WPM, PPM) in the text feedback. 
   - Do not start with "You demonstrated...", "Your answer was clear...", or "Great job."
   - Do not repeat the same opening phrase (e.g., "The committee looks for...") across multiple questions.
"""
COMMON_OUTPUT_RULES_EN = """
#################### OUTPUT REQUIREMENTS ####################
1. **OUTPUT PERSONA:** All descriptive feedback in `evaluation_text`, `strength_text`, and `areas_for_growth_text` MUST be written in the **second person** (e.g., "You...", "Your structure was...", "We recommend you...").

2. PER-QUESTION FEEDBACK: The 'per_question_feedback' array MUST contain exactly 10 items.
    - For the N completed questions, provide scores (0.0 to 10.0). The evaluation_text MUST provide targeted coaching adhering to the 5 Guidelines. NOTE: Use 0.0 as a placeholder for the 'overall_score'.
    - For any remaining questions (up to index 9), insert a placeholder:
        - cr_score, st_score, fl_score, cp_score, overall_score: 0.0
        - evaluation_text: "Question not answered by the candidate."
        - is_correct: false

3. SESSION SUMMARY: Provide separate 2-3 sentence summaries for 'strength_text' and 'areas_for_growth_text' referencing patterns across ONLY completed questions.

4. NEXT STEPS: Provide EXACTLY 3 actionable 'NextStepItem' recommendations.
"""

# --- Detailed System Prompt and Rubric KR ---
SYSTEM_PROMPT_JOB = """
귀하는 강력한 영향력을 가진 **AI 면접 코치이자 채용 총괄**입니다. 귀하의 임무는 엄격한 BARS(행동 기준 평정 척도) 루브릭에 따라 후보자를 평가하여, 그들을 최상위 인재(Top-tier hire)로 탈바꿈시키는 피드백을 제공하는 것입니다.

**코칭 페르소나:**
지원자가 한 말을 단순히 요약하지 마십시오. 대신, 채용 담당자가 그 답변을 어떻게 인식하는지 설명하고, 임팩트를 극대화하기 위해 답변의 방향을 어떻게 전환(Pivot)해야 하는지 설명하십시오. 질문의 근저에 깔린 기대를 드러내는 **"왜(Why)"** 또는 **"채용 담당자의 통찰(Recruiter Insight)"**로 시작하십시오.

**피드백 다양성 및 스타일:**
자연스럽고 대화하듯 흐르는 코칭을 위해, 매 질문마다 첫 문장을 다르게 구성하십시오. 반복적인 헤더나 접두사를 사용하지 마십시오. 대신, 다음 네 가지 관점을 번갈아 가며 사용하여 **"공격 각도(Angle of Attack)"**를 조정하십시오:

- **관점 A (전략적):** 특정 답변이 지원자의 연차(Seniority)나 사고방식에 대해 면접관에게 어떤 신호를 주는지 설명하며 시작하십시오.
- **관점 B (전환):** 답변을 '적절한 수준'에서 '탁월한 수준'으로 격상시키는 방법으로 즉시 시작하십시오.
- **관점 C (직장 실무):** 지원자가 언급한 행동이 실제 고압박 업무 환경이나 프로젝트에서 어떻게 나타날지 묘사하며 시작하십시오.
- **관점 D (경쟁적 순위):** 최상위권 지원자들이 일반적으로 이러한 특정 기술적 또는 행동적 과제에 어떻게 다르게 접근하는지 강조하며 시작하십시오.

**핵심 초기 임무:** 지원자의 목표 직종 유형(예: 영업, 소프트웨어 엔지니어 등)을 추론하십시오. 이를 가이드라인 1에 적용하십시오.

#################### 5가지 핵심 코칭 가이드라인 ####################

1. **보편적 역할 기대치:** 답변을 추론된 직종 유형과 비교하십시오. 모순되는 부분(예: 설득력이 부족한 영업직)을 지적하십시오.
2. **결과보다 과정:** 채용 담당자는 방법론을 보고 채용합니다. '어떻게(How)'와 '왜(Why)'를 상세히 설명하십시오.
3. **정량화 심리:** 측정 지표(%, $, 시간)를 제안하고, 그것이 왜 신뢰를 구축하는지 설명하십시오.
4. **건설적 완벽주의:** 높은 점수를 받은 답변이라 할지라도, 더 진보된 산업 전문 용어를 제안하십시오.
5. **실제 상황 연관화:** 전달 방식이나 구조를 직장 내 행동과 연결하십시오(예: "이해관계자는 이를 불확실성으로 읽을 수 있습니다").

#################### 채점 루브릭 (BARS 0.0 - 10.0) ####################

1. **내용 관련성 (CR)** - 의도 부합도, 방법론의 품질, 직무 일치성.
    - **0-3:** 요점을 놓침, 주요 내용 오류, 또는 비전문적인 어조.
    - **4-6:** 전반적으로 관련은 있으나 깊이나 정량화가 부족함. 질문의 일부만 답변함.
    - **7-10:** 매우 정확함, 깊은 지식을 입증함, 명확한 임팩트를 포함함. (가이드라인 3 & 4 적용).

2. **구조 (ST)** - STAR 방식의 서사, 어휘 및 문법.
    - **0-3:** 장황하고 무질서함, 또는 명확한 STAR 프레임워크가 없음.
    - **4-6:** 부분적인 구조(예: 상황/행동은 있으나 결과가 누락됨). 적절한 문법.
    - **7-10:** 명확한 논리와 정교한 어휘를 갖춘 설득력 있는 서사. (가이드라인 4 적용).

3. **유창성 및 속도 (FL)** - WPM 및 침묵 비율에 기반한 흐름과 페이스.
    - **0-3:** 매우 느림(<80 WPM) 또는 높은 침묵 비율(>25%).
    - **4-6:** 수용 가능한 속도(80-120 WPM)와 보통 수준의 망설임(15-25% 침묵 비율).
    - **7-10:** 최소한의 침묵(<15%)을 동반한 대화하듯 매끄러운 흐름(120-180 WPM).
    - **참고:** 멈춤 없는 과도한 속도 = "빠르지만 혼란스러움" (2-4점).

4. **자신감 프록시 (CP)** - 분당 멈춤 횟수(PPM)에 기반한 안정성 및 확신.
    - **0-5:** 높은 멈춤 빈도(>10 PPM)로 불안감이나 일관성 부족을 시사함.
    - **6-10:** 통제되고 절제된 페이스(<8 PPM)로 역량과 확신을 전달함.

#################### 핵심 채점 규칙 ####################
A. **홀수 번호 질문 (1, 3, 5, 7, 9):** 4가지 차원 전체 평가 수행.
B. **짝수 번호 질문 (2, 4, 6, 8, 10):** 2가지 차원(CR/ST)만 평가. FL/CP에는 0.0을 할당. `evaluation_text`에는 CR과 ST에 대한 내용만 작성하고 FL과 CP는 언급하지 마십시오.
C. **금지 사항:**
    - 텍스트 피드백에 수치 지표(WPM, PPM)를 직접 인용하지 마십시오.
    - "귀하는 ~을 입증했습니다...", "당신의 답변은 명확했습니다...", 또는 "잘했습니다"와 같은 상투적인 문구로 시작하지 마십시오.
    - 여러 질문에 걸쳐 동일한 시작 문구(예: "채용 담당자는 ~을 찾습니다...")를 반복하지 마십시오.
"""
SYSTEM_PROMPT_UNI = """
귀하는 강력한 영향력을 가진 **AI 대입 면접 코치이자 교육 컨설턴트**입니다. 귀하의 임무는 엄격한 학술적 BARS(행동 기준 평정 척도) 루브릭에 따라 학생의 면접 성과를 평가하여, 명문대 합격을 위한 최상위권 인재로 준비시키는 것입니다.

**코칭 페르소나:**
지원자가 한 말을 단순히 요약하지 마십시오. 대신, 입학 사정관이 해당 답변을 어떻게 인식하는지, 그리고 어떻게 해야 "학업적 역량(Academic Readiness)"을 증명할 수 있는지 설명하십시오. 위원회가 이 질문을 던진 이유(예: 지원자의 지적 호기심을 측정하려는 의도 등)를 밝히는 **"입학 사정 통찰(Admissions Insight)"**로 시작하십시오. 귀하의 목표는 학생의 답변을 일반적인 수준에서 학술적인(Scholarly) 수준으로 격상시키도록 능동적으로 코칭하는 것입니다.

**피드백 다양성 및 스타일:**
자연스럽고 대화하듯 흐르는 코칭을 위해, 매 질문마다 첫 문장을 다르게 구성하십시오. 반복적인 헤더, 접두사, 시작 문구를 사용하지 마십시오. 대신, 다음 네 가지 관점을 번갈아 가며 사용하여 **"공격 각도(Angle of Attack)"**를 조정하십시오:

- **관점 A (학업적 잠재력):** 특정 답변이 지원자의 지적 깊이나 전공에 대한 열정에 대해 입학 위원회에 어떤 신호를 주는지 설명하며 시작하십시오.
- **관점 B (학술적 전환):** 표면적인 답변에서 통찰력 있고 학술적인 답변으로 즉시 전환하는 방법으로 시작하십시오.
- **관점 C (캠퍼스 기여도):** 지원자가 언급한 행동이나 가치관이 대학의 협력적 환경이나 연구 현장에서 어떻게 나타날지 묘사하며 시작하십시오.
- **관점 D (학구적 우위):** 최상위권 지원자들이 자신의 개인적 관심사를 특정 교과 과정이나 학과 연구에 어떻게 연결시키는지 강조하며 시작하십시오.

**핵심 초기 임무:** 지원자의 목표 전공 또는 학과(예: 경영, 생물학, 공학 등)를 추론하십시오. 이를 가이드라인 1에 적용하십시오.

#################### 5가지 핵심 코칭 가이드라인 ####################

1. **학과 일치성 및 정교함:** 답변을 추론된 전공과 비교하십시오. 고급 전문 용어와 학술적 담론을 제안하십시오. 전공 분야에 대한 호기심 부족이나 학과 가치와의 불일치를 표시하십시오.
2. **논리적 엄격함, 결과보다 과정:** 단순한 결과뿐만 아니라 학생의 사고 방식을 평가하십시오. 학생의 사고 '과정'을 상세히 설명하십시오. 입학 사정관은 전제에서 결론에 이르는 과정을 중요하게 여깁니다. 단순한 성공 사례보다 지적 엄격함에 가중치를 두십시오.
3. **구체성 및 정량화 심리:** 신뢰도 신호로서 측정 지표(%, $, 시간, 규모)를 적극적으로 요구하십시오. 뛰어난 답변이라 할지라도, 임팩트를 가시화하고 신뢰를 쌓기 위해 정량화가 반드시 필요함을 설명하십시오.
4. **지적 인성:** 전달 방식과 구조를 학술적 특성(회복 탄력성, 호기심, 윤리)과 연결하십시오. 학생의 페르소나가 높은 수준의 학계에서 요구하는 역량에 부합하는지 평가하십시오.
5. **건설적인 완벽주의:** "완벽한" 답변은 없습니다. 점수가 높더라도 고급 산업 전문 용어를 제안하십시오. "다음 단계" 제안이 없는 축하성 피드백은 코칭 실패입니다.

#################### 채점 루브릭 (BARS 0.0 - 10.0) ####################

1. **내용 관련성 (CR)** - 전공 적합성, 학과에 대한 이해도, 통찰력의 깊이.
    - **0-3:** 관련 없음, 전공 분야에 대한 기초 지식 부족, 또는 동기 결여.
    - **4-6:** 일반적인 지식은 갖추었으나 개인적인 통찰이나 특정 학과와의 연결 고리가 부족함.
    - **7-10:** 깊은 지적 호기심, 특정 학과에 대한 구체적 지식, 명확한 학업 목표를 입증함. (가이드라인 3 & 4 적용).

2. **구조 (ST)** - 논리적 흐름(예: PEEL 또는 STAR 방식), 어휘 및 학술적 문법.
    - **0-3:** 무질서함, 주장에 대한 근거 부족, 또는 지나치게 비격식적인 언어 사용.
    - **4-6:** 어느 정도 구조는 갖추었으나 문장 간 연결이 매끄럽지 않거나 근거가 희박함.
    - **7-10:** 명확한 논리적 연결과 학술적 수준의 어휘를 갖춘 정교한 서사. (가이드라인 4 적용).

3. **유창성 및 속도 (FL)** - WPM 및 침묵 비율에 기반한 흐름과 페이스.
    - **0-3:** 매우 느림(<80 WPM) 또는 높은 침묵 비율(>25%).
    - **4-6:** 수용 가능한 속도(80-120 WPM)와 보통 수준의 망설임(15-25% 침묵 비율).
    - **7-10:** 최소한의 침묵(<15%)을 동반한 대화하듯 매끄러운 흐름(120-180 WPM).
    - **참고:** 멈춤 없는 과도한 속도 = "빠르지만 혼란스러움" (2-4점).

4. **자신감 프록시 (CP)** - 분당 멈춤 횟수(PPM)에 기반한 안정성 및 확신.
    - **0-5:** 높은 멈춤 빈도(>10 PPM)로 불안감이나 일관성 부족을 시사함.
    - **6-10:** 통제되고 절제된 페이스(<8 PPM)로 역량과 확신을 전달함.

#################### 핵심 채점 규칙 ####################
A. **홀수 번호 질문 (1, 3, 5, 7, 9):** 4가지 차원 전체 평가 수행.
B. **짝수 번호 질문 (2, 4, 6, 8, 10):** 2가지 차원(CR/ST)만 평가. FL/CP에는 0.0을 할당. `evaluation_text`에는 CR과 ST에 대한 내용만 작성하고 FL과 CP는 언급하지 마십시오.
C. **금지 사항:**
    - 텍스트 피드백에 수치 지표(WPM, PPM)를 직접 인용하지 마십시오.
    - "귀하는 ~을 입증했습니다...", "당신의 답변은 명확했습니다...", 또는 "잘했습니다"와 같은 상투적인 문구로 시작하지 마십시오.
    - 여러 질문에 걸쳐 동일한 시작 문구(예: "위원회는 ~을 찾습니다...")를 반복하지 마십시오.
"""
COMMON_OUTPUT_RULES = """
#################### 출력 요구 사항 ####################

1. **출력 페르소나:** `evaluation_text`, `strength_text`, 그리고 `areas_for_growth_text`에 포함되는 모든 서술적 피드백은 반드시 **2인칭**으로 작성되어야 합니다. (예: "당신은...", "당신의 답변 구조는...", "우리는 당신에게 ...을 권장합니다.")
2. **질문별 피드백:** `per_question_feedback` 배열은 반드시 정확히 10개의 항목을 포함해야 합니다.
    - **답변이 완료된 N개의 질문:** 0.0에서 10.0 사이의 점수를 제공하십시오. `evaluation_text`는 반드시 위에서 정의한 5가지 가이드라인을 준수하여 맞춤형 코칭을 제공해야 합니다. (참고: 개별 질문의 `overall_score` 필드에는 플레이스홀더로 0.0을 입력하십시오.)
    - **나머지 미답변 질문 (인덱스 9까지):** 아래와 같은 플레이스홀더 값을 삽입하십시오.
        - cr_score, st_score, fl_score, cp_score, overall_score: 0.0
        - evaluation_text: "후보자가 답변하지 않은 질문입니다."
        - is_correct: false
3. **세션 요약:** 완료된 질문들에서 나타난 패턴만을 참조하여 'strength_text'(강점)와 'areas_for_growth_text'(개선 필요 사항)를 각각 별도의 2~3문장으로 요약하여 제공하십시오.
4. **다음 단계:** 정확히 3개의 실행 가능한 'NextStepItem' 권장 사항을 제공하십시오.
"""

def _get_weights_for_question(q_num: int) -> Dict[str, float]:
    """Determines the weighting scheme based on question parity (1-based index)."""
    if q_num % 2 == 1:
        return ODD_Q_WEIGHTS
    else:
        return EVEN_Q_WEIGHTS

def _apply_weighted_per_question_scores(feedback_items: List[DetailedEvaluationItem]) -> List[DetailedEvaluationItem]:
    """
    DETERMINISTIC FUNCTION: Calculates and sets the weighted overall score 
    for each individual question based on the question's parity.
    """
    for item in feedback_items:
        q_num = item.question_order
        
        # Determine weights based on question parity
        weights = _get_weights_for_question(q_num)
        
        # Apply the calculation only if it's a completed question
        if item.content_relevance_score > 0.0 or item.structure_score > 0.0: 
            
            # Use content_relevance_score > 0.0 as a reliable proxy for a completed question
            weighted_score = (
                item.content_relevance_score * weights["cr_score"] +
                item.structure_score * weights["st_score"] +
                item.fluency_score * weights["fl_score"] +
                item.confidence_score * weights["cp_score"]
            )
            item.overall_score = round(weighted_score, 2)
            
    return feedback_items

def _calculate_overall_scores(feedback_items: List[DetailedEvaluationItem]) -> OverallScores:
    """
    Calculates the overall session averages for each dimension.
    
    CRITICAL: Iterates over the full list and uses item.question_order to correctly 
    filter FL/CP averages to ODD questions only.
    """
    
    # 1. Collect all completed items and scores by iterating over the 10-item list
    completed_items = []
    cr_scores = []
    st_scores = []
    fl_scores_graded = [] # Only scores from ODD questions
    cp_scores_graded = [] # Only scores from ODD questions
    
    for item in feedback_items:
        q_num = item.question_order
        
        # Check if the question was answered (CR or ST score is > 0.0)
        is_answered = item.content_relevance_score > 0.0 or item.structure_score > 0.0
        
        if is_answered:
            completed_items.append(item)
            
            # CR and ST are always graded for answered questions
            cr_scores.append(item.content_relevance_score)
            st_scores.append(item.structure_score)
            
            # FL and CP are only graded for ODD questions
            if q_num % 2 == 1:
                fl_scores_graded.append(item.fluency_score)
                cp_scores_graded.append(item.confidence_score)
    
    num_completed = len(completed_items)
    if num_completed == 0:
        return OverallScores(
            content_relevance_score=0.0,
            structure_score=0.0,
            fluency_score=0.0,
            confidence_proxy_score=0.0,
            overall_score=0.0
        )
        
    # Function to safely calculate average
    def safe_average(scores: List[float], num_total_graded_items: int) -> float:
        if num_total_graded_items == 0:
            return 0.0
        return round(sum(scores) / num_total_graded_items, 2)
    
    # --- 2. Calculate Raw Dimension Averages ---
    
    num_graded_fl_cp = len(fl_scores_graded)
    
    cr_avg = safe_average(cr_scores, num_completed)
    st_avg = safe_average(st_scores, num_completed)
    fl_avg = safe_average(fl_scores_graded, num_graded_fl_cp)
    cp_avg = safe_average(cp_scores_graded, num_graded_fl_cp)
    
    # --- 3. Calculate the Final Overall SESSION Score ---
    
    # This averages the individual question overall scores, which were already 
    # correctly weighted in _apply_weighted_per_question_scores.
    overall_score_final = sum(item.overall_score for item in completed_items) / num_completed
    overall_score_final = round(overall_score_final, 2)


    return OverallScores(
        content_relevance_score=cr_avg,
        structure_score=st_avg,
        fluency_score=fl_avg,
        confidence_proxy_score=cp_avg,
        overall_score=overall_score_final
    )

async def generate_session_evaluation_gpt(qa_pairs: List[QuestionAnswerPair], q_type: str = "job") -> EvaluationBatchResponse:
    """Calls GPT-4o via Proxy to generate structured evaluation."""
    global global_client 
    
    if global_client is None:
        try:
            global_client = AsyncOpenAI(
                base_url=f"{settings.GPT_API_BASE_URL}/v1",
                api_key=settings.ELICE_API_KEY
            )
            logging.info("GPT-4o Async Client for Evaluation successfully initialized.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize GPT-4o client: {e}")
            raise Exception("GPT-4o API Client initialization failed.")

    print(f"Question type processed: {q_type.lower()}")
    
    schema_hint = json.dumps(EvaluationLLMOutput.model_json_schema())
    OUTPUT_SCHEMA = f"""
    출력 스키마:
    {schema_hint}"""

    base_prompt = SYSTEM_PROMPT_UNI if "university" in q_type.lower() else SYSTEM_PROMPT_JOB
    SYSTEM_PROMPT = base_prompt + COMMON_OUTPUT_RULES + OUTPUT_SCHEMA

    qa_text = "\n\n--- 면접 전사 데이터 및 측정 지표 ---\n"
    for qa in qa_pairs:
        # Use the explicit question_order field from the answered item, not the list index.
        
        q_num = qa.question_order
        
        # Check if the answer was likely typed (audio duration <= 0.1s is the proxy for no meaningful audio)
        audio_duration = qa.audio_duration_seconds or 0.0
        word_count = qa.word_count or 0
        is_typed_response = (audio_duration <= 0.1)
        
        # Default values

        # --- Dynamic Metric String Construction based on Parity and Input Type ---
        if q_num % 2 == 0:
            # EVEN Question (2, 4, 6, 8, 10): FL and CP MUST be 0.0 per rubric.
            wpm, silence_ratio, ppm = 0.0, 0.0, 0.0
            grading_tag = f"| 채점 규칙: CR/ST 전용 (FL 및 CP는 반드시 0.0 처리) |"
            metrics_string = "| 측정 지표 | 유형: 짝수 번호 질문 | (출력 시 FL 및 CP는 반드시 0.0) |\n"
            raw_data_string = ""
        elif is_typed_response:
            # ODD Question, but TEXT INPUT: Full assessment required, but metrics are zeroed safely.
            wpm, silence_ratio, ppm = 0.0, 0.0, 0.0
            
            # Full assessment required (FL/CP are scored by LLM). 
            # The prompt now explicitly forces the LLM to use 7.5 for FL/CP.
            grading_tag = "| 채점 규칙: 4가지 차원 전체 평가 (CR, ST, FL, CP) |"
            metrics_string = "| 측정 지표 | 유형: 텍스트 입력 | (LLM은 반드시 FL과 CP 점수를 7.5로 부여해야 함) |\n" 
            raw_data_string = ""
        else:
            # ODD Question, SPOKEN INPUT: Use standard metric calculation
            total_pause_duration_seconds = qa.total_pause_duration_seconds or 0.0
            total_pause_count = qa.total_pause_count or 0

            # Avoid division by zero
            speaking_time_seconds = audio_duration - total_pause_duration_seconds
            speaking_time_seconds = max(speaking_time_seconds, 0.001) # Small epsilon

            if word_count == 0:
                wpm = 0.0
                silence_ratio = 100.0 if audio_duration > 0 else 0.0
                ppm = 0.0
            else:
                wpm = (word_count / speaking_time_seconds) * 60.0
                silence_ratio = (total_pause_duration_seconds / audio_duration) * 100.0 if audio_duration > 0 else 0.0
                ppm = (total_pause_count / audio_duration) * 60.0 if audio_duration > 0 else 0.0
            
            # Full assessment
            grading_tag = "| 채점 규칙: 4가지 차원 전체 평가 (CR, ST, FL, CP) |\n"
            metrics_string = (
                f"| 측정 지표 | WPM: {wpm:.1f} | 침묵 비율: {silence_ratio:.1f}% | PPM: {ppm:.1f} |\n"
            )
            raw_data_string = (
                f"| 원천 데이터 | 오디오 길이: {audio_duration:.1f}초 | 단어 수: {word_count} | 멈춤 횟수: {total_pause_count} | 멈춤 시간: {total_pause_duration_seconds:.1f}초 |\n"
            )

        
        qa_text += f"질문{q_num}: {qa.question_text}\n"
        qa_text += f"답변{q_num} (전사 데이터): {qa.answer_text}\n"
        qa_text += grading_tag
        qa_text += metrics_string
        qa_text += raw_data_string
        qa_text += "\n"
        
    num_completed_questions = len(qa_pairs)
    num_unanswered_questions = 10 - num_completed_questions
    
    qa_text += "--------------------------------------\n\n"
    
    user_query = (
        f"제공된 총 10개 중 {num_completed_questions}개의 문답 쌍을 바탕으로, "
        f"유창성(FLUENCY) 및 자신감 프록시(CONFIDENCE PROXY) 채점을 위해 제공된 정량적 지표를 엄격히 사용하고, "
        f"해당되는 경우 텍스트 입력(TEXT INPUT)에 대한 핵심 채점 규칙을 준수하여, "
        f"구조화된 전체 JSON 평가 결과를 제공하십시오. "
        f"응답 내의 evaluation_text에는 WPM, 침묵 비율(Silence Ratio), 또는 PPM의 구체적인 수치값을 **절대로 인용해서는 안 됩니다**. "
        f"제공된 {num_completed_questions}개의 답변에 대해서만 평가를 진행하십시오. "
        f"그 다음, 'per_question_feedback' 배열의 길이가 정확히 10개가 되도록, "
        f"미답변 질문에 대해 원래의 질문 순서와 플레이스홀더 값을 사용하여 {num_unanswered_questions}개의 플레이스홀더 항목을 배열 끝에 반드시 추가해야 합니다.\n\n"
        f"{qa_text}"
    )
    # user_query = (
    #     f"Based on the following {num_completed_questions} Q&A pair(s) (out of 10 total), "
    #     f"and strictly using the quantitative metrics provided for FLUENCY and CONFIDENCE PROXY scoring, "
    #     f"and adhering to the CRITICAL SCORING RULE for TEXT INPUT where applicable, "
    #     f"provide the full structured JSON evaluation. "
    #     f"The evaluation_text in the response **MUST NOT** quote the specific numerical values of WPM, Silence Ratio, or PPM. "
    #     f"Remember to evaluate only the {num_completed_questions} answers provided. "
    #     f"Then, you MUST add {num_unanswered_questions} placeholder item(s) to the end of the 'per_question_feedback' array, "
    #     f"using the original question order and placeholder values for unanswered questions, to ensure its length is exactly 10.\n\n"
    #     f"{qa_text}"
    # )

    try:
        # response = await global_client.chat.completions.parse(
        #     model=MODEL_NAME,
        #     messages=[
        #         {"role": "system", "content": SYSTEM_PROMPT},
        #         {"role": "user", "content": user_query}
        #     ],
        #     response_format=EvaluationLLMOutput
        # )

        # llm_out = response.choices[0].message.parsed
        # feedback_items = _apply_weighted_per_question_scores(llm_out.per_question_feedback)
        # overall_scores_obj = _calculate_overall_scores(feedback_items)

        response = await global_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content
        parsed_json = json.loads(raw_content)
        
        # Pydantic validation (The "Guarantee" that fields match your schema)
        llm_out = EvaluationLLMOutput(**parsed_json)
        
        # Post-process for math
        feedback_items = _apply_weighted_per_question_scores(llm_out.per_question_feedback)
        overall_scores_obj = _calculate_overall_scores(feedback_items)


        return EvaluationBatchResponse(
            per_question_feedback=feedback_items,
            overall_scores=overall_scores_obj,
            session_summary=llm_out.session_summary,
            next_steps=llm_out.next_steps
        )

    except Exception as e:
        logging.error(f"GPT-4o Evaluation Error: {e}")
        raise Exception(f"Failed to generate evaluation: {e}")