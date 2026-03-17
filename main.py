# Import FastAPI framework
# FastAPI is used to create web APIs so other systems or users can send requests to our AI service.
from fastapi import FastAPI

# Import datetime to add timestamps to responses
# This helps track when the AI response was generated.
from datetime import datetime

# Import uuid to generate unique conversation IDs
# This ensures each chat session can be tracked separately.
import uuid

# Import Pydantic for request validation (JSON body)
from pydantic import BaseModel
from typing import Optional

# Import the AI orchestrator
# The orchestrator controls the full AI workflow and coordinates all AI components.
from app.orchestrator.agent_runner import run_agent


# --------------------------------------------------
# Request Model (Production Standard)
# --------------------------------------------------
# This defines the expected JSON structure for the /chat endpoint.
class ChatRequest(BaseModel):
    user_query: str
    conversation_id: Optional[str] = None


# Create the FastAPI application
# This represents our AI service backend.
app = FastAPI()


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI Agent Service Running"}


# --------------------------------------------------
# AI Chat Endpoint (Production Version)
# --------------------------------------------------
@app.post(
    "/chat",
    summary="AI Chat Endpoint",
    description="""
This endpoint sends a user message to the AI agent and returns an AI-generated response.

Full AI Pipeline:
1. Load agent configuration
2. Load conversation history
3. Search experience logs
4. Build structured prompt
5. Send prompt to LLM
6. Return generated response
"""
)
def chat(request: ChatRequest):

    # --------------------------------------------------
    # Extract Request Data
    # --------------------------------------------------
    # Get user query and conversation ID from JSON body
    user_query = request.user_query
    conversation_id = request.conversation_id

    # --------------------------------------------------
    # Generate Conversation ID
    # --------------------------------------------------
    # If no conversation ID is provided, create a new one.
    if not conversation_id:
        conversation_id = f"conv_{uuid.uuid4().hex[:10]}"

    # --------------------------------------------------
    # Run the AI Orchestrator
    # --------------------------------------------------
    result = run_agent(user_query)

    # Extract AI response and memory info
    ai_response = result["content"]
    memory_info = result["memory"]

    # --------------------------------------------------
    # Token Usage (Placeholder for now)
    # --------------------------------------------------
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    # --------------------------------------------------
    # Return API Response
    # --------------------------------------------------
    return {
        "success": True,
        "message": "AI response generated successfully",
        "data": {
            "conversation_id": conversation_id,
            "role": "assistant",
            "user_query": user_query,
            "content": ai_response,
            "agent": {
                "agent_name": "Sales_agent"
            },
            "memory": memory_info,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }