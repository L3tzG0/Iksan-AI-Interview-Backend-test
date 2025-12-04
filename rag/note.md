Recommended approach (singleton engine + reuse)
Create the engine / PGVector once at app startup and reuse it for all requests.
Do not call dispose() after each request; only call it on graceful shutdown or when you need to recycle the pool for a reason.
If you are in Session mode, configure a very small pool_size (1–4) and max_overflow=0 when creating the engine.
If PGVector allows passing an existing SQLAlchemy engine, create the engine yourself and pass it in. If not, ensure you only instantiate PGVector once.
Example pattern (minimal, adjust to your framework):

```python
from sqlalchemy import create_engine
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
import os

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
YOUR_PASSWORD = os.environ["DB_PASSWORD"]
CONNECTION_STRING = f"postgresql://postgres:{YOUR_PASSWORD}@db.hjddiycvtlzgialqxcof.supabase.co:5432/postgres"
COLLECTION_NAME = "interview_question_bank"

# Create a single engine at startup with conservative pool settings
engine = create_engine(
    CONNECTION_STRING,
    pool_size=2,        # tune this per pooler limits & number of app instances
    max_overflow=0,
    pool_pre_ping=True
)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=GEMINI_API_KEY)

# If PGVector accepts engine parameter, pass it; otherwise pass connection string but ensure single instantiation
vectorstore = PGVector(embeddings=embeddings, connection=CONNECTION_STRING, collection_name=COLLECTION_NAME)
# If supported: PGVector(..., engine=engine)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def get_retrieved_docs(user_topic: str):
    return retriever.invoke(user_topic)

# On graceful shutdown only:
# engine.dispose()
```

If PGVector supports passing an engine, prefer that to avoid hidden engine creation. If it does not, ensure you call PGVector(...) only once at startup.