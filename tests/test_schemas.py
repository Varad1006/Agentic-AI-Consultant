from app.schemas import ROIEstimate, compute_roi


def _estimate(cost, savings):
    return ROIEstimate(
        estimated_development_cost_usd=cost,
        annual_hours_saved=1000,
        estimated_annual_monetary_savings_usd=savings,
        key_assumptions=[],
    )


def test_roi_is_derived_from_cost_and_savings():
    roi = compute_roi(_estimate(60000, 48000))
    assert roi.payback_period_months == 15.0
    assert roi.roi_percentage == 140.0  # (3 * 48k - 60k) / 60k


def test_roi_handles_zero_values():
    assert compute_roi(_estimate(60000, 0)).payback_period_months is None
    assert compute_roi(_estimate(0, 48000)).roi_percentage is None
