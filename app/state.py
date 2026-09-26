import operator
from typing import Annotated, List, Optional, TypedDict

from app.schemas import ArchitecturePlan, CurrentStateAnalysis, FinalReport, ROIMetrics


class ConsultantState(TypedDict, total=False):
    job_id: str
    client_document_text: str
    document_context: str
    analysis_result: Optional[CurrentStateAnalysis]
    architecture_plan: Optional[ArchitecturePlan]
    roi_result: Optional[ROIMetrics]
    final_report: Optional[FinalReport]

    # Nodes append errors; the graph stops at the first node that reports one.
    errors: Annotated[List[str], operator.add]
