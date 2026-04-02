import os
from datetime import datetime
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import Pinecone classes to connect to your Vector Database
from pinecone import Pinecone, ServerlessSpec

# Import our custom embedding function
from app.services.embedding_service import generate_embedding

# We use the central logger so all print statements show up beautifully in the terminal
from app.core.logger import logger

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-agent-memory")

# Create a global pinecone index object so we don't connect every time
_pinecone_index = None

def init_pinecone():
    """
    Function: init_pinecone
    Purpose: To connect to your Pinecone account using your API key. If the index 
             (like a specialized Vector table) doesn't exist, this function creates it automatically!
             
    Why we did this: As you asked, instead of manually clicking "Create Index" in the dashboard, 
    the code checks if it exists. If not, it builds the database for you with dimension 1536!
    """
    global _pinecone_index
    
    # If we already connected, no reason to connect again
    if _pinecone_index is not None:
        return _pinecone_index
        
    try:
        # 1. Connect to Pinecone using the API key
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # 2. Check all the indexes you currently have in your account
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
        
        # 3. If your desired index name is not there, CREATE IT!
        if PINECONE_INDEX_NAME not in existing_indexes:
            logger.info(f"[PINECONE INIT] Creating new index: {PINECONE_INDEX_NAME}. Please wait a few seconds...")
            
            # OpenAI requires a 1536 length vector list
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=1536,
                metric='cosine',  # Cosine means we search based on the angle/similarity between words
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1' # Default region for free tier
                )
            )
            logger.info("[PINECONE INIT] Successfully created the Vector Index!")
            
        else:
            logger.info(f"[PINECONE INIT] Index {PINECONE_INDEX_NAME} already exists. Connected!")
            
        # 4. Save the connection so we can use it to insert and search data later
        _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
        
        return _pinecone_index
        
    except Exception as e:
        logger.error(f"[PINECONE INIT ERROR] {e}")
        return None


def upsert_experience(user_id: str, role: str, content: str) -> bool:
    """
    Function: upsert_experience
    Purpose: To save a new memory (like "I love Toyota") into Pinecone.
    
    Example Input: 
    - user_id: "masum-123"
    - role: "user"
    - content: "I want a blue car."
    
    How it works:
    1. It first changes "I want a blue car" into numbers (embeddings) using OpenAI.
    2. Then it uploads that number list to Pinecone, along with some tags (metadata) like who said it.
    """
    
    # Make sure we are connected
    index = init_pinecone()
    if not index:
        return False
        
    if not content or str(content).strip() == "":
        return False
        
    try:
        # Step 1: Turn words into numbers
        vector = generate_embedding(content)
        if not vector:
            return False
            
        # Generate a random unique ID for this memory block (so they don't overwrite each other)
        memory_id = str(uuid.uuid4())
        
        # We attach metadata (tags) so we can filter exactly this user's memory later
        metadata = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 2: Push to Pinecone Cloud
        index.upsert(
            vectors=[
                {"id": memory_id, "values": vector, "metadata": metadata}
            ]
        )
        
        logger.info(f"[PINECONE UPSERT] Saved memory for {user_id}: {content[:30]}...")
        return True
        
    except Exception as e:
        logger.error(f"[PINECONE UPSERT ERROR] {e}")
        return False


def semantic_search(user_id: str, query: str, top_k: int = 20) -> List[str]:
    """
    Function: semantic_search (RAG Retrieval)
    Purpose: When the AI needs context, this searches Pinecone for the most related memories.
    
    Example query: "What car do I like?"
    Instead of finding the exact word "car", it understands that "Toyota" is related to car!
    Output: ['I want a blue car.', 'I love Toyota.']
    """
    
    index = init_pinecone()
    if not index:
        return []
        
    # If query is empty, just return nothing (cannot semantic search on empty)
    if not query or str(query).strip() == "":
        return []
        
    try:
        # First turn the user's question into numbers
        query_vector = generate_embedding(query)
        if not query_vector:
            return []
            
        # Ask Pinecone for the 20 closest matching memories
        # But ONLY memories that belong to this exact `user_id` (so we don't leak others' info)
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter={
                "user_id": {"$eq": user_id}
            }
        )
        
        # Extract the English text ('content') from the metadata of the matched vectors
        matches = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            content = metadata.get("content")
            if content:
                matches.append(content)
                
        # By default Pinecone returns the BEST matches first. 
        # But we previously decided the LLM likes to read chronologically.
        # However, for Semantic Search, Order of relevance is actually very good! Let's keep relevance.
        logger.info(f"[PINECONE QUERY] Found {len(matches)} relevant semantic memories!")
        
        return matches
        
    except Exception as e:
        logger.error(f"[PINECONE QUERY ERROR] {e}")
        return []
    

