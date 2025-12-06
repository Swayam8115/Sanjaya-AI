from supabase import create_client
from app.config.settings import settings

url = settings.SUPABASE_URL
key = settings.SUPABASE_KEY
supabase = create_client(url, key)

def run_query(sql: str):
    try:
        result = supabase.rpc("exec_sql", {"query": sql}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}
