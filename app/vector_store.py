import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
# Initialize local ChromaDB client (saves data to a folder in your project)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Initialize Gemini's fast embedding model
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def ingest_document_to_chroma(job_id: str, raw_text: str):
    """Chunks a massive document and stores it in a collection unique to the job."""
    # 1. Chunk the document into 1000-character blocks with some overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)
    
    # 2. Create a unique database collection for this specific job
    collection = chroma_client.get_or_create_collection(name=f"job_{job_id}")
    
    # 3. Generate embeddings and store them
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({"source": f"chunk_{i}"})
        ids.append(str(i))
        
    # We use LangChain to generate the mathematical vectors
    embeddings = embeddings_model.embed_documents(documents)
    
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    return True

def retrieve_relevant_context(job_id: str, query: str, top_k: int = 5) -> str:
    """Searches the database for the most relevant chunks based on the agent's query."""
    try:
        collection = chroma_client.get_collection(name=f"job_{job_id}")
        
        # Convert the agent's search query into a vector
        query_embedding = embeddings_model.embed_query(query)
        
        # Find the top matches
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Combine the retrieved chunks back into a single string for the LLM to read
        if results and results['documents']:
            return "\n...\n".join(results['documents'][0])
        return ""
    except Exception as e:
        return f"Error retrieving context: {str(e)}"