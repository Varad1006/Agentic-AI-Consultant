from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessBottleneck(BaseModel):
    process_name: str = Field(description="Short name of the inefficient process")
    current_time_spent_hours: float = Field(
        description="Estimated hours spent on this process per week, across the whole team"
    )
    pain_point_description: str = Field(description="Why this process is slow, error-prone or costly")


class CurrentStateAnalysis(BaseModel):
    core_business_model: str = Field(description="2-3 sentences on what the client does and for whom")
    current_tech_stack: List[str] = Field(description="Software, systems and spreadsheets the team uses")
    identified_bottlenecks: List[ProcessBottleneck] = Field(
        description="Manual, repetitive, slow or error-prone processes"
    )


class ProposedSolution(BaseModel):
    target_bottleneck: str = Field(description="Name of the bottleneck this solution addresses")
    recommended_technology: str = Field(description="Specific tools or frameworks to use")
    implementation_steps: List[str] = Field(description="3-6 concrete implementation steps")


class ArchitecturePlan(BaseModel):
    overall_strategy: str = Field(description="Summary of the automation approach")
    proposed_solutions: List[ProposedSolution] = Field(description="Solutions mapped to bottlenecks")
    infrastructure_requirements: List[str] = Field(description="Platforms, integrations and compute needed")


class ROIEstimate(BaseModel):
    """The figures the ROI agent estimates. Derived metrics are calculated in code."""

    estimated_development_cost_usd: float = Field(
        description="One-off cost to build and roll out all proposed solutions, in USD"
    )
    annual_hours_saved: float = Field(description="Hours per year the solutions will realistically free up")
    estimated_annual_monetary_savings_usd: float = Field(description="Savings per year, in USD")
    key_assumptions: List[str] = Field(description="The 3-5 assumptions behind these estimates")


class ROIMetrics(ROIEstimate):
    payback_period_months: Optional[float] = None
    roi_percentage: Optional[float] = Field(default=None, description="Return over a 3-year horizon")


class FinalReport(BaseModel):
    executive_summary: str = Field(description="Two short paragraphs for the executive team")
    priority_actions: List[str] = Field(description="3-5 initiatives in priority order, one sentence each")


def compute_roi(estimate: ROIEstimate) -> ROIMetrics:
    """Derive payback and 3-year ROI from the agent's estimates so the numbers are always consistent."""
    cost = max(estimate.estimated_development_cost_usd, 0.0)
    annual_savings = max(estimate.estimated_annual_monetary_savings_usd, 0.0)

    payback = round(cost / (annual_savings / 12), 1) if annual_savings > 0 else None
    roi = round((3 * annual_savings - cost) / cost * 100, 1) if cost > 0 else None

    return ROIMetrics(**estimate.model_dump(), payback_period_months=payback, roi_percentage=roi)
