from openai import OpenAI
from app.config.settings import settings
import json
from app.tools.supabase_tool import run_query
from app.utils.prompts import IQVIA_SYSTEM_PROMPT
from .base_agent import BaseAgent

client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_supabase",
            "description": "Execute SQL query on the iqvia_sales table.",
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

def handle_user_query(user_query: str):

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": IQVIA_SYSTEM_PROMPT},
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

        print("LLM called tool:", fn_name)
        print("Args:", args)

        # Execute the tool
        sql = args["sql"]
        result = run_query(sql)

        return {
            "sql": sql,
            "result": result
        }

    # If no tool was called
    return {"response": message["content"]}

class IQVIAAgent(BaseAgent):

    async def run(self, query: str, context=None):

        # print("IQVIA Insights Agent CALLED")
        result = handle_user_query(query)

        return {
            "agent": "IQVIA Insights Agent",
            "output": result
        }

def main():
    print("\nIQVIA Insights Agent — CLI Mode")
    user_query = input("\nEnter your query: ")

    output = handle_user_query(user_query)

    print("\nFinal Output:")
    print(output)


if __name__ == "__main__":
    main()
