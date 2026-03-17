from typing import List, Dict


def format_conversation(messages: List[Dict]) -> List[Dict]:
    """
    Convert DB messages to LLM-compatible format
    Handles inconsistent DB schemas safely
    """

    allowed_roles = ["user", "assistant", "system"]
    formatted = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        # -----------------------------
        # 1. Normalize role
        # -----------------------------
        role = str(msg.get("role", "")).lower()

        if role not in allowed_roles:
            role = "user"

        # -----------------------------
        # 2. Extract content (robust)
        # -----------------------------
        content = (
            msg.get("content")
            or msg.get("message")
            or msg.get("text")
            or msg.get("body")
            or ""
        )

        content = str(content).strip()

        # -----------------------------
        # 3. Skip empty messages
        # -----------------------------
        if not content:
            continue

        # -----------------------------
        # 4. Append clean message
        # -----------------------------
        formatted.append({
            "role": role,
            "content": content
        })

    return formatted