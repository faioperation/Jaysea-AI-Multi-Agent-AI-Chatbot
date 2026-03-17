# Orchestrator: Main AI controller

from app.context.prompt_builder import build_prompt
from app.core.logger import logger
from app.llm.openai_adapter import generate_response

# DB integrations
from app.memory.memory_service import get_instance_messages
from app.services.experience_api import search_experience


def run_agent(user_query: str, user_id: str = "demo-user") -> dict:
    """
    Runs the full AI pipeline and returns structured output
    """

    try:
        logger.info("Starting AI agent pipeline")

        # -----------------------------
        # 1. Agent Config
        # -----------------------------
        identity = "You are a helpful AI assistant."
        behaviour = "Be clear, concise, and professional."

        # -----------------------------
        # 2. Short-term Memory (conversation)
        # -----------------------------
        try:
            conversation = get_instance_messages(user_id)
        except Exception as e:
            logger.error(f"Conversation fetch failed: {str(e)}")
            conversation = []

        # Limit memory (IMPORTANT)
        conversation = conversation[-5:]

        short_term_memory_used = bool(conversation)

        logger.info(f"Loaded {len(conversation)} conversation messages")

        # -----------------------------
        # 3. Long-term Memory (experience search)
        # -----------------------------
        try:
            experience_data = search_experience(user_query)
            experience = [item.get("content", "") for item in experience_data]
        except Exception as e:
            logger.error(f"Experience search failed: {str(e)}")
            experience = []

        long_term_memory_used = bool(experience)

        # -----------------------------
        # 4. Build Prompt
        # -----------------------------
        prompt = build_prompt(
            identity=identity,
            behaviour=behaviour,
            experience=experience,
            conversation=conversation,
            user_query=user_query
        )

        logger.info("Prompt successfully built")
        logger.debug(f"Prompt preview: {prompt[:300]}")

        # -----------------------------
        # 5. Call LLM
        # -----------------------------
        llm_response = generate_response(prompt)

        logger.info("AI response generated")

        # -----------------------------
        # 6. Output cleaning
        # -----------------------------
        reply = ""

        if isinstance(llm_response, dict):
            reply = (llm_response.get("content") or "").strip()
        elif isinstance(llm_response, str):
            reply = llm_response.strip()

        if not reply:
            reply = "I'm not sure how to respond to that."

        # -----------------------------
        # Return Structured Response
        # -----------------------------
        return {
            "reply": reply,
            "usage": llm_response.get("usage", {}) if isinstance(llm_response, dict) else {},
            "model": llm_response.get("model", "unknown") if isinstance(llm_response, dict) else "unknown",
            "memory": {
                "short_term_used": short_term_memory_used,
                "long_term_used": long_term_memory_used
            }
        }

    except Exception as e:
        logger.error(f"Agent pipeline failed: {str(e)}", exc_info=True)

        return {
            "reply": "Sorry, something went wrong while processing your request.",
            "usage": {},
            "model": "unknown",
            "memory": {
                "short_term_used": False,
                "long_term_used": False
            },
            "error": True
        }