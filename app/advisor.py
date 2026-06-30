from langchain_google_genai import ChatGoogleGenerativeAI

from app.prompts import CONSULTANT_SYSTEM_PROMPT
from app.consultant_memory import load_consulting_memory
from app.vector_store import retrieve_relevant_context

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2
)


def answer_question(job_id: str, question: str):

    # Load previous consulting engagement
    consulting_memory = load_consulting_memory(job_id)

    if consulting_memory is None:
        return (
            "I couldn't find the consulting report for this business. "
            "Please generate a report before starting a consultation."
        )

    # Retrieve supporting evidence from Chroma
    supporting_context = retrieve_relevant_context(
        job_id,
        question,
        top_k=5
    )

    # Extract the important sections
    analysis = consulting_memory.get("analysis", "")
    architecture = consulting_memory.get("architecture", "")
    roi = consulting_memory.get("roi", "")
    report = consulting_memory.get("report", "")

    # Build the final prompt
    prompt = f"""
{CONSULTANT_SYSTEM_PROMPT}

==================================================
BUSINESS ANALYSIS
==================================================

{analysis}

==================================================
SOLUTION ARCHITECTURE
==================================================

{architecture}

==================================================
ROI ANALYSIS
==================================================

{roi}

==================================================
EXECUTIVE REPORT
==================================================

{report}

==================================================
SUPPORTING DOCUMENT EVIDENCE
==================================================

{supporting_context}

==================================================
CLIENT QUESTION
==================================================

{question}
"""

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = []

        for block in content:
            if isinstance(block, dict):
                text.append(block.get("text", ""))
            else:
                text.append(str(block))

        return "\n".join(text)

    return str(content)