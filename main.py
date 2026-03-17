# Import FastAPI framework
from fastapi import FastAPI
from datetime import datetime
import uuid
from pydantic import BaseModel
from typing import Optional

from app.orchestrator.agent_runner import run_agent
from app.core.logger import logger


# --------------------------------------------------
# Request Model (Production Standard)
# --------------------------------------------------
class ChatRequest(BaseModel):
    user_query: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None  # ✅ Added for multi-user support


# Create FastAPI app
app = FastAPI()


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI Agent Service Running"}


# --------------------------------------------------
# AI Chat Endpoint
# --------------------------------------------------
@app.post(
    "/chat",
    summary="AI Chat Endpoint",
    description="""
AI chat endpoint with memory + LLM pipeline
"""
)
def chat(request: ChatRequest):

    try:
        # --------------------------------------------------
        # Extract Request Data
        # --------------------------------------------------
        user_query = request.user_query
        conversation_id = request.conversation_id
        user_id = request.user_id or "anonymous-user"  # ✅ FIX

        # --------------------------------------------------
        # Generate Conversation ID
        # --------------------------------------------------
        if not conversation_id:
            conversation_id = f"conv_{uuid.uuid4().hex[:10]}"

        # --------------------------------------------------
        # Run AI Orchestrator
        # --------------------------------------------------
        result = run_agent(user_query, user_id=user_id)

        # --------------------------------------------------
        # Extract Data from Orchestrator
        # --------------------------------------------------
        ai_response = result.get("reply")
        memory_info = result.get("memory", {})
        usage_info = result.get("usage", {})
        model_info = result.get("model", "unknown")

        # --------------------------------------------------
        # Handle orchestrator failure
        # --------------------------------------------------
        if result.get("error"):
            return {
                "success": False,
                "error": "AI processing failed",
                "meta": {
                    "conversation_id": conversation_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        # --------------------------------------------------
        # Return API Response (Improved but compatible)
        # --------------------------------------------------
        return {
            "success": True,
            "message": "AI response generated successfully",
            "data": {
                "conversation_id": conversation_id,
                "role": "ASSISTANT",
                "user_query": user_query,  # optional (keep for now)
                "content": ai_response,
                "agent": {
                    "agent_name": "sales_agent"
                },
                "memory": memory_info,
                "usage": usage_info,
                "timestamp": datetime.utcnow().isoformat()
            },
            "meta": {
                "model": model_info
            }
        }

    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)

        return {
            "success": False,
            "error": "Internal server error",
            "meta": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }