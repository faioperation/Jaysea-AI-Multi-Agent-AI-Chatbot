from typing import List, Dict
from app.core.logger import logger
from app.services.database_client import get_user_messages


def get_instance_messages(user_id: str, limit: int = 5) -> List[Dict]:
    try:
        logger.info(f"[MEMORY] Fetching messages for user_id={user_id}")

        messages = get_user_messages(user_id)

        if not messages:
            logger.warning("[MEMORY] No messages found")
            return []

        logger.debug(f"[MEMORY RAW SAMPLE] {messages[:2]}")

        normalized = []

        for i, instance in enumerate(messages):
            if not isinstance(instance, dict):
                logger.debug(f"[MEMORY] Skipped non-dict at index {i}")
                continue

            user_msg = (
                instance.get("userQuery")
                or instance.get("user_query") 
                or instance.get("message")
            )

            ai_msg = (
                instance.get("aiResponse")
                or instance.get("ai_response")
            )

            if user_msg:
                normalized.append({
                    "role": "user",
                    "content": str(user_msg).strip()
                })

            if ai_msg:
                normalized.append({
                    "role": "assistant",
                    "content": str(ai_msg).strip()
                })

        logger.info(
            f"[MEMORY] Normalized={len(normalized)} | Returned={min(len(normalized), limit)}"
        )

        return normalized[-limit:]

    except Exception as e:
        logger.error(f"[MEMORY ERROR] {e}", exc_info=True)
        return []