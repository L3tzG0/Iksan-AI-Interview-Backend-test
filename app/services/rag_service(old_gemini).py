import os
import re
import asyncio
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector, DistanceStrategy
from langchain_core.documents import Document
from dotenv import load_dotenv

# Local imports
from app.schemas.rag_schema import RagResult
from app.core.config import settings

# Load environment variables if running outside a container environment
load_dotenv() 

# --- Configuration ---
GEMINI_API_KEY = settings.GEMINI_API_KEY
DB_PASSWORD = settings.DB_PASSWORD
COLLECTION_NAME_JOB = "interview_question_bank"
COLLECTION_NAME_UNI = "uni_interview_question_bank"

# NOTE: Using the TRANSACTION POOLER address (Port 6543) for maximum concurrency and scalability.
# CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{DB_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
CONNECTION_STRING = settings.RAG_DB_CONN_STRING

HIGH_VALUE_TERMS_JOB = [
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

HIGH_VALUE_TERMS_UNI = [
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

# --- RAG Initialization Check ---
# Embeddings are initialized once globally as they are immutable and thread-safe.
_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
_rag_is_ready = False

try:
    if DB_PASSWORD and GEMINI_API_KEY:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=GEMINI_API_KEY
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