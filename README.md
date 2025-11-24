# Iksan AI Interview Backend

A FastAPI-based backend service for the Iksan AI Interview platform, powered by Supabase for authentication and database management.

##  Features

- **Supabase Authentication** - Secure user authentication with JWT tokens
- **Role-Based Access Control** - Support for students and teachers
- **RESTful API** - Well-documented OpenAPI/Swagger endpoints
- **Row Level Security** - Database-level security policies

##  Prerequisites

- Python 3.10 or higher
- Supabase account ([Sign up here](https://supabase.com))
- pip (Python package manager)
- Git

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/calistasalscpw/Iksan-AI-Interview-Backend.git
cd Iksan-AI-Interview-Backend
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**Where to find these values:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy the **Project URL** and **anon/public** key

### 5. Set Up Database Schema
Go to your Supabase Dashboard → SQL Editor and run the SQL queries in `/queries`

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The server will start at **http://127.0.0.1:8000**

### 7. Test the API

Open your browser and visit:
- **Hello from IKSAN AI Interview**: http://127.0.0.1:8000/
- **Healh Check**: http://127.0.0.1:8000/health

## API Documentation

Once the server is running, access the interactive API documentation:

### Swagger UI
http://127.0.0.1:8000/docs

### ReDoc
http://127.0.0.1:8000/redoc

## 🔐 Authentication Flow

(to be implemented)
## 📁 Project Structure

```
Iksan-AI-Interview-Backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py          # FastAPI dependencies
│   │   └── v1/
│   │       ├── endpoints/           # API route handlers
│   │       │   ├── auth.py         # Authentication endpoints
│   │       │   ├── students.py     # Student management
│   │       │   ├── teachers.py     # Teacher management
│   │       │   ├── classes.py      # Class management
│   │       │   ├── interview_sessions.py
│   │       │   ├── interview_scores.py
│   │       │   └── feedback.py
│   │       └── router.py           # API router configuration
│   ├── core/
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Supabase client setup
│   │   └── security.py             # JWT validation
│   ├── schemas/                    # Pydantic schemas
│   │   ├── auth.py                 # Auth request/response models
│   │   ├── user.py
│   │   ├── student.py
│   │   └── ...
│   └── main.py                     # FastAPI application entry point
├── .env                            # Environment variables (not in git)
├── .gitignore
├── requirements.txt                # Python dependencies
├── test_migration.py              # Migration test suite
├── README.md                       # This file
├── MIGRATION_GUIDE.md             # Migration documentation
└── CHECKLIST.md                   # Setup checklist
```

## 🧪 Testing

### Run Set up Test

```bash
python ./tests/test_setup.py
```

Expected output:
```
✅ PASS - Configuration
✅ PASS - Supabase Client
✅ PASS - Auth Methods
✅ PASS - Table Methods
✅ PASS - Module Imports
✅ PASS - FastAPI App

Total: 6 | Passed: 6 | Failed: 0
```

