import os
import tempfile

# Configure the app before any `app.*` module is imported.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="consultant-tests-")
os.environ["GROQ_API_KEY"] = ""
os.environ["CHROMA_HOST"] = ""
os.environ["MAX_CONTEXT_CHARS"] = "12000"

import pytest  # noqa: E402

from app.schemas import (  # noqa: E402
    ArchitecturePlan,
    CurrentStateAnalysis,
    FinalReport,
    ProcessBottleneck,
    ProposedSolution,
    ROIEstimate,
)

SAMPLE_DOCUMENT = (
    "Brightline Fulfillment runs two warehouses for 180 online retailers. "
    "Every morning dispatchers spend 3 hours building delivery routes in Excel and "
    "send them to drivers over WhatsApp. Purchase orders are typed manually into PDFs, "
    "which takes the procurement team about 12 hours a week. Invoices are reconciled "
    "by hand against the ERP."
)


def fake_outputs():
    return {
        CurrentStateAnalysis: CurrentStateAnalysis(
            core_business_model="Third-party fulfilment for online retailers.",
            current_tech_stack=["Excel", "WhatsApp", "ERP"],
            identified_bottlenecks=[
                ProcessBottleneck(
                    process_name="Route planning",
                    current_time_spent_hours=15,
                    pain_point_description="Routes are built by hand in Excel every morning.",
                ),
                ProcessBottleneck(
                    process_name="Purchase orders",
                    current_time_spent_hours=12,
                    pain_point_description="POs are typed manually into PDFs.",
                ),
            ],
        ),
        ArchitecturePlan: ArchitecturePlan(
            overall_strategy="Automate dispatch and procurement on top of the existing ERP.",
            proposed_solutions=[
                ProposedSolution(
                    target_bottleneck="Route planning",
                    recommended_technology="Route optimisation API + driver app",
                    implementation_steps=["Export orders", "Optimise routes", "Push to drivers"],
                )
            ],
            infrastructure_requirements=["ERP API access", "Cloud functions"],
        ),
        ROIEstimate: ROIEstimate(
            estimated_development_cost_usd=60000,
            annual_hours_saved=1100,
            estimated_annual_monetary_savings_usd=48000,
            key_assumptions=["$40/hour fully-loaded cost", "80% of route planning automated"],
        ),
        FinalReport: FinalReport(
            executive_summary="Brightline can save 1,100 hours a year.",
            priority_actions=["Automate route planning.", "Digitise purchase orders."],
        ),
    }


class FakeStructuredModel:
    def __init__(self, output):
        self.output = output
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return self.output


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace Groq with canned structured outputs; returns the prompts each agent received."""
    outputs = fake_outputs()
    models = {schema: FakeStructuredModel(output) for schema, output in outputs.items()}
    monkeypatch.setattr("app.nodes.structured_model", lambda schema: models[schema])
    return models
