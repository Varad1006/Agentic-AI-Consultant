from pydantic import BaseModel, Field
from typing import List, Optional

class ProcessBottleneck(BaseModel):
    process_name: str = Field(description="Name of the inefficient process")
    current_time_spent_hours: float = Field(description="Estimated hours spent per week")
    pain_point_description: str = Field(description="Why this process is failing or slow")

class ProposedSolution(BaseModel):
    target_bottleneck: str = Field(description="Which bottleneck from the analysis this solves")
    recommended_technology: str = Field(description="Specific tool/framework")
    implementation_steps: List[str] = Field(description="High-level technical steps")

class CurrentStateAnalysis(BaseModel):
    core_business_model: str = Field(description="Brief summary of what the client does")
    current_tech_stack: List[str] = Field(description="Tools currently used")
    identified_bottlenecks: List[ProcessBottleneck] = Field(description="List of exact inefficiencies")

class ArchitecturePlan(BaseModel):
    overall_strategy: str = Field(description="Summary of the technical approach")
    proposed_solutions: List[ProposedSolution] = Field(description="Solutions mapped to bottlenecks")
    infrastructure_requirements: List[str] = Field(description="Cloud or compute needs")

class MCPJobRequest(BaseModel):
    document_text: Optional[str] = None
    target_directory_path: Optional[str] = None # For MCP ingestion

class ROIMetrics(BaseModel):
    estimated_development_cost_usd: float = Field(description="Estimated cost to build and implement the proposed automation solutions.")
    annual_hours_saved: float = Field(description="Total operational hours saved per year across all bottlenecks.")
    estimated_annual_monetary_savings_usd: float = Field(description="Calculated financial savings per year based on time saved and resource reclamation.")
    payback_period_months: float = Field(description="How many months it will take for the monetary savings to clear the development cost.")
    roi_percentage: float = Field(description="Return on Investment percentage over a 3-year horizon.")

class FinalReportCompilation(BaseModel):
    executive_summary: str = Field(description="A high-level corporate summary combining the business overview, core critical pain points, and why the proposed automation blueprint is a strategic necessity.")