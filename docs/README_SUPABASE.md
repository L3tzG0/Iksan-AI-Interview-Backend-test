# Iksan AI Interview Backend - Supabase Setup

## Quick Start

This project uses the official Supabase Python client for authentication and database operations.

### Prerequisites
- Python 3.10+
- Supabase account
- Supabase project created

### Installation

1. Clone the repository
```bash
git clone <your-repo-url>
cd Iksan-AI-Interview-Backend
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
# Create .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

5. Run the application
```bash
uvicorn app.main:app --reload
```

## Architecture

### Authentication Flow
```
Client Request → FastAPI Endpoint → Supabase Auth → JWT Validation → Protected Resource
```

### Database Flow
```
Client Request → FastAPI Endpoint → Supabase Client → PostgreSQL → Response
```

## Key Features

### ✅ Supabase Auth Integration
- Email/Password authentication
- JWT token management
- User metadata support
- Automatic session handling

### ✅ Database Operations
- CRUD operations via Supabase client
- Type-safe queries
- Automatic API generation
- Row Level Security support

### ✅ FastAPI Integration
- OpenAPI documentation
- Dependency injection
- Type hints
- Async support

## API Documentation

Once running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Project Structure

```
app/
├── api/
│   ├── dependencies.py       # FastAPI dependencies
│   └── v1/
│       ├── endpoints/         # API endpoints
│       │   ├── auth.py        # Authentication endpoints
│       │   ├── students.py
│       │   └── teachers.py
│       └── router.py
├── core/
│   ├── config.py             # Configuration settings
│   ├── database.py           # Supabase client setup
│   └── security.py           # JWT validation
├── models/                   # Pydantic models (removed SQLAlchemy)
├── schemas/                  # Request/Response schemas
├── services/                 # Business logic
│   ├── auth_service.py       # Supabase Auth operations
│   ├── user_service.py       # User CRUD
│   └── ...
└── main.py                   # FastAPI application
```


## Testing

### Manual Testing with curl

**Register:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123",
    "full_name": "Test User",
    "role_id": 1
  }'
```

**Login:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123"
  }'
```

**Protected Route:**
```bash
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJhbGc...` |

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use RLS policies** - Protect your data at database level
3. **Validate input** - Use Pydantic schemas
4. **HTTPS only in production** - Protect JWT tokens
5. **Rotate keys regularly** - In Supabase Dashboard

## Common Operations

### Adding a New Table

1. Create table in Supabase Dashboard
2. Create Pydantic schema in `app/schemas/`
3. Create service in `app/services/`
4. Create endpoints in `app/api/v1/endpoints/`
5. Register router in `app/api/v1/router.py`

### Example Service
```python
from supabase import Client

class ExampleService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def create(self, data: dict):
        response = self.supabase.table('examples').insert(data).execute()
        return response.data[0]
    
    async def get(self, id: int):
        response = self.supabase.table('examples').select('*').eq('id', id).execute()
        return response.data[0] if response.data else None
```

## Deployment

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables in Production
- Use secrets management (AWS Secrets Manager, etc.)
- Never hardcode credentials
- Use `service_role` key for admin operations (backend only)

## Troubleshooting

**Problem:** "Could not validate credentials"
- Check if token is expired
- Verify token format: `Bearer <token>`
- Ensure `SUPABASE_KEY` is correct

**Problem:** "Table does not exist"
- Create table in Supabase Dashboard
- Check table name spelling
- Verify schema is `public`

**Problem:** "Row Level Security policy violation"
- Check RLS policies in Supabase
- Ensure user is authenticated
- Verify policy conditions

## Support

- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Project Issues](link-to-your-issues)
