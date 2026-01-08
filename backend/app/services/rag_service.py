import os
import re
import asyncio
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector, DistanceStrategy
from langchain_core.documents import Document
from dotenv import load_dotenv
import random

# Local imports
from app.schemas.rag_schema import RagResult
from app.core.config import settings

# Load environment variables if running outside a container environment
load_dotenv() 

# --- Configuration ---
OPENAI_API_KEY = settings.ELICE_API_KEY
COLLECTION_NAME_JOB = "interview_question_bank"
COLLECTION_NAME_UNI = "uni_interview_question_bank"
OPENAI_API_BASE = settings.GPT_EMBED_BASE_URL

# NOTE: Using the TRANSACTION POOLER address (Port 6543) for maximum concurrency and scalability.
# CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{DB_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
CONNECTION_STRING = settings.RAG_DB_CONN_STRING

HIGH_VALUE_TERMS_JOB_EN = [
    # --- Technical & Engineering (Hard Specs) ---
    'Python', 'FastAPI', 'React', 'TypeScript', 'SQL', 'PostgreSQL', 
    'Supabase', 'AWS', 'Azure', 'Kubernetes', 'Machine Learning', 
    'Data Science', 'Lead Engineer', 'DevOps', 'CI/CD', 'Agile', 'Scrum',
    'Architecture', 'Infrastructure', 'Kernel', 'Hacking', 'Programming Language',
    'C++', 'GET vs POST', 'Process vs Thread', 'Fluid Dynamics', 'Thermodynamics', 
    'Energy Efficiency', 'Semiconductors', 'Electromagnetic Induction', 'Lenz\'s Law',

    # --- Industry & Business Domain ---
    'SCM', 'Supply Chain', 'Logistics', 'Retail', 'Market Research', 
    'Brand Marketing', 'Profit and Loss', 'Interest Rates', 'Insurance', 
    'Securities', 'Leasing Industry', 'Smart Grid', 'Public Enterprise',
    'Social Security', 'Ancillary Revenue', 'Trade Cartels', 'Engel Coefficient',
    'Mobile Market', 'Game Planning', 'UX Design', 'Food Service', 'Production',

    # --- Leadership & Soft Skills (The behavioral "Bridges") ---
    'Leadership', 'Follower', 'Initiator', 'Conflict', 'Coordination', 
    'Persuasion', 'Communication', 'Interpersonal', 'Management Style', 
    'Mentorship', 'Feedback', 'Stakeholder', 'Teamwork', 'Decision-making',

    # --- Situational, Stress & Ethics ---
    'Supervisor', 'Superior', 'Unreasonable', 'Legally Wrongful', 'Scolded',
    'Complaint', 'Malicious Civil Petitioner', 'Burnout', 'Workload', 'Excessive', 
    'Deadline', 'Crisis Management', 'Labor Dispute', 'Union', '52-hour week', 
    'Emergency', 'Broken machine', 'Work-life balance', 'WoRaBel',

    # --- Career Path & Personal Background ---
    'Aspirations', 'Five years', 'Work ethic', 'Philosophy', 'Core Value',
    'Internship', 'Practical Training', 'Leave of Absence', 'Gap Year', 
    'Master\'s Degree', 'Exchange Program', 'Volunteer', 'Career Gap',
    'Military Service', 'Qualifications', 'GPA', 'Major-alignment',

    # --- Abstract & Creativity Triggers ---
    'Creativity', 'Fierce', 'Dedicated', 'Red Brick', 'Quantitative Estimate',
    'Logic', 'Motto', 'Life Goal', 'Reading', 'Newspaper', 'Article', 
    'English Interview', 'Self-PR', '1-minute self-introduction'

    # --- Company Anchors ---
    'Nexon', 'Samsung', 'Hyundai', 'LG', 'Shinhan', 'CJ', 'Kakao', 'SK Hynix', 'KEPCO',
    
    # --- Industry Anchors ---
    'Gaming', 'Retail', 'Semiconductor', 'Finance', 'Banking', 'Logistics', 
    'Public Enterprise', 'Automotive', 'Department Store', 'Construction'
]

