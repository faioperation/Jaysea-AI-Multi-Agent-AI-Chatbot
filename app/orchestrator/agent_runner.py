# Orchestrator: Main AI controller

from app.context.prompt_builder import build_prompt
from app.core.logger import logger
from app.llm.openai_adapter import generate_response
from app.memory.memory_service import get_instance_messages, search_experience


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
        # 2. Short-term Memory
        # -----------------------------
        conversation = get_instance_messages(user_id)
        short_term_memory_used = bool(conversation)

        # -----------------------------
        # 3. Long-term Memory
        # -----------------------------
        experience = search_experience(user_query)
        long_term_memory_used = bool(experience)

        # -----------------------------
        # 4. Prompt Building
        # -----------------------------
        prompt = build_prompt(
            identity=identity,
            behaviour=behaviour,
            experience=experience,
            conversation=conversation,
            user_query=user_query
        )

        logger.info("Prompt successfully built")

        # -----------------------------
        # 5. LLM Call
        # -----------------------------
        llm_response = generate_response(prompt)

        logger.info("AI response generated")

        # -----------------------------
        # Return Structured Response
        # -----------------------------
        return {
            "reply": llm_response["content"],
            "usage": llm_response.get("usage", {}),
            "model": llm_response.get("model", "unknown"),
            "memory": {
                "short_term_used": short_term_memory_used,
                "long_term_used": long_term_memory_used
            }
        }

    except Exception as e:
        logger.error(f"Agent pipeline failed: {str(e)}", exc_info=True)

        # Important: never crash API
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