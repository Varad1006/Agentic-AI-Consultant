from typing import TypedDict, List, Optional
from app.schemas import CurrentStateAnalysis, ArchitecturePlan, ROIMetrics, FinalReportCompilation

class ConsultantState(TypedDict):
    job_id: str                                       # NEW: So agents can query the DB
    client_document_text: str
    analysis_result: Optional[CurrentStateAnalysis]
    architecture_plan: Optional[ArchitecturePlan]
    roi_result: Optional[ROIMetrics]
    final_report: Optional[FinalReportCompilation]
    errors: List[str]

# Because our database needs to know which document to search, we need to pass the job_id into our LangGraph state.