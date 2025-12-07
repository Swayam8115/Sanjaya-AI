import json
from openai import OpenAI
import google.generativeai as genai
import pathlib
from app.config.settings import settings
from app.utils.prompts import INTERNAL_KNOWLEDGE_SYSTEM_PROMPT
from app.tools.internal_doc_tool import list_documents,load_document_file,generate_briefing_pdf
from .base_agent import BaseAgent

client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)



def internal_agent(user_query: str):
    """Runs internal knowledge agent with tool calling."""

    available_docs = list_documents()

    tools=[
            {
                "type": "function",
                "function": {
                    "name": "load_document_file",
                    "description": "Load a document file for analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {"type": "string"}
                        },
                        "required": ["file_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_briefing_pdf",
                    "description": "Generate final combined PDF",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "takeaways": {"type": "string"},
                            "table": {"type": "string"}
                        },
                        "required": ["summary", "takeaways", "table"]
                    }
                }
            }
        ]

    # First LLM call — choose document & analyze
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": INTERNAL_KNOWLEDGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"User query: {user_query}\nAvailable documents: {available_docs}"}
        ],
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message

    # Handle tool calls
    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if fn_name == "load_document_file":
            BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # backend/app
            DATA_DIR = BASE_DIR / "data"  # backend/app/data
            filepath = DATA_DIR / args["file_name"]
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response_g = model.generate_content(
                [
                    {
                        "mime_type": "application/pdf",
                        "data": filepath.read_bytes(),
                    },
                    f"Use the user's query ({user_query}) as the focus of your analysis. Extract information from the document and produce: a summary, key takeaways, and a structured table relevant to that query."
                ]
            )

            print("Document Parsed and summarized")


            analysis = response_g.text
            # Now ask LLM to call the PDF generation tool
            pdf_response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": INTERNAL_KNOWLEDGE_SYSTEM_PROMPT},
                {"role": "assistant", "content": analysis},
                {"role": "user", "content": "Generate the corporate PDF briefing now using the tool."}
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "generate_briefing_pdf",
                        "description": "Create PDF report",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string"},
                                "takeaways": {"type": "string"},
                                "table": {"type": "string"}
                            },
                            "required": ["summary", "takeaways", "table"]
                        }
                    }
                }
            ],
            tool_choice="auto"
        )

        # If tool didn't trigger — fail early with a meaningful message
        message = pdf_response.choices[0].message

        if message.tool_calls is None:
            raise ValueError("Model did not call the PDF tool. Last message:\n" + message.content)

        pdf_call = message.tool_calls[0]
        pdf_args = json.loads(pdf_call.function.arguments)

        return generate_briefing_pdf(**pdf_args)

    return msg.content

class InternalKnowledgeAgent(BaseAgent):

    async def run(self, query: str, context=None):
        # print("Internal Knowledge Agent CALLED")
        output = internal_agent(query)

        return {
            "agent": "Internal Knowledge Agent",
            "output": output
        }


def main():
    print("\nInternal Knowledge Agent")
    query = input("Enter your query: ")

    result = internal_agent(query)

    print("\nFinal Output:")
    print(result)


if __name__ == "__main__":
    main()
