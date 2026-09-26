"""Render a completed job as a Markdown consulting report."""

from typing import Any, Dict, Optional


def _money(value: Optional[float]) -> str:
    return f"${value:,.0f}" if value is not None else "n/a"


def _number(value: Optional[float], suffix: str = "") -> str:
    return f"{value:,.1f}".rstrip("0").rstrip(".") + suffix if value is not None else "n/a"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(job: Dict[str, Any]) -> str:
    result = job["result"]
    analysis = result["analysis"]
    architecture = result["architecture"]
    roi = result["roi"]
    report = result["report"]

    source = job.get("filename") or "Pasted text"
    lines = [
        "# Executive Consulting Report",
        "",
        f"**Source:** {source}  ",
        f"**Generated:** {job['created_at']}  ",
        f"**Reference:** `{job['job_id']}`",
        "",
        "## 1. Executive Summary",
        "",
        report["executive_summary"],
        "",
        "### Priority actions",
        "",
        *[f"{i}. {action}" for i, action in enumerate(report["priority_actions"], start=1)],
        "",
        "## 2. Financial Case",
        "",
        "| Metric | Estimate |",
        "| --- | --- |",
        f"| Development cost | {_money(roi['estimated_development_cost_usd'])} |",
        f"| Annual savings | {_money(roi['estimated_annual_monetary_savings_usd'])} |",
        f"| Hours saved per year | {_number(roi['annual_hours_saved'])} |",
        f"| Payback period | {_number(roi['payback_period_months'], ' months')} |",
        f"| 3-year ROI | {_number(roi['roi_percentage'], '%')} |",
        "",
        "**Key assumptions**",
        "",
        *[f"- {assumption}" for assumption in roi["key_assumptions"]],
        "",
        "## 3. Current State",
        "",
        f"**Business model:** {analysis['core_business_model']}",
        "",
        "**Current tools:** " + (", ".join(analysis["current_tech_stack"]) or "None identified"),
        "",
        "### Bottlenecks",
        "",
        "| Process | Hours / week | Pain point |",
        "| --- | --- | --- |",
        *[
            f"| {_cell(b['process_name'])} | {_number(b['current_time_spent_hours'])} "
            f"| {_cell(b['pain_point_description'])} |"
            for b in analysis["identified_bottlenecks"]
        ],
        "",
        "## 4. Automation Blueprint",
        "",
        architecture["overall_strategy"],
        "",
    ]

    for solution in architecture["proposed_solutions"]:
        lines += [
            f"### {solution['target_bottleneck']}",
            "",
            f"**Recommended stack:** {solution['recommended_technology']}",
            "",
            *[f"{i}. {step}" for i, step in enumerate(solution["implementation_steps"], start=1)],
            "",
        ]

    lines += [
        "### Infrastructure requirements",
        "",
        *[f"- {item}" for item in architecture["infrastructure_requirements"]],
        "",
    ]
    return "\n".join(lines)
