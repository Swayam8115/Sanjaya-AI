from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os
os.makedirs("generated_reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="generated_reports"), name="reports")

class ChatRequest(BaseModel):
    query: str

async def event_stream(query: str):
    """Stream events as they happen"""
    
    # Import here to avoid circular imports
    from app.agents.master_agent import run_master_agent_streaming
    
    try:
        async for event in run_master_agent_streaming(query):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        error_event = {
            "type": "error",
            "message": str(e)
        }
        yield f"data: {json.dumps(error_event)}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"Received query: {request.query}")
        return StreamingResponse(
            event_stream(request.query),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)