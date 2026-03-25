from typing import List, Dict, Any
import httpx
from app.core.logger import logger

BASE_URL = "https://test21.fireai.agency/api"
TIMEOUT = 5


async def get_conversation_history(
    user_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch recent conversation history (short-term memory)
    """

    url = f"{BASE_URL}/admin/user-instances/for-ai/{user_id}"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            res = await client.get(url)
            res.raise_for_status()

        data = res.json()
        messages = data.get("data", [])

        if not isinstance(messages, list):
            logger.warning("[CONVERSATION] Invalid format")
            return []

        # -----------------------------
        # Normalize (important)
        # -----------------------------
        normalized = []

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            if msg.get("userQuery"):
                normalized.append({
                    "role": "user",
                    "content": str(msg["userQuery"]).strip()
                })

            if msg.get("aiResponse"):
                normalized.append({
                    "role": "assistant",
                    "content": str(msg["aiResponse"]).strip()
                })

        # -----------------------------
        # Limit
        # -----------------------------
        return normalized[-limit:]

    except httpx.TimeoutException:
        logger.error("[CONVERSATION] Timeout")
        return []

    except httpx.RequestError as e:
        logger.error(f"[CONVERSATION] Request failed: {e}")
        return []

    except Exception as e:
        logger.error(f"[CONVERSATION] Unexpected error: {e}", exc_info=True)
        return []