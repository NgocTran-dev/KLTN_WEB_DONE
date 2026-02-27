"""Utility functions for scoring and risk analytics.

This module implements:
- Risk component extraction from listing text (legal risk, planning/dispute risk)
- Price discrepancy normalization (log-scaled)
- Objective weighting via CRITIC
- Composite Risk Score and risk level mapping

The goal is to keep the score:
(1) transparent / explainable,
(2) data-driven (weights),
(3) robust to outliers.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


# ----------------------------
# Text helpers
# ----------------------------

def _to_text(x) -> str:
    return x.lower() if isinstance(x, str) else ""


# ----------------------------
# Risk components
# ----------------------------

LEGAL_RISK_PATTERNS = [
    r"vi\s*bằng",
    r"giấy\s*tay",
    r"giay\s*tay",
    r"sổ\s*chung",
    r"so\s*chung",
    r"chung\s*sổ",
    r"chưa\s*có\s*sổ",
    r"chua\s*co\s*so",
    r"chờ\s*sổ",
    r"cho\s*so",
    r"hđmb",
    r"hợp\s*đồng\s*mua\s*bán",
    r"hop\s*dong\s*mua\s*ban",
    r"ủy\s*quyền",
    r"uỷ\s*quyền",
    r"uy\s*quyen",
    r"góp\s*vốn",
    r"gop\s*von",
    r"giấy\s*viết\s*tay",
    r"giay\s*viet\s*tay",
]

LEGAL_CLEAR_PATTERNS = [
    r"sổ\s*hồng",
    r"sổ\s*đỏ",
    r"so\s*hong",
    r"so\s*do",
    r"sổ\s*riêng",
    r"so\s*rieng",
    r"chính\s*chủ",
    r"chinh\s*chu",
    r"pháp\s*lý\s*chuẩn",
    r"phap\s*ly\s*chuan",
    r"hoàn\s*công",
    r"hoan\s*cong",
    r"công\s*chứng",
    r"cong\s*chung",
    r"sang\s*tên",
    r"sang\s*ten",
    r"đăng\s*bộ",
    r"dang\s*bo",
]


def legal_risk_score(listing_text: str) -> float:
    """Return legal risk score in {0, 0.5, 1}."""
    t = _to_text(listing_text)

    if any(re.search(p, t) for p in LEGAL_RISK_PATTERNS):
        return 1.0
    if any(re.search(p, t) for p in LEGAL_CLEAR_PATTERNS):
        return 0.0
    return 0.5


PLANNING_KEYWORDS = [
    r"quy\s*hoạch",
    r"quy\s*hoach",
    r"lộ\s*giới",
    r"lo\s*gioi",
    r"tranh\s*chấp",
    r"tranh\s*chap",
    r"giải\s*tỏa",
    r"giai\s*toa",
    r"treo",
]

PLANNING_SAFE_PATTERNS = [
    r"không\s*dính\s*quy\s*hoạch",
    r"khong\s*dinh\s*quy\s*hoach",
    r"không\s*nằm\s*trong\s*quy\s*hoạch",
    r"khong\s*nam\s*trong\s*quy\s*hoach",
    r"không\s*quy\s*hoạch",
    r"khong\s*quy\s*hoach",
    r"không\s*lộ\s*giới",
    r"khong\s*lo\s*gioi",
    r"không\s*tranh\s*chấp",
    r"khong\s*tranh\s*chap",
    r"không\s*bị\s*lộ\s*giới",
    r"khong\s*bi\s*lo\s*gioi",
    r"không\s*bị\s*quy\s*hoạch",
    r"khong\s*bi\s*quy\s*hoach",
    r"có\s*giấy\s*xác\s*nhận\s*quy\s*hoạch",
    r"co\s*giay\s*xac\s*nhan\s*quy\s*hoach",
    r"quy\s*hoạch\s*ổn\s*định",
    r"quy\s*hoach\s*on\s*dinh",
]

PLANNING_RISK_PATTERNS = [
    r"dính\s*quy\s*hoạch",
    r"dinh\s*quy\s*hoach",
    r"nằm\s*trong\s*quy\s*hoạch",
    r"nam\s*trong\s*quy\s*hoach",
    r"bị\s*quy\s*hoạch",
    r"bi\s*quy\s*hoach",
    r"quy\s*hoạch\s*treo",
    r"quy\s*hoach\s*treo",
    r"đang\s*tranh\s*chấp",
    r"dang\s*tranh\s*chap",
    r"tranh\s*chấp",
    r"tranh\s*chap",
    r"lộ\s*giới",
    r"lo\s*gioi",
    r"giải\s*tỏa",
    r"giai\s*toa",
]


def planning_risk_score(listing_text: str) -> float:
    """Return planning/dispute risk score in {0, 0.5, 1}.

    - 0.0: explicitly stated safe ("không quy hoạch", "không tranh chấp"...)
    - 1.0: explicit red-flag mention ("dính quy hoạch", "đang tranh chấp"...)
    - 0.5: no mention / ambiguous (information missing)
    """
    t = _to_text(listing_text)

    if not any(re.search(k, t) for k in PLANNING_KEYWORDS):
        return 0.5
    if any(re.search(p, t) for p in PLANNING_SAFE_PATTERNS):
        return 0.0
    if any(re.search(p, t) for p in PLANNING_RISK_PATTERNS):
        return 1.0
    return 0.5


# ----------------------------
# Price discrepancy
# ----------------------------

def normalize_log_ratio(ratio: float, cap: float = 10.0) -> float:
    """Normalize a positive ratio into [0, 1] using log scaling.

    score = min(1, log(ratio) / log(cap))
    Values <= 1 map to 0, and ratio >= cap maps to 1.
    """
    if ratio is None or not np.isfinite(ratio) or ratio <= 0:
        return float("nan")
    ratio = max(ratio, 1e-9)
    score = math.log(ratio) / math.log(cap)
    return float(np.clip(score, 0.0, 1.0))


def normalize_price_gap(price_gap: float, cap: float = 10.0) -> float:
    """Backward-compatible alias (older pages import this name)."""
    return normalize_log_ratio(price_gap, cap=cap)


# ----------------------------
# CRITIC weights
# ----------------------------

def critic_weights(df: pd.DataFrame, cols: List[str]) -> Dict[str, float]:
    """Compute objective weights using the CRITIC method.

    Cj = std_j * sum_k (1 - corr_jk)
    wj = Cj / sum_j Cj
    """
    X = df[cols].astype(float).copy()
    # Replace inf and drop rows with NaN
    X = X.replace([np.inf, -np.inf], np.nan).dropna(how="any")
    if X.empty:
        # Fallback to equal weights
        m = len(cols)
        return {c: 1.0 / m for c in cols}

    stds = X.std(ddof=0)
    corr = X.corr().fillna(0.0)

    C = {}
    for c in cols:
        C[c] = float(stds[c] * (1.0 - corr[c]).sum())

    total = sum(C.values())
    if total <= 0:
        m = len(cols)
        return {c: 1.0 / m for c in cols}

    return {c: C[c] / total for c in cols}


# ----------------------------
# Composite Risk Score
# ----------------------------

@dataclass(frozen=True)
class RiskConfig:
    text_col: str = "Listing Text"
    fake_prob_col: str = "Độ tin cậy tin ảo (%)"
    unit_price_col: str = "Unit Price (million VND/m²)"
    gov_price_col: str = "Gov Price 2026 Corrected (million VND/m²)"
    cap_ratio: float = 10.0


def add_risk_components(df: pd.DataFrame, cfg: RiskConfig = RiskConfig()) -> pd.DataFrame:
    """Add component columns: S_legal, S_plan, S_fake, S_price, ListingGap."""
    out = df.copy()

    # Text-based components
    if cfg.text_col in out.columns:
        out["S_legal"] = out[cfg.text_col].apply(legal_risk_score)
        out["S_plan"] = out[cfg.text_col].apply(planning_risk_score)
    else:
        out["S_legal"] = np.nan
        out["S_plan"] = np.nan

    # Fake probability (convert % to 0..1 if needed)
    if cfg.fake_prob_col in out.columns:
        fake = out[cfg.fake_prob_col].astype(float)
        if fake.max(skipna=True) > 1.0:
            fake = fake / 100.0
        out["S_fake"] = fake.clip(0.0, 1.0)
    else:
        out["S_fake"] = np.nan

    # Price discrepancy
    if cfg.unit_price_col in out.columns and cfg.gov_price_col in out.columns:
        unit = out[cfg.unit_price_col].astype(float)
        gov = out[cfg.gov_price_col].astype(float)
        ratio = unit / gov.replace(0, np.nan)
        out["ListingGap"] = ratio
        out["S_price"] = ratio.apply(lambda r: normalize_log_ratio(r, cap=cfg.cap_ratio))
    else:
        out["ListingGap"] = np.nan
        out["S_price"] = np.nan

    return out


def compute_risk_score(
    df: pd.DataFrame,
    method: str = "critic",
    cfg: RiskConfig = RiskConfig(),
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Compute Risk Score (4 components) and return (df_with_cols, weights)."""
    out = add_risk_components(df, cfg=cfg)

    cols = ["S_legal", "S_fake", "S_price", "S_plan"]
    if weights is None:
        if method.lower() == "equal":
            weights = {c: 1.0 / len(cols) for c in cols}
        else:
            weights = critic_weights(out, cols)

    # Fill NaN with 0.5 as neutral/unknown (conservative)
    X = out[cols].astype(float).copy()
    X = X.fillna(0.5)

    out["Risk Score"] = sum(weights[c] * X[c] for c in cols)

    # Risk level by tertiles (Q33/Q67) for data-driven thresholds
    q33 = float(out["Risk Score"].quantile(1 / 3))
    q67 = float(out["Risk Score"].quantile(2 / 3))

    def _level(s: float) -> str:
        if not np.isfinite(s):
            return "N/A"
        if s <= q33:
            return "Low"
        if s <= q67:
            return "Medium"
        return "High"

    out["Risk Level"] = out["Risk Score"].apply(_level)
    out["Risk_Q33"] = q33
    out["Risk_Q67"] = q67

    return out, weights