HIGH_VALUE_TERMS_JOB = [
    # --- 기술 및 엔지니어링 (하드 스펙) ---
    'Python', 'FastAPI', 'React', 'TypeScript', 'SQL', 'PostgreSQL', 
    'Supabase', 'AWS', 'Azure', 'Kubernetes', '머신러닝', 
    '데이터 사이언스', '리드 엔지니어', 'DevOps', 'CI/CD', '애자일(Agile)', '스크럼(Scrum)',
    '아키텍처', '인프라', '커널', '해킹', '프로그래밍 언어',
    'C++', 'GET vs POST', '프로세스 vs 스레드', '유체역학', '열역학', 
    '에너지 효율', '반도체', '전자기 유도', '렌츠의 법칙',

    # --- 산업 및 비즈니스 도메인 ---
    'SCM', '공급망 관리', '물류', '유통/리테일', '시장 조사', 
    '브랜드 마케팅', '손익(P&L)', '금리', '보험', 
    '증권', '리스 산업', '스마트 그리드', '공기업',
    '사회 보장', '부대 수입', '담합/카르텔', '엔겔 지수',
    '모바일 시장', '게임 기획', 'UX 디자인', '외식 산업', '생산 관리',

    # --- 리더십 및 소프트 스킬 (커리어 가교 질문용) ---
    '리더십', '팔로워십', '주도자', '갈등 관리', '조정', 
    '설득', '커뮤니케이션/소통', '대인 관계', '관리 스타일', 
    '멘토링', '피드백', '이해관계자', '팀워크', '의사결정',

    # --- 상황 판단, 스트레스 및 윤리 ---
    '관리자', '상사', '부당함', '법적 위반', '질책/꾸지람',
    '불만/민원', '악성 민원인', '번아웃', '업무량', '과도함', 
    '마감 기한', '위기 관리', '노사 갈등', '노동조합', '주 52시간 근무제', 
    '비상 상황', '장비 고장', '일과 삶의 균형', '워라밸',

    # --- 커리어 경로 및 개인 배경 ---
    '입사 후 포부', '5년 후 모습', '직업 윤리', '가치관/철학', '핵심 가치',
    '인턴십', '현장 실습', '휴학', '갭이어(Gap Year)', 
    '석사 학위', '교환 학생', '봉사 활동', '경력 공백',
    '병역/군 복무', '자격 요건', '학점(GPA)', '전공 적합성',

    # --- 추상적 사고 및 창의성 트리거 ---
    '창의성', '치열함', '헌신적인', '붉은 벽돌(창의성 테스트)', '정량적 추정',
    '논리', '좌우명', '인생 목표', '독서', '신문', '기사', 
    '영어 면접', '자기 PR', '1분 자기소개'

    # --- 기업 앵커 (주요 기업명) ---
    '넥슨', '삼성', '현대', 'LG', '신한', 'CJ', '카카오', 'SK하이닉스', '한국전력(KEPCO)',
    
    # --- 산업 앵커 (주요 산업군) ---
    '게임', '유통/리테일', '반도체', '금융', '은행', '물류', 
    '공기업', '자동차', '백화점', '건설'
]

HIGH_VALUE_TERMS_UNI_EN = [
    # --- Technical & Subject Anchors ---
    'Thermodynamics', 'Quantum Mechanics', "Hess's Law", 'Fourier Transform', 
    'Calculus III', 'Microeconomics', 'Organic Chemistry', 'Classical Physics', 
    'Financial Accounting', 'Differential Equations', 'Linear Algebra',
    
    # --- Academic Performance (Adjusted for your specific questions) ---
    'GPA', 'Grades', 'Academic Record', 'Level 1', 'Top Grades', 'Self-study', 
    'Private Education', 'Academic Score', 'Subject Grades', 'Drop in grades',
    
    # --- Department & Motivation ---
    'Motivation', 'Applying', 'Major', 'Department', 'Competency', 
    'Study Plan', 'Academic Verification', 'Research', 'Career Path',
    'Applied specifically', 'Choice of department',
    
    # --- Personality & Growth (Added Specific Regret/Difficulty terms) ---
    'Strengths', 'Weaknesses', 'Self-introduction', 'Personality', 'Overcame', 
    'Difficulty', 'Confidence', 'Regrets', 'Hardship', 'Loss of confidence',
    'Personal Statement', 'Aspiration', 'Anecdotes', 'Faithful',
    
    # --- Extracurricular & Leadership (Added Specific Roles) ---
    'Club', 'Executive', 'Leadership', 'Cooperation', 'Volunteer', 'Mentoring', 
    'School Record', 'Award', 'Event', 'Organizational Adaptability', 
    'School Life', 'Life Record', 'Extracurricular', 'Demonstrate',
    
    # --- Vision & Reading (Adjusted for career and book specifics) ---
    'Vision', 'Goals', '10 years', 'Ultimate Goal', 'Book', 'Memorable', 
    'Reading Experience', 'Graduating', 'Future Hope', 'Cultivate', 
    'Major-related skills', 'Enlightenment', 'Rewarding'
]

