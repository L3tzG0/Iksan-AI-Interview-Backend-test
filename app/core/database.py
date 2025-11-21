from supabase import create_client, Client
from app.core.config import settings

# Create Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Dependency to get Supabase client
def get_supabase() -> Client:
    """
    Dependency to get Supabase client instance.
    This replaces the SQLAlchemy session dependency.
    """
    return supabase
