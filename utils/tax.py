"""Tax & fee helpers (educational / reference only).

All values returned in *million VND* for convenience.

NOTE: This app provides only simplified estimates. In practice, tax bases,
exemptions/reductions, local land quotas (hạn mức), and dossier-specific rules
must be verified with current legal documents and local tax authorities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LandUseTaxBreakdown:
    area_in_quota_m2: float
    area_over_quota_up_to_3x_m2: float
    area_over_3x_m2: float
    tax_in_quota_mil: float
    tax_over_quota_up_to_3x_mil: float
    tax_over_3x_mil: float
    total_mil: float
    applied_reduction_factor: float


def calc_registration_fee_land(
    area_m2: float,
    gov_price_mil_per_m2: float,
    rate: float = 0.005,
    is_exempt: bool = False,
) -> float:
    """Lệ phí trước bạ (đất) ≈ 0.5% * (diện tích * giá tính lệ phí).

    Parameters
    ----------
    area_m2:
        Land area.
    gov_price_mil_per_m2:
        Land price used as fee base (often land price table).
    rate:
        Default 0.005 (0.5%).
    is_exempt:
        If True, return 0.
    """
    if is_exempt:
        return 0.0
    base_value_mil = max(area_m2, 0.0) * max(gov_price_mil_per_m2, 0.0)
    return base_value_mil * rate


def calc_pit_real_estate_transfer(
    transfer_price_mil: float,
    rate: float = 0.02,
    is_exempt: bool = False,
) -> float:
    """Personal income tax (PIT) for real-estate transfer.

    Simplified: PIT ≈ 2% * transfer price.

    Parameters
    ----------
    transfer_price_mil:
        Total transfer price in million VND.
    rate:
        Default 0.02 (2%).
    is_exempt:
        If True, return 0.
    """
    if is_exempt:
        return 0.0
    return max(transfer_price_mil, 0.0) * rate


def calc_non_agri_land_use_tax(
    area_m2: float,
    gov_price_mil_per_m2: float,
    quota_m2: float,
    is_exempt: bool = False,
    is_reduce_50: bool = False,
) -> LandUseTaxBreakdown:
    """Thuế sử dụng đất phi nông nghiệp (đất ở) - lũy tiến từng phần.

    Simplified based on Luật 48/2010/QH12 (Điều 7):
    - In quota: 0.03%
    - Over quota up to 3x: 0.07%
    - Over 3x: 0.15%

    Returns a breakdown for transparency.
    """

    area_m2 = float(max(area_m2, 0.0))
    gov_price_mil_per_m2 = float(max(gov_price_mil_per_m2, 0.0))
    quota_m2 = float(max(quota_m2, 0.0))

    # If quota is missing/0, treat the whole area as "in quota" to avoid divide confusion.
    if quota_m2 <= 0:
        quota_m2 = area_m2

    if is_exempt:
        return LandUseTaxBreakdown(
            area_in_quota_m2=area_m2,
            area_over_quota_up_to_3x_m2=0.0,
            area_over_3x_m2=0.0,
            tax_in_quota_mil=0.0,
            tax_over_quota_up_to_3x_mil=0.0,
            tax_over_3x_mil=0.0,
            total_mil=0.0,
            applied_reduction_factor=0.0,
        )

    a1 = min(area_m2, quota_m2)
    a2 = max(0.0, min(area_m2, 3.0 * quota_m2) - quota_m2)
    a3 = max(0.0, area_m2 - 3.0 * quota_m2)

    # Rates in percent
    t1 = a1 * gov_price_mil_per_m2 * (0.03 / 100.0)
    t2 = a2 * gov_price_mil_per_m2 * (0.07 / 100.0)
    t3 = a3 * gov_price_mil_per_m2 * (0.15 / 100.0)

    total = t1 + t2 + t3
    reduction_factor = 1.0
    if is_reduce_50:
        reduction_factor = 0.5
        total *= reduction_factor

    return LandUseTaxBreakdown(
        area_in_quota_m2=a1,
        area_over_quota_up_to_3x_m2=a2,
        area_over_3x_m2=a3,
        tax_in_quota_mil=t1 * (reduction_factor if is_reduce_50 else 1.0),
        tax_over_quota_up_to_3x_mil=t2 * (reduction_factor if is_reduce_50 else 1.0),
        tax_over_3x_mil=t3 * (reduction_factor if is_reduce_50 else 1.0),
        total_mil=total,
        applied_reduction_factor=reduction_factor,
    )
