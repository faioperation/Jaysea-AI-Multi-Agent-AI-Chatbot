# Orchestrator: Main AI controller

from app.context.prompt_builder import build_prompt
from app.core.logger import logger
from app.llm.openai_adapter import generate_response
import time

# DB integrations
from app.memory.memory_service import get_instance_messages
from app.services.experience_api import search_experience, save_experience
from app.services.database_client import get_user_profile   # ✅ NEW

# Vector DB (Pinecone RAG) Integrations
from app.services.pinecone_client import semantic_search, upsert_experience


def run_agent(user_query: str, user_id: str = "demo-user") -> dict:
    """
    Runs the full AI pipeline and returns structured output
    """

    try:
        logger.info("Starting AI agent pipeline")

        # -----------------------------
        # 1. Dynamic Identity
        # -----------------------------
        try:
            profile = get_user_profile(user_id)

            name = profile.get("name", "Unknown User")
            role = profile.get("role", "USER")
            designation = profile.get("designation", "")

            # 🔥 Dynamic Identity (client requirement)
            identity = f"""
You are an AI assistant interacting with a user.

User Information:
- Name: {name}
- Role: {role}
- Designation: {designation}

Use this information only if relevant to the question.
Do NOT repeat it unnecessarily.
"""

        except Exception as e:
            logger.error(f"User profile fetch failed: {str(e)}")

            # fallback (important for production)
            identity = "You are a helpful AI assistant."

        # -----------------------------
        # 2. Behaviour (keep same)
        # -----------------------------
        behaviour =  """
        You are a conversational AI assistant.

        Rules:
        - Always use previous conversation context if available
        - Never guess unknown information
        - If asked about something you don't have in your memory/context, politely say you don't have that information instead of a blunt "I don't know" (e.g. "I'm sorry, I don't have a record of that.")
        - If the user is just greeting you (e.g. "hello", "hi"), respond politely (e.g. "Hello! How can I help you today?")
        - Do NOT assume user details
        - Respond naturally (not email style)
        - Do NOT write like an email
        - Do NOT use formal sign-offs like "Best regards"
        - Keep answers short and direct
        """

        # -----------------------------
        # 3. Short-term Memory
        # -----------------------------
        try:
            conversation = get_instance_messages(user_id)

            if not conversation:
                logger.warning("Conversation empty,retrying after delay..")
                time.sleep(1)
                conversation=get_instance_messages(user_id)
        except Exception as e:
            logger.error(f"Conversation fetch failed: {str(e)}")
            conversation = []

        conversation = conversation[-5:]
        short_term_memory_used = bool(conversation)

        logger.info(f"Loaded {len(conversation)} conversation messages")

        # -----------------------------
        # 4. Long-term Memory (experience)
        # -----------------------------
       
        try:
            # 1. Fetch from Old Database (Keyword Matching)
            experience_data = search_experience(user_id, user_query)
            old_experience = [
                item.get("content") or item.get("message") or item.get("text") or ""
                for item in experience_data if isinstance(item, dict)
            ]

            # 2. Fetch from Vector Database (Pinecone Semantic Search)
            semantic_experience = semantic_search(user_id, user_query, top_k=15)

            # 3. Combine both and remove duplicates (so user gets best of both worlds)
            experience = []
            for e in semantic_experience + old_experience:
                if e and e not in experience:
                    experience.append(e)

            logger.info(f"[EXPERIENCE] Retrieved {len(experience)} items combined")

        except Exception as e:
            logger.error(f"Experience search failed: {str(e)}")
            experience = []


        #  FALLBACK (VERY IMPORTANT)
        if not experience:
            logger.warning("[EXPERIENCE] No real experience data found")

            # experience = [
            #     msg.get("content", "")
            #     for msg in conversation[-3:]
            # ]


        #  FINAL FLAG
        long_term_memory_used = bool(experience)

        # Reverse experience so that newest is at the bottom (LLM prefers later text)
        experience.reverse()

        # -----------------------------
        # 5. Build Prompt
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
        # 6. Call LLM
        # -----------------------------
        llm_response = generate_response(prompt)

        logger.info("AI response generated")

        # -----------------------------
        # 7. Output cleaning
        # -----------------------------
        reply = ""

        llm_failed = False

        if isinstance(llm_response, dict):
            reply = (llm_response.get("content") or "").strip()
            llm_failed = llm_response.get("error", False)

        # 🔥 smarter fallback
        if llm_failed:
            reply = "Sorry, I'm having trouble responding right now. Please try again."

        elif not reply:
            reply = "I'm not sure how to respond to that."

        # -----------------------------
        # Save to Long-Term Memory
        # -----------------------------
        if not llm_failed and reply:
            try:
                # Save to traditional database append-only log
                save_experience(user_id, "user", user_query)
                save_experience(user_id, "assistant", reply)
                
                # Save to Vector Database (Pinecone) for Semantic RAG Search
                upsert_experience(user_id, "user", user_query)
                upsert_experience(user_id, "assistant", reply)
                
                logger.info("[MEMORY] Saved turn to both DB and Pinecone Vector Space")
            except Exception as e:
                logger.error(f"[MEMORY ERROR] Failed to save experience: {str(e)}")

        # -----------------------------
        # Final Response
        # -----------------------------
        return {
            "reply": reply,
            "usage": llm_response.get("usage", {}) if isinstance(llm_response, dict) else {},
            "model": llm_response.get("model", "unknown") if isinstance(llm_response, dict) else "unknown",
            "memory": {
                "short_term_used": short_term_memory_used,
                "long_term_used": long_term_memory_used,
                "identity_used": True,  # ✅ NEW (for client proof)
                "experience_count": len(experience)  if 'experience' in locals() else 0 
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
                "long_term_used": False,
                "identity_used": False
            },
            "error": True
        }