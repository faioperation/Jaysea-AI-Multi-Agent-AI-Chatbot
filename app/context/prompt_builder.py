from typing import List, Dict


def build_prompt(
    identity: str,
    behaviour: str,
    experience: List[str],
    conversation: List[Dict],
    user_query: str,
    max_experience: int = 100,
    max_conversation: int = 10
) -> str:
    """
    Build structured prompt for LLM
    """

    sections = []

    # -----------------------------
    # 1. Identity
    # -----------------------------
    sections.append("### AGENT IDENTITY")
    sections.append(identity.strip())

    # -----------------------------
    # 2. Behaviour
    # -----------------------------
    sections.append("\n### BEHAVIOUR")
    sections.append(behaviour.strip())

    # -----------------------------
    # 3. Experience (LIMITED)
    # -----------------------------
    sections.append("\n### EXPERIENCE MEMORY")

    if experience:
        for exp in experience[:max_experience]:
            if exp:
                sections.append(f"- {str(exp).strip()}")
    else:
        sections.append("No relevant experience.")

    # -----------------------------
    # 4. Conversation (LIMITED)
    # -----------------------------
    sections.append("\n### RECENT CONVERSATION")

    if conversation:
        for msg in conversation[-max_conversation:]:
            role = (msg.get("role") or "user").upper()
            content = (msg.get("content") or "").strip()

            sections.append(f"[{role}] {content}")
    else:
        sections.append("No recent conversation.")

    # -----------------------------
    # 5. User Question (SANITIZED)
    # -----------------------------
    sections.append("\n### USER QUESTION")

    safe_query = user_query.strip().replace("\n", " ")
    sections.append(safe_query)

    # -----------------------------
    # 6. Strong Instruction
    # -----------------------------
    sections.append("\n### INSTRUCTION")
    sections.append(
        "Answer the USER QUESTION using only the provided context.\n"
        "- Use conversation and experience if relevant\n"
        "- Do NOT invent information\n"
        "- If information is missing, say 'I don't know'\n"
        "- Keep answer short and direct\n"
    )

    # -----------------------------
    # 7. Response
    # -----------------------------
    sections.append("\n### RESPONSE")

    return "\n".join(sections)