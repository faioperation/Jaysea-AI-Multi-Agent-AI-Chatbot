import requests
from typing import List, Dict, Any
from app.core.logger import logger

BASE_URL = "https://test21.fireai.agency"
TIMEOUT = 5


def search_experience(
    user_id: str,
    query: str,
    limit: int = 100
) -> List[Dict[str, Any]]:

    url = f"{BASE_URL}/api/experience/user/for-ai/{user_id}?limit=300"

    try:
        logger.info(f"[EXPERIENCE] Fetching user_id={user_id}")

        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        json_resp = response.json()

        data_block = json_resp.get("data", {})
        experience_list = data_block.get("data", [])

        if not isinstance(experience_list, list):
            logger.warning("[EXPERIENCE] Invalid format")
            return []

        # 🔥 Sort by newest first to ensure we prioritize latest memories when filtering
        experience_list.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)

        logger.info(f"[EXPERIENCE] Raw count={len(experience_list)}")

        # FILTER (Modified to avoid strict exact substring match)
        if query:
            query_words = query.lower().split()

            filtered = [
                item for item in experience_list
                if any(word in str(item.get("content", "")).lower() for word in query_words)
            ]
            
            # If no keyword matches, fallback to returning the top experiences anyway for context
            if not filtered:
                filtered = experience_list
        else:
            filtered = experience_list

        logger.info(f"[EXPERIENCE] Filtered count={len(filtered)}")

        return filtered[:limit]

    except Exception as e:
        logger.error(f"[EXPERIENCE ERROR] {e}", exc_info=True)
        return []

# -------------------------------------------------
# SAVE EXPERIENCE (Improved)
# -------------------------------------------------
def save_experience(user_id: str, role: str, content: str) -> bool:
    try:
        payload = {
            "actor": role.lower(),
            "event_type": "message",
            "content": content,
            "user_id": user_id
        }

        response = requests.post(
            f"{BASE_URL}/experience",
            json=payload,
            timeout=3
        )

        if response.status_code not in (200, 201):
            logger.error(f"[EXPERIENCE SAVE] Failed: {response.status_code}")
            return False

        logger.info("[EXPERIENCE SAVE] Success")
        return True

    except Exception as e:
        logger.error(f"[EXPERIENCE SAVE ERROR] {e}", exc_info=True)
        return False