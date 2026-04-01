import os
from openai import OpenAI
from typing import List
from dotenv import load_dotenv

# Load environment variables (API keys) from the .env file in the root folder.
load_dotenv()

# Get the OpenAI API key from the environment.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI Client. 
# We will use this to convert normal text (like "I love Neymar") into an array of numbers (Vectors).
# Non-technical explanation: AI models can only "understand" numbers, not words. So an Embedding model
# translates a sentence into a list of 1536 numbers, which perfectly captures the meaning of the sentence.
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_embedding(text: str) -> List[float]:
    """
    Function: generate_embedding
    Purpose: To convert human readable text into a Vector (a list of 1536 decimal numbers).
    
    Example Input: "My favorite football player is Neymar."
    Example Output: [0.0123, -0.0456, 0.7890, ... up to 1536 numbers]
    
    Why we need this: We save these numbers in our Pinecone Database. When the user asks a new question,
    we convert the question to numbers too, and compare them. Pinecone finds the numbers that are 
    closest to each other (Semantic Search). This means it understands context, not just keyword matching.
    """
    
    # Check if text is empty to avoid API errors
    if not text or not str(text).strip():
        return []
    
    try:
        # Call OpenAI's API to generate the embedding using their latest small model
        response = client.embeddings.create(
            input=str(text).strip(),
            model="text-embedding-3-small"
        )
        
        # Extract the actual list of numbers from the OpenAI response
        embedding_numbers = response.data[0].embedding
        
        return embedding_numbers
        
    except Exception as e:
        print(f"[EMBEDDING ERROR] Failed to generate embedding: {e}")
        return []
