# -------------------------------------------------
# Database Client Layer
# -------------------------------------------------
# This file handles ALL communication with the external database API.
# No other module should directly call external APIs.
# This ensures clean architecture and easy maintainability.

import requests
from typing import List, Dict, Any
from app.core.logger import logger


# -------------------------------------------------
# Configuration
# -------------------------------------------------

BASE_URL = "https://test21.fireai.agency"
TIMEOUT = 5


# -------------------------------------------------
# Function: get_user_messages
# -------------------------------------------------
# Fetch short-term conversation memory (instance memory)
# Used by orchestrator to load recent chat history
def get_user_messages(user_id: str) -> List[Dict[str, Any]]:

    url = f"{BASE_URL}/api/admin/user-instances/for-ai/{user_id}"

    try:
        logger.info(f"[DB] Fetching messages for user_id={user_id}")
        logger.debug(f"[DB URL] {url}")

        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json().get("data",[])

        json_resp = response.json()
        logger.info(f"RAW DB RESPONSE: {json_resp}") 

        # Validate structure
        if not isinstance(json_resp, dict) or "data" not in json_resp:
            logger.warning("[DB] Invalid response format (missing 'data')")
            return []

        messages = json_resp.get("data", [])

        if not isinstance(messages, list):
            logger.warning("[DB] Messages is not a list")
            return []

        logger.info(f"[DB] Retrieved {len(messages)} messages")

        return messages

    except requests.exceptions.Timeout:
        logger.error("[DB ERROR] get_user_messages timeout")
        return []

    except requests.exceptions.RequestException as e:
        logger.error(f"[DB ERROR] get_user_messages failed: {e}")
        raise

    except Exception as e:
        logger.error(f"[DB ERROR] Unexpected error: {e}", exc_info=True)
        return []


# -------------------------------------------------
# Function: get_user_profile
# -------------------------------------------------
# Fetch long-term identity (name, role, etc.)
# REQUIRED for orchestrator (Identity injection)
def get_user_profile(user_id: str) -> Dict[str, Any]:

    # NOTE:
    # API returns ALL users → we filter locally
    # Better approach: ask backend for /users/{id}

    url = f"{BASE_URL}/api/admin/users/for-ai"

    try:
        logger.info(f"[DB] Fetching users list to find user_id={user_id}")
        logger.debug(f"[DB URL] {url}")

        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        json_resp = response.json()

        users = json_resp.get("data", [])

        if not isinstance(users, list):
            logger.warning("[DB] Invalid users format")
            return {}
        # 🔥 filter by user_id
        user = next((u for u in users if u.get("id") == user_id), None)

        # 🔥 Find matching user
        user = next((u for u in users if u.get("id") == user_id), None)

        if not user:
            logger.warning(f"[DB] User not found: {user_id}")  
            return {}

        profile = {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "language": user.get("language"),
            "designation": user.get("designation"),
        }

        logger.info(f"[DB] User loaded: {profile.get('name')}")

        return profile

    except requests.exceptions.Timeout:
        logger.error("[DB ERROR] get_user_profile timeout")
        return {}

    except requests.exceptions.RequestException as e:
        logger.error(f"[DB ERROR] get_user_profile failed: {e}")
        return {}

    except Exception as e:
        logger.error(f"[DB ERROR] Unexpected error: {e}", exc_info=True)
        return {}


# -------------------------------------------------
# Local Test Runner (for debugging only)
# -------------------------------------------------
# Run using:
# python -m app.services.database_client
# if __name__ == "__main__":

#     test_user_id = "caa3abb6-c2cc-426e-9ee3-dad32aa31883"  # use real id

#     print("\n--- Testing get_user_profile ---") 
#     profile = get_user_profile(test_user_id)
#     print(profile)

#     print("\n--- Testing get_user_messages ---")
#     messages = get_user_messages(test_user_id)
#     print(f"Messages count: {len(messages)}")