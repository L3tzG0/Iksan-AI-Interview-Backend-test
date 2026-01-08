import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

YOUR_PASSWORD = os.getenv("DB_PASSWORD")

COLLECTION_NAME = "interview_question_bank"
CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{YOUR_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
# CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{YOUR_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
# CONNECTION_STRING = f"postgresql://postgres:[{YOUR_PASSWORD}]@db.hjddiycvtlzgialqxcof.supabase.co:5432/postgres"
# CONNECTION_STRING = os.getenv("DATABASE_URL")

# Ensure CONNECTION_STRING is defined (it should be from previous cells)
# If you run this cell independently, you might need to re-run the cell defining CONNECTION_STRING
# CONNECTION_STRING = f"postgresql://postgres.hjddiycvtlzgialqxcof:{YOUR_PASSWORD}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
print(f"Attempting to connect to database using: {CONNECTION_STRING.split('@')[1]}...")

try:
    # Attempt to establish a connection
    conn = psycopg.connect(CONNECTION_STRING)
    # Create a cursor object
    cur = conn.cursor()
    # Execute a simple query to verify connection
    cur.execute("SELECT 1;")
    result = cur.fetchone()[0]
    if result == 1:
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed with unexpected query result.")

    # Close cursor and connection
    cur.close()
    conn.close()
except psycopg.Error as e:
    print(f"❌ Database connection failed: {e}")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")