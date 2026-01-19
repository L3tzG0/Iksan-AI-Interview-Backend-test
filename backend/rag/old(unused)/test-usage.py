# pip install langchain-google-genai langchain-postgres python-dotenv psycopg2-binary

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUR_PASSWORD = os.getenv("DB_PASSWORD")


embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)

COLLECTION_NAME = "interview_question_bank"
CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{YOUR_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
# CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{YOUR_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
# CONNECTION_STRING = f"postgresql://postgres:{YOUR_PASSWORD}@db.hjddiycvtlzgialqxcof.supabase.co:5432/postgres"
# Re-initialize the vector store for retrieval (using the same settings)
vectorstore_retriever = PGVector(
    embeddings=embeddings,
    connection=CONNECTION_STRING,
    collection_name=COLLECTION_NAME
)

# Create a Retriever object
retriever = vectorstore_retriever.as_retriever(search_kwargs={"k": 5})

# Test Query
# user_topic = "I am a final year computer science student looking forward to being a software engineer"
# user_topic = "I am a final year computer science student looking forward to being a software engineer focusing on backend system design and architecture for a gaming company."
user_topic = "computer science, software engineer, technology, back end"
# user_topic = "I am a final year computer science student, looking forward to pursue my career in tech, aiming to be an employee at nexon"

try:
    retrieved_docs = retriever.invoke(user_topic)

    print(f"\n--- Retrieved {len(retrieved_docs)} Relevant Context Chunks ---")
    for i, doc in enumerate(retrieved_docs):
        print(f"\n[Chunk {i+1}] Score: {doc.metadata.get('score', 'N/A')}")
        print(doc.page_content + "...")
finally:
    # Explicitly dispose of the SQLAlchemy engine to close connections
    # This is important when hitting connection limits, especially with PgBouncer
    if vectorstore_retriever and hasattr(vectorstore_retriever, '_engine'):
      print("Disposing of SQLAlchemy engine...")
      vectorstore_retriever._engine.dispose()