HIGH_VALUE_TERMS_UNI = [
    # --- 기술 및 과목 앵커 (전공 지식) ---
    '열역학', '양자역학', "헤스의 법칙", '푸리에 변환', 
    '미적분학 III', '미시경제학', '유기화학', '고전물리학', 
    '재무회계', '미분방정식', '선형대수학',
    
    # --- 학업 성취도 (한국 내신 시스템 반영) ---
    '학점/내신(GPA)', '성적', '생활기록부(기록)', '1등급', '최상위 성적', '자기주도학습', 
    '사교육', '학업 점수', '교과 성적', '성적 하락/추이',
    
    # --- 학과 및 지원 동기 (전공 적합성) ---
    '지원 동기', '지원 과정', '전공', '학과', '역량', 
    '학업 계획', '학업 역량 검증', '연구', '진로 계획',
    '구체적 지원 목적', '학과 선택 이유',
    
    # --- 인성 및 성장 (극복 및 회복 탄력성) ---
    '강점', '약점', '자기소개', '성격/인성', '극복 사례', 
    '어려움/난관', '자신감', '아쉬운 점/후회', '역경', '자존감 저하',
    '자기소개서(자소서)', '포부', '에피소드/경험', '성실성',
    
    # --- 창체 및 리더십 (학교 생활 기록부 핵심) ---
    '동아리', '임원/회장', '리더십', '협력', '봉사 활동', '멘토링', 
    '학생부 기록', '수상 경력', '교내 행사', '조직 적응력', 
    '학교 생활', '생활기록부(생기부)', '창의적 체험활동', '역량 증명',
    
    # --- 비전 및 독서 (한국 대입 특화) ---
    '비전', '목표', '10년 후 모습', '최종 목표', '도서/책', '감명 깊은', 
    '독서 경험', '졸업 후 진로', '장래 희망', '함양/도모', 
    '전공 관련 기술', '깨달음/통찰', '보람찬 경험'
]

# --- RAG Initialization Check ---
# Embeddings are initialized once globally as they are immutable and thread-safe.
_embeddings: Optional[OpenAIEmbeddings] = None
_rag_is_ready = False

try:
    if CONNECTION_STRING and OPENAI_API_KEY:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE
        )
        _rag_is_ready = True
    else:
        print("Warning: RAG environment variables not fully set. RAG will be disabled.")

except Exception as e:
    print(f"FATAL ERROR: RAG Initialization failed: {e}")
    _rag_is_ready = False

# --- Core Logic ---
def extract_keywords_job_prep(cv_text: str) -> str:
    """
    Extracts core keywords from CV/About Me text using regex 
    and structural parsing, optimized for technical and professional terms.
    """
    skills_match = re.search(r'(Skills|Technical Proficiencies|Expertise)[:\s]*(.*?)(?=\n[A-Z]|\Z)', cv_text, re.DOTALL | re.IGNORECASE)
    experience_match = re.search(r'(Experience|Professional History|Career Summary)[:\s]*(.*?)(?=\n[A-Z]|\Z)', cv_text, re.DOTALL | re.IGNORECASE)

    found_terms = [term for term in HIGH_VALUE_TERMS_JOB if re.search(r'\b' + re.escape(term) + r'\b', cv_text, re.IGNORECASE)]
    
    query_parts = []
    
    if skills_match:
        skills_text = re.sub(r'\s+', ' ', skills_match.group(2).strip())
        query_parts.append(f"Skills: {skills_text}")
    
    # Limit experience summary to the first line to keep the query concise
    if experience_match and len(query_parts) < 3: 
        experience_summary = experience_match.group(2).strip().split('\n')[0]
        query_parts.append(f"Top Job Role: {experience_summary}")

    if found_terms:
        query_parts.append(f"Keywords: {', '.join(set(found_terms))}")
    
    if not query_parts:
        summary = ' '.join(cv_text.split()[:50])
        query_parts.append(summary)

    return " | ".join(query_parts)

