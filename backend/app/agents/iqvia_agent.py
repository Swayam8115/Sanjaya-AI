from pydantic_ai import Agent
from app.utils.prompts import IQVIA_SYSTEM_PROMPT
from app.tools.supabase_tool import run_query
import asyncio
from pydantic import BaseModel

class SQLQuery(BaseModel):
    sql: str

iqvia_agent = Agent(
    model="google-gla:gemini-2.0-flash",
    system_prompt=IQVIA_SYSTEM_PROMPT,
    retries=2,
)
from pydantic_ai import RunContext
import json

@iqvia_agent.tool_plain
def process_sql(response: str):
    """
    Cleans LLM JSON output, extracts SQL, and executes it in Supabase.
    """
    # Remove markdown fences if present
    cleaned = response.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(cleaned)
        sql = parsed["query_supabase"]["sql"]
    except Exception as e:
        return {"error": f"Failed to parse SQL from LLM: {e}", "raw": cleaned}

    # Now run the actual query
    return run_query(sql)

@iqvia_agent.tool_plain
def query_supabase(sql: str):
    """
    Executes a SQL query on the Supabase table `iqvia_sales`.

    REQUIRED USAGE:
    - This tool MUST be called whenever a SQL query is needed.
    - The `sql` argument must be a complete SQL SELECT statement.
    - Only valid columns are allowed:
        molecule, region, sales_value, sales_volume, cagr, competitors, atc_code, year.

    FORMAT FOR TOOL CALL:
    {
      "query_supabase": {
        "sql": "<SQL QUERY HERE>"
      }
    }

    DO NOT wrap output in markdown.
    DO NOT use code fences.
    DO NOT output explanation or natural language.

    This tool returns the result rows from Supabase as JSON.
    """
    return run_query(sql)

async def run_agent():
    print("\nIQVIA Insights Agent")
    user_query = input("Enter your query: ")

    print("\nRunning agent...")
    response = await iqvia_agent.run(user_query)   

    print("\n🎯 Agent Final Output:")
    print(response.output)


def main():
    asyncio.run(run_agent())  


if __name__ == "__main__":
    main()
