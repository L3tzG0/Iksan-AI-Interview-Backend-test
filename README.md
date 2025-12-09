# Iksan AI Interview Backend

A FastAPI-based backend service for the Iksan AI Interview platform, powered by Supabase for authentication and database management.

##  Features

- **Supabase Authentication** - Secure user authentication with JWT tokens
- **Role-Based Access Control** - Support for students and teachers
- **RESTful API** - Well-documented OpenAPI/Swagger endpoints
- **Row Level Security** - Database-level security policies
- **Document Processing** - PDF, DOCX, TXT, MD file extraction
- **LLM Integration Ready** - Cleaned text extraction optimized for AI processing

##  Prerequisites

- Python 3.10 or higher
- Supabase account ([Sign up here](https://supabase.com))
- pip (Python package manager)
- Git

## Installation

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

### 5. Set Up Database

**Option A: Using Migration System (Recommended)**

```bash
# Check migration status
python scripts/migrate.py status

# Generate SQL for pending migrations
python scripts/migrate.py upgrade

# Copy the output and execute in Supabase Dashboard → SQL Editor

# After successful execution, mark migrations as applied:
python scripts/migrate.py mark-applied 001
python scripts/migrate.py mark-applied 002

# Commit the tracking file
git add migrations/APPLIED_MIGRATIONS.md
git commit -m "feat: apply initial migrations"
```

**Option B: Legacy Method (Initial Setup)**

In Supabase Dashboard → SQL Editor, copy and run `queries/initialize_tables.sql`, then seed reference data:
```bash
python scripts/init_db.py --seed
```

> For detailed migration guide, see [migrations/README.md](migrations/README.md)  


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

## Authentication Flow

The backend uses **Supabase Auth** with JWT tokens for secure API access:

1. **User Registration/Login** - Via `/api/v1/auth/` endpoints
2. **JWT Token Generation** - Automatic token creation by Supabase
3. **Token Validation** - Every protected endpoint verifies JWT token
4. **Role-Based Access** - User roles (student/teacher) determine endpoint access
5. **Row Level Security** - Database queries filtered by user role and permissions

**Key Security Features:**
- JWT tokens issued by Supabase Auth service
- Automatic token refresh mechanism
- Email verification for new accounts
- Role-based endpoint protection
- User profiles linked to authentication

## Project Structure

```
Iksan-AI-Interview-Backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py          # FastAPI dependencies & auth
│   │   └── v1/
│   │       ├── router.py            # API route configuration
│   │       └── endpoints/           # API route handlers
│   │           ├── auth.py          # Authentication endpoints
│   │           ├── students.py      # Student management
│   │           ├── teachers.py      # Teacher management
│   │           ├── classes.py       # Class management
│   │           ├── schools.py       # School management
│   │           ├── majors.py        # Major/specialization management
│   │           ├── roles.py         # Role management
│   │           ├── users.py         # User profiles
│   │           ├── interview_sessions.py  # Interview session lifecycle
│   │           └── feedback.py      # Feedback generation & retrieval
│   ├── core/
│   │   ├── config.py               # Configuration settings (env vars)
│   │   ├── database.py             # Supabase client dependency (via app.state)
│   │   └── security.py             # JWT validation & auth helpers
│   ├── main.py                     # FastAPI app with lifespan management
│   ├── services/
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── student_service.py      # Student data operations
│   │   ├── teacher_service.py      # Teacher data operations
│   │   ├── user_service.py         # User profile management
│   │   ├── class_service.py        # Class management
│   │   ├── document_service.py     # Document storage & retrieval
│   │   ├── text_extraction_service.py  # PDF/DOCX/TXT/MD extraction
│   │   ├── interview_session_service.py # Session management
│   │   ├── feedback_service.py     # Feedback generation
│   │   ├── storage_service.py      # File validation & security
│   │   └── ...
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── auth.py                 # Auth schemas
│   │   ├── user.py                 # User schemas
│   │   ├── student.py              # Student schemas
│   │   ├── document.py             # Document schemas
│   │   ├── interview_session.py    # Session schemas
│   │   ├── detailed_feedback.py    # Detailed feedback with scores
│   │   └── ...
│   └── main.py                     # FastAPI application entry point
├── docs/
│   ├── DB_SCHEMA.md               # Database schema (ERD)
│   ├── DATABASE_SETUP_GUIDE.md    # Setup instructions
│   ├── SUPABASE_AUTH_IMPLEMENTATION_SUMMARY.md
│   ├── TEXT_EXTRACTION_IMPLEMENTATION.md
│   └── ...
├── migrations/                     # 🆕 Database migration system
│   ├── APPLIED_MIGRATIONS.md      # Tracks applied migrations (commit to git)
│   ├── README.md                  # Migration system documentation
│   ├── 001_initial_schema.sql     # Initial database schema
│   ├── 001_initial_schema.down.sql # Rollback for initial schema
│   ├── 002_seed_reference_data.sql # Reference data seeding
│   └── 002_seed_reference_data.down.sql
├── queries/
│   ├── initialize_tables.sql      # Legacy: Database initialization
│   └── ...
├── scripts/
│   ├── migrate.py                 # 🆕 Migration management CLI
│   ├── init_db.py                 # Legacy: Database setup automation
│   └── reset_db.py                # Database hard reset script (dev only)
├── tests/
│   ├── test_setup.py              # Setup validation tests
│   ├── test_supabase_connection.py # Database connection tests
│   └── ...
├── .env                           # Environment variables (not in git)
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Core Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.121.3+ |
| Server | Uvicorn | 0.38.0+ |
| Database | Supabase (PostgreSQL) | 2.9.0+ |
| Authentication | Supabase Auth + JWT | Built-in |
| Document Processing | PyMuPDF, python-docx | 1.26.6+, 1.2.0+ |
| ORM/Query | Python (direct Supabase client) | - |
| Validation | Pydantic | 2.x |
| Python | CPython | 3.10+ |

## Testing

### Run Setup Test

```bash
python ./tests/test_setup.py
```

**Expected output:**
```
✅ PASS - Configuration
✅ PASS - Supabase Client
✅ PASS - Auth Methods
✅ PASS - Table Methods
✅ PASS - Module Imports
✅ PASS - FastAPI App

Total: 6 | Passed: 6 | Failed: 0
```

### Run Database Connection Test

```bash
python ./tests/test_supabase_connection.py
```


## Additional Documentation

- [DATABASE_SETUP_GUIDE.md](docs/DATABASE_SETUP_GUIDE.md) - Database initialization
- [SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md) - Security considerations
- [PERFORMANCE_REVIEW.md](docs/PERFORMANCE_REVIEW.md) - Performance optimization
- [INTERVIEW_SESSION_INITIATION.md](docs/INTERVIEW_SESSION_INITIATION.md) - Session workflow

## Deployment

### Deploy to Railway

This project is configured for easy deployment to [Railway](https://railway.app).

#### Option 1: Deploy from GitHub (Recommended)

1. Push your code to GitHub
2. Go to [Railway Dashboard](https://railway.app/dashboard)
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your repository
5. Railway will auto-detect the `railway.json` configuration
6. Set the required environment variables in the Railway dashboard:
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase anon/public key
   - `LLM_API_KEY` - Your LLM API key (if using AI features)
7. Deploy!

#### Option 2: Deploy using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (in your repo directory)
railway init

# Deploy
railway up
```

#### Option 3: Manual Configuration

If not using `railway.json`, configure in the Railway dashboard:

1. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
2. **Health Check Path:** `/health`

#### Post-Deployment

After deployment:

1. Go to **Settings** → **Networking** → **Generate Domain** to get a public URL
2. Verify your service is running:
   - **Health Check:** `https://your-app.up.railway.app/health`
   - **API Docs:** `https://your-app.up.railway.app/docs`

