# from langchain_google_genai import ChatGoogleGenerativeAI
# from app.vector_store import retrieve_relevant_context
# from pydantic import BaseModel

# class ChatRequest(BaseModel):
#     question: str

# # Use the active model
# llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.2)

# def ask_consultant(job_id: str, question: str) -> str:
#     """Retrieves context from ChromaDB and answers the user's custom question."""
    
#     # 1. Search the vector database for paragraphs related to the user's specific question
#     context = retrieve_relevant_context(job_id, question, top_k=5)
    
#     if not context:
#         return "I don't have enough information in the uploaded documents to answer that."

#     # 2. Build a strict prompt forcing the AI to only use the retrieved context
#     prompt = f"""
#     You are an AI Enterprise Consultant. Answer the user's question based ONLY on the following retrieved context from their uploaded business documents. 
#     If the answer is not contained in the context, say "I cannot find the answer to this in the provided documents." Do not invent information.
    
#     Retrieved Context:
#     {context}
    
#     User Question: {question}
#     """
    
#     # 3. Generate the response
#     try:
#         response = llm.invoke(prompt)
#         content = response.content
#         if isinstance(content, str):
#             return content
#         if isinstance(content, list):
#             text=[]
#             for block in content:
#                 if isinstance(block, dict):
#                     if "text" in block:
#                         text.append(block["text"])
#                     elif "type" in block and block.get("type") == "text":
#                         text.append(str(block))
#                 else:
#                     text.append(str(block))
#             return "\n".join(text)
#         return str(content)
       
      
         
#     except Exception as e:
#         return f"Error communicating with the LLM: {str(e)}"

from app.advisor import answer_question
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


def ask_consultant(job_id: str, question: str) -> str:
    """
    Public entry point for the consultant chat.
    Delegates all reasoning to the Advisor.
    """
    return answer_question(job_id, question)