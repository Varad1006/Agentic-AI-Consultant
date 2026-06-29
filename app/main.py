from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.celery_worker import run_consulting_job, celery_app
from celery.result import AsyncResult
from typing import Optional
from fastapi import UploadFile, File
import io
from pypdf import PdfReader
import docx
from app.vector_store import ingest_document_to_chroma
from app.chat_agent import ask_consultant, ChatRequest

app = FastAPI(title="Agentic AI Consultant API")

# --- THE FIX: Correct CORS Configuration ---
# allow_credentials MUST be False if allow_origins is ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    document_text: str
    target_directory_path: Optional[str] = None

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Accepts a PDF, DOCX, or TXT file, parses the text, and starts the agent graph."""
    extracted_text = ""
    
    try:
        # 1. Parse PDF Files
        if file.filename.endswith('.pdf'):
            pdf = PdfReader(file.file)
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
                
        # 2. Parse Word Documents
        elif file.filename.endswith('.docx'):
            doc = docx.Document(file.file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
                
        # 3. Parse Standard Text/CSV Files
        else:
            extracted_text = (await file.read()).decode("utf-8")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="The uploaded document appears to be empty or unreadable.")

    # Pass the extracted text directly into your existing Celery graph worker
    task = run_consulting_job.delay(extracted_text)
    ingest_document_to_chroma(task.id, extracted_text)
    task.delay()  # Store the document in ChromaDB for context retrieval
    
    return {
        "job_id": task.id, 
        "status": "Processing", 
        "filename": file.filename,
        "message": "File parsed successfully. Agents are analyzing."
    }

@app.post("/api/v1/consult")
async def submit_consulting_job(request: JobRequest):
    """Submits a document to the background agent workflow."""
    task = run_consulting_job.delay(request.document_text)
    return {"job_id": task.id, "status": "Processing"}

@app.get("/api/v1/consult/{job_id}")
async def get_job_status(job_id: str):
    """Checks the status of a previously submitted job."""
    task = AsyncResult(job_id, app=celery_app)
    
    if task.state == "PENDING":
        return {"job_id": job_id, "status": "Pending/In Queue"}
    elif task.state in ["STARTED", "PROGRESS"]:
        return {"job_id": job_id, "status": "Processing"}
    elif task.state == "SUCCESS":
        return {"job_id": job_id, "status": "Completed", "result": task.result}
    elif task.state == "FAILURE":
        return {"job_id": job_id, "status": "Failed", "error": str(task.info)}
    else:
        return {"job_id": job_id, "status": task.state}

@app.get("/api/v1/consult/{job_id}/report")
async def get_formatted_report(job_id: str):
    """Fetches the job data and parses it into a clean Markdown report."""
    task = AsyncResult(job_id, app=celery_app)
    
    if task.state != "SUCCESS":
        return {"job_id": job_id, "status": task.state, "message": "Report is not ready yet."}
    
    data = task.result
    
    # Safely handle if the agents crashed and returned errors instead of data
    if data.get("errors") and not data.get("analysis"):
        error_msgs = "\n".join([f"- {e}" for e in data["errors"]])
        return {
            "job_id": job_id,
            "format": "markdown",
            "content": f"## ⚠️ Agent Execution Failed\n\n{error_msgs}"
        }

    analysis = data.get("analysis")
    architecture = data.get("architecture")
    roi = data.get("roi")
    report = data.get("report")
    
    if not analysis or not architecture:
        raise HTTPException(status_code=404, detail="Incomplete data found for report generation.")
    
    # UI Parser Engine: Compiling ALL 5 nodes into clean Markdown
    markdown_content = f"# Executive Consulting Report\n"
    markdown_content += f"**Job Reference ID:** `{job_id}`\n\n"
    
    # --- 1. EXECUTIVE SUMMARY (Report Generator Node) ---
    markdown_content += f"## 1. Executive Summary\n"
    if report and "executive_summary" in report:
        markdown_content += f"*{report['executive_summary']}*\n\n"
    else:
        markdown_content += "*Summary generation pending...*\n\n"
        
    markdown_content += "---\n\n"
    
    # --- 2. CURRENT STATE (Analyst Node) ---
    markdown_content += f"## 2. Current State Discovery\n"
    markdown_content += f"**Business Model:** {analysis.get('core_business_model', 'N/A')}\n\n"
    
    markdown_content += "### Existing Infrastructure & Tools\n"
    for tech in analysis.get('current_tech_stack', []):
        markdown_content += f"- {tech}\n"
        
    markdown_content += "\n### Identified Inefficiencies & Bottlenecks\n"
    for bottleneck in analysis.get('identified_bottlenecks', []):
        markdown_content += f"- **{bottleneck['process_name']}** ({bottleneck['current_time_spent_hours']} hrs/week): {bottleneck['pain_point_description']}\n"

    markdown_content += "\n---\n\n"
    
    # --- 3. ARCHITECTURE (Architect Node) ---
    markdown_content += f"## 3. Proposed Solution Architecture\n"
    markdown_content += f"{architecture.get('overall_strategy', 'N/A')}\n\n"
    
    markdown_content += "### Technical Solution Blueprints\n"
    for solution in architecture.get('proposed_solutions', []):
        markdown_content += f"#### 🛠️ Target Area: {solution['target_bottleneck']}\n"
        markdown_content += f"- **Recommended Stack:** `{solution['recommended_technology']}`\n"
        markdown_content += f"- **Implementation Execution Steps:**\n"
        for step in solution['implementation_steps']:
            markdown_content += f"  1. {step}\n"
        markdown_content += "\n"

    markdown_content += "### Infrastructure & Resource Requirements\n"
    for infra in architecture.get('infrastructure_requirements', []):
        markdown_content += f"- {infra}\n"

    # --- 4. ROI METRICS (ROI Calculator Node) ---
    if roi:
        markdown_content += "\n---\n\n"
        markdown_content += f"## 4. Projected Return on Investment (ROI)\n"
        # Using string formatting to add commas and 2 decimal places to currency
        markdown_content += f"- **Estimated Development Cost:** ${roi.get('estimated_development_cost_usd', 0):,.2f}\n"
        markdown_content += f"- **Annual Hours Saved:** {roi.get('annual_hours_saved', 0)} hours\n"
        markdown_content += f"- **Estimated Annual Savings:** ${roi.get('estimated_annual_monetary_savings_usd', 0):,.2f}\n"
        markdown_content += f"- **Payback Period:** {roi.get('payback_period_months', 0)} months\n"
        markdown_content += f"- **3-Year ROI:** {roi.get('roi_percentage', 0)}%\n"

    return {
        "job_id": job_id,
        "format": "markdown",
        "content": markdown_content
    }
# ... existing routes ...

@app.post("/api/v1/consult/{job_id}/chat")
async def chat_with_agent(job_id: str, request: ChatRequest):
    """Allows the user to ask custom questions against their uploaded documents."""
    
    # Check if the job exists (optional, depending on your DB setup)
    if not job_id:
        raise HTTPException(status_code=400, detail="Invalid Job ID")
        
    answer = ask_consultant(job_id, request.question)
    
    return {
        "job_id": job_id,
        "question": request.question,
        "answer": answer
    }