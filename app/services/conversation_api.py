# app/services/conversation_api.py

import requests
from app.core.logger import logger

BASE_URL = "https://test21.fireai.agency/api"


def get_conversation_history(user_id: str):
    try:
        res = requests.get(
            f"{BASE_URL}/admin/user-instances/for-ai/{user_id}",
            timeout=3
        )

        res.raise_for_status()  # ✅ important
        data = res.json()

        messages=data.get("data",[])

        if not isinstance(messages, list):
            return []

        return messages

    except Exception as e:
        logger.error(f"Conversation API failed: {str(e)}")
        return []