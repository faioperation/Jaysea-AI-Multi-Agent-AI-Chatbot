# app/llm/openai_adapter.py

from typing import Dict, Any
import os
from dotenv import load_dotenv
from openai import OpenAI
from app.core.logger import logger


# -------------------------------------------------
# Load Environment Variables
# -------------------------------------------------
load_dotenv()  # loads .env file


# -------------------------------------------------
# Validate API Key (CRITICAL)
# -------------------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set. Check your .env file.")


# -------------------------------------------------
# Create OpenAI Client (Singleton)
# -------------------------------------------------
client = OpenAI(
    api_key=API_KEY,
    timeout=10  # global timeout
)


# -------------------------------------------------
# Function: generate_response
# -------------------------------------------------
def generate_response(prompt: str) -> Dict[str, Any]:
    """
    Sends prompt to OpenAI and returns structured response

    Args:
        prompt (str): Final prompt string

    Returns:
        dict: {
            content: str,
            usage: dict,
            model: str
        }
    """

    try:
        logger.info("[LLM] Sending request to OpenAI")

        response = client.chat.completions.create(
            model="gpt-4o-mini",

            # IMPORTANT: Only user message (system already in prompt)
            messages=[
                {"role": "user", "content": prompt}
            ],

            max_tokens=300,  # cost control
        )

        # -------------------------------------------------
        # Safe Extraction
        # -------------------------------------------------
        content = ""

        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""

        logger.info("[LLM] Response received")

        return {
            "content": content.strip(),

            "usage": {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            },

            "model": response.model
        }

    except Exception as e:
        logger.error(f"[LLM ERROR] {str(e)}", exc_info=True)

        # Fail-safe response
        return {
            "content": "I don't know",
            "usage": {},
            "model": "error"
        }