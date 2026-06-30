import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

# DEBUG: Check if key is loaded
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("CRITICAL ERROR: GOOGLE_API_KEY not found in environment!")
else:
    print(f"DEBUG: API Key found (starts with: {api_key[:4]}...)")

# Initialize client
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# ✅ FIX: Use the correct Google embedding model name
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",  # Changed from "text-embedding-004"
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def ingest_document_to_chroma(job_id: str, raw_text: str):
    """Chunks a massive document and stores it in a collection unique to the job."""
    print(f"DEBUG: Ingesting text for job {job_id}...")
    
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
    try:
        embeddings = embeddings_model.embed_documents(documents)
        print(f"DEBUG: Generated embeddings for {len(documents)} chunks")
    except Exception as e:
        print(f"ERROR: Failed to generate embeddings: {str(e)}")
        raise
    
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"DEBUG: Successfully saved {len(chunks)} chunks to ChromaDB.")
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