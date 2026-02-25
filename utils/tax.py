from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any

ReliefType = Literal[
    "none",
    "exempt_within_quota",
    "reduce50_within_quota",
    "exempt_all",
    "reduce50_all",
]

def _to_float(x: object, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def registration_fee_land_vnd(
    area_m2: float,
    gov_price_mil_m2: float,
    rate: float = 0.005,
    exempt: bool = False,
) -> Dict[str, Any]:
    """Estimate registration fee for land (lệ phí trước bạ - phần đất).

    Base value is typically the provincial land-price table (bảng giá đất),
    i.e., area * gov_unit_price, then multiply by rate (commonly 0.5%).

    Inputs:
        area_m2: land area in m²
        gov_price_mil_m2: government unit price in million VND/m²

    Returns:
        dict with base_value_vnd, fee_vnd, rate, exempt
    """
    area = max(_to_float(area_m2), 0.0)
    gov = max(_to_float(gov_price_mil_m2), 0.0)
    base_value_vnd = area * gov * 1_000_000.0
    fee_vnd = 0.0 if exempt else base_value_vnd * _to_float(rate)
    return {
        "base_value_vnd": base_value_vnd,
        "fee_vnd": fee_vnd,
        "rate": _to_float(rate),
        "exempt": bool(exempt),
    }

def pit_transfer_tax_vnd(
    transfer_price_billion_vnd: float,
    rate: float = 0.02,
    exempt: bool = False,
) -> Dict[str, Any]:
    """Estimate PIT for real-estate transfer (thuế TNCN khi chuyển nhượng BĐS).

    Common practice: 2% x transfer price (contract price) for real estate transfer.
    Many exemption cases exist; this function supports a simple exempt flag.

    Input:
        transfer_price_billion_vnd: contract/transfer price (billion VND)

    Returns:
        dict with tax_base_vnd, pit_vnd, rate, exempt
    """
    base_vnd = max(_to_float(transfer_price_billion_vnd), 0.0) * 1_000_000_000.0
    pit_vnd = 0.0 if exempt else base_vnd * _to_float(rate)
    return {
        "tax_base_vnd": base_vnd,
        "pit_vnd": pit_vnd,
        "rate": _to_float(rate),
        "exempt": bool(exempt),
    }

def non_agri_land_tax_vnd(
    area_m2: float,
    gov_price_mil_m2: float,
    quota_m2: float = 160.0,
    relief: ReliefType = "none",
) -> Dict[str, Any]:
    """Estimate non-agricultural land use tax for residential land (thuế SDĐ phi nông nghiệp - đất ở).

    Progressive rates for residential land (Luật Thuế SDĐPNN 48/2010/QH12):
        - 0.03% for area within quota (hạn mức)
        - 0.07% for area exceeding quota up to 3x quota
        - 0.15% for area exceeding 3x quota

    Relief handling (simplified for the tool UI):
        - none: no relief
        - exempt_within_quota: set tax on the within-quota segment to 0
        - reduce50_within_quota: 50% reduction on the within-quota segment
        - exempt_all / reduce50_all: apply to total tax (used for some force-majeure cases, etc.)

    NOTE: This is an educational estimator. Actual assessment depends on hồ sơ, quyết định địa phương,
    and the tax authority's final determination.

    Returns:
        dict with segment areas, segment taxes, totals (VND)
    """
    area = max(_to_float(area_m2), 0.0)
    gov = max(_to_float(gov_price_mil_m2), 0.0)
    quota = max(_to_float(quota_m2), 0.0)

    # Segment areas
    a1 = min(area, quota) if quota > 0 else 0.0
    a2 = 0.0
    a3 = 0.0
    if quota > 0:
        a2 = min(max(area - quota, 0.0), 2 * quota)          # (quota, 3*quota]
        a3 = max(area - 3 * quota, 0.0)                      # > 3*quota
    else:
        # If quota unknown, fall back to flat rate of the first tier (educational)
        a1 = area
        a2 = 0.0
        a3 = 0.0

    # Rates
    r1 = 0.0003  # 0.03%
    r2 = 0.0007  # 0.07%
    r3 = 0.0015  # 0.15%

    # Segment tax (VND)
    tax1 = a1 * gov * 1_000_000.0 * r1
    tax2 = a2 * gov * 1_000_000.0 * r2
    tax3 = a3 * gov * 1_000_000.0 * r3
    total_before_relief = tax1 + tax2 + tax3

    # Apply relief
    relief = relief or "none"
    tax1_after = tax1
    tax2_after = tax2
    tax3_after = tax3

    if relief == "exempt_within_quota":
        tax1_after = 0.0
    elif relief == "reduce50_within_quota":
        tax1_after = tax1 * 0.5
    elif relief == "exempt_all":
        tax1_after = 0.0
        tax2_after = 0.0
        tax3_after = 0.0
    elif relief == "reduce50_all":
        tax1_after *= 0.5
        tax2_after *= 0.5
        tax3_after *= 0.5

    total_after_relief = tax1_after + tax2_after + tax3_after

    return {
        "area_m2": area,
        "quota_m2": quota,
        "gov_price_mil_m2": gov,
        "segments": {
            "within_quota_m2": a1,
            "over_quota_to_3x_m2": a2,
            "over_3x_quota_m2": a3,
        },
        "rates": {"r1": r1, "r2": r2, "r3": r3},
        "tax_vnd": {
            "within_quota": tax1_after,
            "over_quota_to_3x": tax2_after,
            "over_3x_quota": tax3_after,
            "total": total_after_relief,
        },
        "tax_vnd_before_relief": {
            "within_quota": tax1,
            "over_quota_to_3x": tax2,
            "over_3x_quota": tax3,
            "total": total_before_relief,
        },
        "relief": relief,
    }