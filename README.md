# Iksan AI Interview Backend

A FastAPI-based backend service for the Iksan AI Interview platform, powered by Supabase for authentication and database management.

##  Features

- **Supabase Authentication** - Secure user authentication with JWT tokens
- **Role-Based Access Control** - Support for students, teachers, and admins
- **Interview Management** - Track and manage AI-powered interview sessions
- **Score Analytics** - Comprehensive scoring and feedback system
- **RESTful API** - Well-documented OpenAPI/Swagger endpoints
- **Row Level Security** - Database-level security policies
- **Real-time Ready** - Built on Supabase for future real-time features

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

Go to your Supabase Dashboard → **SQL Editor** and run the following SQL:

```sql
-- Roles table
CREATE TABLE public.roles (
    id SERIAL PRIMARY KEY,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO public.roles (role_name, description) VALUES
('student', 'Student role'),
('teacher', 'Teacher role'),
('admin', 'Administrator role');

-- Users table (extends auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role_id INTEGER REFERENCES public.roles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Schools table
CREATE TABLE public.schools (
    id SERIAL PRIMARY KEY,
    school_name TEXT NOT NULL,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Majors table
CREATE TABLE public.majors (
    id SERIAL PRIMARY KEY,
    major_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Students table
CREATE TABLE public.students (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    school_id INTEGER REFERENCES public.schools(id),
    major_id INTEGER REFERENCES public.majors(id),
    student_id_number TEXT,
    grade_level INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Teachers table
CREATE TABLE public.teachers (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    school_id INTEGER REFERENCES public.schools(id),
    department TEXT,
    years_of_experience INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Classes table
CREATE TABLE public.classes (
    id SERIAL PRIMARY KEY,
    class_name TEXT NOT NULL,
    teacher_id INTEGER REFERENCES public.teachers(id),
    school_id INTEGER REFERENCES public.schools(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interview Sessions table
CREATE TABLE public.interview_sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES public.students(id),
    session_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending',
    total_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interview Scores table
CREATE TABLE public.interview_scores (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES public.interview_sessions(id),
    category TEXT NOT NULL,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

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
│   ├── models/                     # Data models (kept for reference)
│   ├── schemas/                    # Pydantic schemas
│   │   ├── auth.py                 # Auth request/response models
│   │   ├── user.py
│   │   ├── student.py
│   │   └── ...
│   ├── services/                   # Business logic layer
│   │   ├── auth_service.py         # Auth operations
│   │   ├── user_service.py         # User CRUD
│   │   ├── student_service.py
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

