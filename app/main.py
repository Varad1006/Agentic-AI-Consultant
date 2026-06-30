from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.celery_worker import run_consulting_job, celery_app, test_celery_connection
from celery.result import AsyncResult
from typing import Optional
from fastapi import UploadFile, File
import io
import logging
from pypdf import PdfReader
import docx
from app.vector_store import ingest_document_to_chroma
from app.chat_agent import ask_consultant, ChatRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@app.on_event("startup")
async def startup_event():
    """Test Celery connection on startup"""
    logger.info("🚀 FastAPI startup - Testing Celery connection...")
    try:
        # Try a test task
        test_task = test_celery_connection.delay()
        logger.info(f"✅ Test task sent to Celery: {test_task.id}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Celery: {str(e)}")
        logger.warning("⚠️  Make sure Redis is running and Celery worker is started!")


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint to verify services are running"""
    try:
        # Check Celery connection
        celery_status = "unknown"
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            if active_tasks is not None:
                celery_status = "connected"
            else:
                celery_status = "no_workers"
        except Exception as e:
            celery_status = f"error: {str(e)}"
        
        return {
            "status": "ok",
            "fastapi": "running",
            "celery": celery_status,
            "message": "All systems operational" if celery_status == "connected" else f"Warning: {celery_status}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Accepts a PDF, DOCX, or TXT file, parses the text, and starts the agent graph."""
    logger.info(f"📁 File upload received: {file.filename}")
    
    extracted_text = ""
    
    try:
        if file.filename.endswith('.pdf'):
            logger.info("Processing PDF file...")
            pdf = PdfReader(file.file)
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
        elif file.filename.endswith('.docx'):
            logger.info("Processing DOCX file...")
            doc = docx.Document(file.file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
        else:
            logger.info("Processing TXT file...")
            extracted_text = (await file.read()).decode("utf-8")
            
    except Exception as e:
        logger.error(f"❌ Failed to parse document: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")

    if not extracted_text.strip():
        logger.error("❌ Uploaded document is empty")
        raise HTTPException(status_code=400, detail="The uploaded document appears to be empty.")

    try:
        logger.info(f"📝 Extracted text length: {len(extracted_text)} characters")
        
        # 1. Safely generate an ID without starting the worker yet
        signature = run_consulting_job.s(extracted_text)
        job_id = signature.freeze().id
        logger.info(f"✅ Task signature created with ID: {job_id}")
        
        # 2. Save to ChromaDB FIRST
        logger.info(f"💾 Ingesting document to ChromaDB for job {job_id}...")
        ingest_document_to_chroma(job_id=job_id, raw_text=extracted_text)
        logger.info("✅ Document ingested to ChromaDB successfully")
        
        # 3. NOW start the background worker
        logger.info("🚀 Sending task to Celery worker...")
        async_result = signature.apply_async(task_id=job_id)
        logger.info(f"✅ Task sent to Celery. Task ID: {async_result.id}, State: {async_result.state}")
        
        return {
            "job_id": job_id, 
            "status": "Processing", 
            "filename": file.filename,
            "message": "File chunked and embedded successfully. Agents are analyzing."
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.post("/api/v1/consult")
async def submit_consulting_job(request: JobRequest):
    """Submits pasted text to the background agent workflow."""
    logger.info(f"📝 Text submission received. Length: {len(request.document_text)} characters")
    
    try:
        # Apply the same safe sequence for pasted text!
        signature = run_consulting_job.s(request.document_text)
        job_id = signature.freeze().id
        logger.info(f"✅ Task signature created with ID: {job_id}")
        logger.info(f"💾 Ingesting document to ChromaDB for job {job_id}...")
        ingest_document_to_chroma(job_id=job_id, raw_text=request.document_text)
        logger.info("✅ Document ingested to ChromaDB successfully")
        logger.info("🚀 Sending task to Celery worker...")
        async_result = signature.apply_async(task_id=job_id)
        logger.info(f"✅ Task sent to Celery. Task ID: {async_result.id}, State: {async_result.state}")
        return{"job_id": job_id,
        "status": "Processing"}
        
    except Exception as e:
        logger.error(f"❌ Failed to submit job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.get("/api/v1/consult/{job_id}")
async def get_job_status(job_id: str):
    """Checks the status of a previously submitted job."""
    logger.info(f"🔍 Status check for job: {job_id}")
    
    task = AsyncResult(job_id, app=celery_app)
    logger.info(f"   Task state: {task.state}")
    
    if task.state == "PENDING":
        return {"job_id": job_id, "status": "Pending/In Queue"}
    elif task.state in ["STARTED", "PROGRESS"]:
        return {"job_id": job_id, "status": "Processing"}
    elif task.state == "SUCCESS":
        logger.info(f"   ✅ Task completed successfully")
        return {"job_id": job_id, "status": "Completed", "result": task.result}
    elif task.state == "FAILURE":
        logger.error(f"   ❌ Task failed: {str(task.info)}")
        return {"job_id": job_id, "status": "Failed", "error": str(task.info)}
    else:
        return {"job_id": job_id, "status": task.state}


@app.get("/api/v1/consult/{job_id}/report")
async def get_formatted_report(job_id: str):
    """Fetches the job data and parses it into a clean Markdown report."""
    logger.info(f"📄 Report request for job: {job_id}")
    
    task = AsyncResult(job_id, app=celery_app)
    
    if task.state != "SUCCESS":
        logger.info(f"   Report not ready. Task state: {task.state}")
        return {"job_id": job_id, "status": task.state, "message": "Report is not ready yet."}
    
    data = task.result
    logger.info(f"   ✅ Task data retrieved")
    
    # Safely handle if the agents crashed and returned errors instead of data
    if data.get("errors") and not data.get("analysis"):
        error_msgs = "\n".join([f"- {e}" for e in data["errors"]])
        logger.warning(f"   ⚠️  Agent execution failed: {error_msgs}")
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
        logger.error(f"   ❌ Incomplete data: analysis={bool(analysis)}, architecture={bool(architecture)}")
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

    logger.info(f"   ✅ Report generated successfully")
    return {
        "job_id": job_id,
        "format": "markdown",
        "content": markdown_content
    }


@app.post("/api/v1/consult/{job_id}/chat")
async def chat_with_agent(job_id: str, request: ChatRequest):
    """Allows the user to ask custom questions against their uploaded documents."""
    logger.info(f"💬 Chat request for job {job_id}: {request.question[:50]}...")
    
    # Check if the job exists (optional, depending on your DB setup)
    if not job_id:
        logger.error(f"   ❌ Invalid Job ID")
        raise HTTPException(status_code=400, detail="Invalid Job ID")
    
    try:
        answer = ask_consultant(job_id, request.question)
        print(type(answer))
        print(answer)
        logger.info(f"   ✅ Chat response generated")
        
        return {
            "job_id": job_id,
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"   ❌ Chat failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")