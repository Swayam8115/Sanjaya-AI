from openai import OpenAI
from app.config.settings import settings
import json
from app.tools.supabase_tool import run_query
from app.utils.prompts import PATENT_SYSTEM_PROMPT

client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_supabase",
            "description": "Execute SQL query on the patents table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                },
                "required": ["sql"]
            }
        }
    }
]

def handle_patent_query(user_query: str):
    print(f"User Query: {user_query}")

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": PATENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        tools=tools,
        tool_choice="auto"  
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        fn_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Agent decided to call: {fn_name}")
        print(f"SQL generated: {args.get('sql')}")

        if fn_name == "query_supabase":
            sql = args["sql"]
            result = run_query(sql)
            return {
                "sql": sql,
                "data": result
            }

    return {"response": message.content}

def main():
    user_query="Give me active patents for Semaglutide"
    output = handle_patent_query(user_query)
    print(output)
if __name__ == "__main__":
    main()