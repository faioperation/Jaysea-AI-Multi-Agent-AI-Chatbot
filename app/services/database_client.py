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
BASE_URL = "http://172.252.13.97:8004"

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
    # http://172.252.13.97:8004/instances/demo-user/messages
    url = f"{BASE_URL}/instances/{user_id}/messages"

    try:
        # Log that we are requesting data
        logger.info(f"Fetching messages for user_id={user_id}")

        # Send GET request to database service
        response = requests.get(url, timeout=TIMEOUT)

        # If response is not successful (not 200), raise an error
        response.raise_for_status()

        # Convert response into JSON format
        data = response.json()

        # Check if the returned data is a list
        # Expected format:
        # [
        #   {"role": "user", "content": "Hello"},
        #   {"role": "assistant", "content": "Hi"}
        # ]
        if not isinstance(data, list):
            logger.warning("Invalid response format from database")
            return []

        # Return the message list
        return data

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