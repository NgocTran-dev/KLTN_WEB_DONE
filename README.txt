import numpy as np
import pandas as pd

def normalize_gap(price_gap: float, cap: float = 10.0) -> float:
    if price_gap is None:
        return float("nan")
    pg = float(price_gap)
    pg = max(pg, 1e-6)
    s = np.log(pg) / np.log(cap)
    return float(np.clip(s, 0.0, 1.0))

def risk_score(fake_prob: float, gap_score: float, w_fake: float = 0.5) -> float:
    w = min(max(float(w_fake), 0.0), 1.0)
    fp = 0.0 if fake_prob is None else float(fake_prob)
    gs = 0.0 if gap_score is None else float(gap_score)
    return w*fp + (1.0-w)*gs

def risk_level(score: float) -> str:
    if score is None or pd.isna(score):
        return "N/A"
    s = float(score)
    if s < 0.3:
        return "Low"
    if s < 0.6:
        return "Medium"
    return "High"