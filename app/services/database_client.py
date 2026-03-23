# This file is responsible for talking to the database service.
# It sends requests to the database API and receives data.
# Other parts of the system (like memory or AI logic) use this file
# instead of directly calling the database.


import requests

# Used to define data types (for better code clarity)
from typing import List, Dict

# Import logger to record system activity and errors
from app.core.logger import logger


# Base URL of the database service
# This is the address where the database API is running.
BASE_URL = "https://test21.fireai.agency"

# Timeout for API requests (in seconds)
# If the database does not respond within 5 seconds, the request will fail.
TIMEOUT = 5


# -------------------------------------------------
# Function: get_user_messages
# -------------------------------------------------
# This function gets conversation messages for a specific user.
# It sends a request to the database and returns the messages.
def get_user_messages(user_id: str) -> List[Dict]:

    # Build the API URL
    # Example:
    # http://172.252.13.97:8004/api/admin/user-instances/for-ai/demo-user
    url = f"{BASE_URL}/api/admin/user-instances/for-ai/{user_id}"

    try:
        # Log that we are requesting data
        logger.info(f"Fetching messages for user_id={user_id}")

        # Send GET request to database service
        response = requests.get(url, timeout=TIMEOUT)

        # If response is not successful (not 200), raise an error
        response.raise_for_status()

        # Convert response into JSON format
        json_resp = response.json()

        # Check if the returned data is a dict
        if not isinstance(json_resp, dict) or "data" not in json_resp:
            logger.warning("Invalid response format from database, expected dict with 'data'")
            return []
            
        messages = json_resp.get("data", [])
        if not isinstance(messages, list):
            logger.warning("Invalid messages format from database")
            return []

        # Return the message list
        return messages

    # If request takes too long
    except requests.exceptions.Timeout:
        logger.error("Database request timed out")
        return []

    # If there is any network or HTTP error
    except requests.exceptions.RequestException as e:
        logger.error(f"Database request failed: {e}")
        return []

    # Catch any unexpected error
    except Exception as e:
        logger.error(f"Unexpected error in get_user_messages: {e}")
        return []