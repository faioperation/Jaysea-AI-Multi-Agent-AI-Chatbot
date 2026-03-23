import requests
from app.core.logger import logger

BASE_URL = "https://test21.fireai.agency/api"


# -------------------------------------------------
# SEARCH EXPERIENCE (Long-term memory)
# -------------------------------------------------
def search_experience(query: str):
    try:
        res = requests.get(
            f"{BASE_URL}/experience/search",
            params={
                "q": query,
                "limit": 5
            },
            timeout=3
        )

        res.raise_for_status()

        data = res.json()

        # Handle both formats
        if isinstance(data, list):
            return data

        return data.get("data", [])

    except Exception as e:
        logger.error(f"Experience search failed: {str(e)}")
        return []


# -------------------------------------------------
# SAVE EXPERIENCE (Long-term memory write)
# -------------------------------------------------
def save_experience(user_id: str, role: str, content: str):
    try:
        payload = {
            "actor": role.lower(),        # user / agent
            "event_type": "message",
            "content": content,
            "user_id": user_id
        }

        res = requests.post(
            f"{BASE_URL}/experience",
            json=payload,
            timeout=3
        )

        logger.info(f"Experience saved: {res.status_code}")

    except Exception as e:
        logger.error(f"Experience save failed: {str(e)}")