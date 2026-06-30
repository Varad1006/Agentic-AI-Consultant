import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import ConsultantState
from app.schemas import CurrentStateAnalysis, ArchitecturePlan, ROIMetrics, FinalReportCompilation
from app.vector_store import retrieve_relevant_context

load_dotenv()

# ✅ FIX: Use correct Google model name
# Options: "gemini-2.0-flash" (recommended, faster) or "gemini-1.5-pro" (more powerful)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",  # Changed from "gemini-3.5-flash"
    temperature=0
)

# ... existing code ...
def planner_node(state: ConsultantState) -> dict:
    """
    1. Planner Agent: Acts as a gateway gatekeeper. Validates if the content 
    is sufficient for operational analysis and sets up the execution context.
    """
    document = state.get("client_document_text", "")
    
    # Sanitize text to remove null bytes and non-printable characters
    document = "".join(char for char in document if char.isprintable() or char in "\n\t")
    document = document.strip()
    
    if len(document) < 50:
        return {"errors": ["Planner Error: Uploaded operational profile text is too brief to generate a comprehensive consulting analysis."]}
    
    # Passes text safely along to the next node, truncated to prevent size limits
    return {"client_document_text": document[:150000]}


def analyst_node(state: ConsultantState) -> dict:
    """
    2. Business Analyst Agent: Queries the vector database for operational bottlenecks.
    """
    # Short-circuit if previous node failed
    if state.get("errors"):
        return {}
        
    job_id = state.get("job_id")
    search_query = "What is the core business model, what software or tools are used, and what are the specific bottlenecks, pain points, or time-consuming manual processes?"
    
    targeted_context = retrieve_relevant_context(job_id, search_query, top_k=6)
    
    # THE FIX: Safely catch error strings so they don't break Gemini
    if not targeted_context or "Error retrieving context" in targeted_context:
        return {"errors": [f"Analyst Error: Database search failed. Details: {targeted_context}"]}

    analyst_llm = llm.with_structured_output(CurrentStateAnalysis)
    
    prompt = (
        "You are an expert Enterprise Operations Analyst. Analyze the following targeted excerpts "
        "retrieved from the client's operational documentation. Extract the core business model, "
        "key tools in the tech stack, and all specific bottlenecks (including numerical time drains).\n\n"
        f"Retrieved Context:\n{targeted_context}"
    )
    
    try:
        result = analyst_llm.invoke(prompt)
        return {"analysis_result": result}
    except Exception as e:
        return {"errors": [f"Analyst Node Crash: {str(e)}"]}

# ... keep architect_node, roi_calculator_node, and report_generator_node as is ...

def architect_node(state: ConsultantState) -> dict:
    """
    3. Automation Expert Agent: Proposes software architectures to eliminate the extracted bottlenecks.
    """
    analysis_data = state.get("analysis_result")
    if not analysis_data:
        return {"errors": ["Automation Expert Error: Prior Business Analysis metrics are missing."]}
        
    architect_llm = llm.with_structured_output(ArchitecturePlan)
    
    prompt = (
        "You are an Automation Expert and Principal Solutions Architect. Review the following structured analysis "
        "of operational bottlenecks. Propose an automated system integration blueprint, outlining target technology "
        "solutions, sequential execution steps, and infrastructure requirements.\n\n"
        f"Structured Analysis Input:\n{analysis_data}"
    )
    
    try:
        result = architect_llm.invoke(prompt)
        return {"architecture_plan": result}
    except Exception as e:
        return {"errors": [f"Automation Expert Node Crash: {str(e)}"]}


def roi_calculator_node(state: ConsultantState) -> dict:
    """
    4. ROI Calculator Agent: Evaluates time/money savings based on the analyst's structural metrics.
    """
    analysis_data = state.get("analysis_result")
    if not analysis_data:
        return {"errors": ["ROI Calculator Error: Analysis metrics missing. Cannot compute financial projections."]}
        
    roi_llm = llm.with_structured_output(ROIMetrics)
    
    prompt = (
        "You are a Corporate Financial Controller and ROI Automation Analyst. Review the following business "
        "bottlenecks and time drains. Calculate realistic financial projections assuming standard engineering "
        "and operational cost baselines: estimated implementation/development cost (USD), annual hours saved, "
        "annual monetary savings (USD), payback period in months, and a 3-year ROI percentage.\n\n"
        f"Bottleneck Metrics Input:\n{analysis_data}"
    )
    
    try:
        result = roi_llm.invoke(prompt)
        return {"roi_result": result}
    except Exception as e:
        return {"errors": [f"ROI Calculator Node Crash: {str(e)}"]}


def report_generator_node(state: ConsultantState) -> dict:
    """
    5. Report Generator Agent: Synthesizes findings across all downstream nodes 
    and writes a unified, high-level corporate Executive Summary.
    """
    analysis = state.get("analysis_result")
    architecture = state.get("architecture_plan")
    roi = state.get("roi_result")
    
    if not all([analysis, architecture, roi]):
        return {"errors": ["Report Generator Error: Incomplete pipeline data. Missing dependencies to generate summary."]}
        
    report_llm = llm.with_structured_output(FinalReportCompilation)
    
    prompt = (
        "You are a Chief Report Compiler and Management Consultant. Synthesize the outputs from the Business Analyst, "
        "Automation Expert, and ROI Calculator agents into a high-level corporate Executive Summary. This summary "
        "must highlight the strategic business value, core pain points addressed, and a high-conviction case for "
        "why executing this automation blueprint will maximize profitability.\n\n"
        f"Analyst Output:\n{analysis}\n\n"
        f"Architect Output:\n{architecture}\n\n"
        f"ROI Output:\n{roi}"
    )
    
    try:
        result = report_llm.invoke(prompt)
        return {"final_report": result}
    except Exception as e:
        return {"errors": [f"Report Generator Node Crash: {str(e)}"]}