from typing import TypedDict, List, Optional, Annotated
import operator
from app.schemas import CurrentStateAnalysis, ArchitecturePlan, ROIMetrics, FinalReportCompilation

class ConsultantState(TypedDict):
    job_id: str
    client_document_text: str
    analysis_result: Optional[CurrentStateAnalysis]
    architecture_plan: Optional[ArchitecturePlan]
    roi_result: Optional[ROIMetrics]
    final_report: Optional[FinalReportCompilation]
    
    # THE FIX: Tell LangGraph to safely merge (+) lists from parallel agents
    errors: Annotated[List[str], operator.add]