def extract_keywords_uni_prep(study_guide_text: str) -> str:
    """
    Extracts core concepts from study guide or academic text, 
    optimized for finding academic topics and theorems.
    """
    # Simple extraction for academic text, focusing on the first 100 words and key terms
    found_terms = [term for term in HIGH_VALUE_TERMS_UNI if re.search(r'\b' + re.escape(term) + r'\b', study_guide_text, re.IGNORECASE)]
    
    query_parts = []

    # Use the beginning of the text as the primary query part
    summary = ' '.join(study_guide_text.split()[:100])
    query_parts.append(f"Topic Summary: {summary}")
    
    if found_terms:
        query_parts.append(f"Key Concepts: {', '.join(set(found_terms))}")

    return " | ".join(query_parts)

def get_search_query(text: str, q_type: str) -> str:
    """Routes the text to the correct keyword extractor based on query type."""
    q_type = q_type.lower()
    if q_type == "job":
        return extract_keywords_job_prep(text)
    elif q_type == "uni":
        return extract_keywords_uni_prep(text)
    else:
        # Default to job prep if type is unknown or missing
        print(f"Warning: Unknown query type '{q_type}'. Defaulting to 'job' extraction.")
        return extract_keywords_job_prep(text)

async def retrieve_questions_from_rag(cv_text: str, q_type: str = "job", k: int = 10) -> RagResult:
    """
    Orchestrates the RAG retrieval process: Keyword extraction -> Vector Search.
    Initializes PGVector locally and ensures connection disposal.
    """
    if q_type.lower() == "job":
        collection_name = COLLECTION_NAME_JOB
    elif q_type.lower() == "uni":
        collection_name = COLLECTION_NAME_UNI
    else:
        print(f"Error: Invalid q_type '{q_type}'. Using default job collection.")
        collection_name = COLLECTION_NAME_JOB
    
    search_query_text = get_search_query(cv_text, q_type)
    if settings.MOCK_GPT == "true":
            # Simulate network + generation latency
            await asyncio.sleep(random.uniform(2, 5)) 
            return RagResult(
                reference_questions=[
                    "How do you handle high-pressure situations?",
                    "Describe your experience with Python and FastAPI.",
                    "Tell me about a time you solved a complex architectural problem."
                ], 
                source_query=search_query_text
            )
    
    print(f"Generated Search Query ({q_type}): {search_query_text}")

    
    if not _rag_is_ready or not _embeddings:
        print("RAG disabled or failed to initialize. Returning empty reference questions.")
        return RagResult(reference_questions=[], source_query=search_query_text)

    # Synchronous function to run in a thread
    def sync_retrieve(store: PGVector, query: str, k_val: int) -> List[Document]:
        """Synchronous function to perform the LangChain PGVector search."""
        retriever = store.as_retriever(search_kwargs={"k": k_val})
        return retriever.invoke(query)

    vector_store: Optional[PGVector] = None
    try:
        # CRUCIAL: Create PGVector instance locally for per-request connection management.
        vector_store = PGVector(
            embeddings=_embeddings,
            connection=CONNECTION_STRING,
            collection_name=collection_name,
            distance_strategy=DistanceStrategy.COSINE
        )

        # Run retrieval in a separate thread
        retrieved_docs = await asyncio.to_thread(sync_retrieve, vector_store, search_query_text, k)
        
        # Extract the raw page content, retaining the metadata for LLM context
        questions = [doc.page_content for doc in retrieved_docs]
        if questions:
            print(f"questions retrieved ({len(questions)}): {questions}")
        else:
            print("rag problem: No questions retrieved.")
        return RagResult(reference_questions=questions, source_query=search_query_text)
    
    except Exception as e:
        print(f"Error during RAG retrieval runtime: {e}. Returning empty reference questions.")
        return RagResult(reference_questions=[], source_query=search_query_text)
        
    finally:
        # CRUCIAL: Dispose of the SQLAlchemy engine to release the connection to the pooler
        if vector_store and hasattr(vector_store, '_engine') and vector_store._engine:
            try:
                print("Disposing of SQLAlchemy engine...")
                vector_store._engine.dispose()
            except Exception as e_dispose:
                print(f"Warning: Failed to dispose of PGVector engine: {e_dispose}")