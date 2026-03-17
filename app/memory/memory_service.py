# This file is responsible for handling memory-related data.
# It acts as a middle layer between the AI system and the database APIs.
# The AI system does NOT directly talk to the database.
# Instead, it uses this file to get clean and structured data.


from typing import List, Dict

# Import function that fetches messages from the database service
# This function sends a request to the database API and returns raw data.
from app.services.database_client import get_user_messages


# -------------------------------------------------
# Function: get_instance_messages
# -------------------------------------------------
# This function retrieves conversation history (short-term memory).
# It loads previous messages of a user and formats them properly
# so the AI model can understand them.
def get_instance_messages(user_id: str) -> List[Dict]:

    try:
        # Step 1: Get raw messages from the database
        messages = get_user_messages(user_id)

        # Step 2: Normalize the data format
        # This is very important because the AI model expects
        # messages in a specific format: role + content
        normalized_messages = []

        all_raw_messages = []
        for instance in messages:
            if isinstance(instance, dict):
                all_raw_messages.extend(instance.get("messages", []))

        # Sort messages chronologically
        all_raw_messages.sort(key=lambda x: x.get("createdAt", ""))

        for msg in all_raw_messages:
            # Each message is converted into a clean structure
            role = str(msg.get("role", "user")).lower()
            if role == "assistant":
                role = "assistant"
            elif role == "user":
                role = "user"

            normalized_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        # Return cleaned conversation history
        return normalized_messages

    except Exception as e:
        # If something goes wrong (API error, network issue, etc.),
        # we log the error and return an empty list.
        print(f"[Memory Service Error] get_instance_messages: {e}")
        return []


# -------------------------------------------------
# Function: search_experience
# -------------------------------------------------
# This function retrieves long-term memory (past experiences).
# Right now, it is using sample (mock) data.
# Later, it will connect to a real database or vector search system.
def search_experience(query: str) -> List[str]:

    # TODO: Replace this with real database or vector search API
    # Example: db_search_experience(query)

    # Return example past experiences
    return [
        "User previously asked about contract review",
        "Agent generated NDA summary"
    ]