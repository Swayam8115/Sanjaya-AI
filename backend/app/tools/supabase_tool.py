from supabase import create_client
from app.config.settings import settings
import os

url = settings.SUPABASE_URL
key = settings.SUPABASE_KEY
supabase = create_client(url, key)

def run_query(sql: str):
    """Execute SQL on Supabase Postgres."""
    try:
        result = supabase.postgrest.rpc("exec_sql", {"sql": sql}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}
