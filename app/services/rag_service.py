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
COLLECTION_NAME = "interview_question_bank"

# NOTE: Using the TRANSACTION POOLER address (Port 6543) for maximum concurrency and scalability.
CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{DB_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

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

def extract_keywords_cheaply(cv_text: str) -> str:
    """
    Efficiently extracts core keywords from CV/About Me text using regex 
    and structural parsing (non-LLM call). Generates the optimized query string.
    """
    HIGH_VALUE_TERMS = ['Python', 'FastAPI', 'React', 'TypeScript', 'SQL', 'PostgreSQL', 
                        'Supabase', 'AWS', 'Azure', 'Kubernetes', 'Machine Learning', 
                        'Data Science', 'Lead Engineer', 'Manager', 'Project Manager', 
                        'eCommerce', 'FinTech', 'DevOps', 'CI/CD']
    
    skills_match = re.search(r'(Skills|Technical Proficiencies|Expertise)[:\s]*(.*?)(?=\n[A-Z]|\Z)', cv_text, re.DOTALL | re.IGNORECASE)
    experience_match = re.search(r'(Experience|Professional History|Career Summary)[:\s]*(.*?)(?=\n[A-Z]|\Z)', cv_text, re.DOTALL | re.IGNORECASE)

    found_terms = [term for term in HIGH_VALUE_TERMS if re.search(r'\b' + re.escape(term) + r'\b', cv_text, re.IGNORECASE)]
    
    query_parts = []
    
    if skills_match:
        skills_text = re.sub(r'\s+', ' ', skills_match.group(2).strip())
        query_parts.append(f"Skills: {skills_text}")
    
    if experience_match and len(query_parts) < 3: 
        experience_summary = experience_match.group(2).strip().split('\n')[0]
        query_parts.append(f"Top Job: {experience_summary}")

    if found_terms:
        query_parts.append(f"Keywords: {', '.join(set(found_terms))}")
    
    if not query_parts:
        summary = ' '.join(cv_text.split()[:50])
        query_parts.append(summary)

    return " | ".join(query_parts)

async def retrieve_questions_from_rag(cv_text: str, k: int = 10) -> RagResult:
    """
    Orchestrates the RAG retrieval process: Keyword extraction -> Vector Search.
    Initializes PGVector locally and ensures connection disposal.
    """
    search_query_text = extract_keywords_cheaply(cv_text)
    print(search_query_text)
    vector_store: Optional[PGVector] = None
    
    if not _rag_is_ready or not _embeddings:
        print("RAG disabled or failed to initialize. Returning empty reference questions.")
        return RagResult(reference_questions=[], source_query=search_query_text)

    # Synchronous function to run in a thread
    def sync_retrieve(store: PGVector, query: str, k_val: int) -> List[Document]:
        """Synchronous function to perform the LangChain PGVector search."""
        retriever = store.as_retriever(search_kwargs={"k": k_val})
        return retriever.invoke(query)

    try:
        # CRUCIAL: Create PGVector instance locally for per-request connection management.
        vector_store = PGVector(
            embeddings=_embeddings,
            connection=CONNECTION_STRING,
            collection_name=COLLECTION_NAME,
            distance_strategy=DistanceStrategy.COSINE
        )

        # Run retrieval in a separate thread
        retrieved_docs = await asyncio.to_thread(sync_retrieve, vector_store, search_query_text, k)
        
        # Extract the raw page content, retaining the metadata for LLM context
        questions = [doc.page_content for doc in retrieved_docs]
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