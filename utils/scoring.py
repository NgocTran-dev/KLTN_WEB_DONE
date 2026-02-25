import numpy as np
import pandas as pd

def normalize_gap(price_gap, cap: float = 10.0) -> float:
    """
    Normalize Price Gap into [0,1] using log scaling:
    S_gap = min(1, log(PriceGap)/log(cap))
    - cap=10 means PriceGap >= 10 maps to 1.
    - For PriceGap < 1, score becomes < 0 and is clipped to 0.
    """
    if price_gap is None or (isinstance(price_gap, float) and pd.isna(price_gap)):
        return float("nan")
    pg = float(price_gap)
    pg = max(pg, 1e-6)
    s = np.log(pg) / np.log(cap)
    return float(np.clip(s, 0.0, 1.0))

def risk_score(fake_prob, gap_score, w_fake: float = 0.5) -> float:
    """
    Risk = w_fake * S_fake + (1 - w_fake) * S_gap
    """
    w = min(max(float(w_fake), 0.0), 1.0)
    fp = 0.0 if fake_prob is None or (isinstance(fake_prob, float) and pd.isna(fake_prob)) else float(fake_prob)
    gs = 0.0 if gap_score is None or (isinstance(gap_score, float) and pd.isna(gap_score)) else float(gap_score)
    return w * fp + (1.0 - w) * gs

def risk_level(score) -> str:
    """
    Map risk score to categorical level:
    Low < 0.3, Medium 0.3–0.6, High > 0.6
    """
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return "N/A"
    s = float(score)
    if s < 0.3:
        return "Low"
    if s < 0.6:
        return "Medium"
    return "High"
