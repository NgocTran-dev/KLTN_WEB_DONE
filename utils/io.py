from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict

import pandas as pd
import streamlit as st

from utils.scoring import compute_risk_score, RiskConfig


DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "RegTech_Data_Q1_Q5_2026.xlsx"
)


def _mode_or_na(s: pd.Series):
    if s.empty:
        return "N/A"
    m = s.mode(dropna=True)
    return m.iloc[0] if not m.empty else "N/A"


@st.cache_data(show_spinner=False)
def load_data(path: str | Path = DEFAULT_DATA_PATH, frontage_only: bool = True):
    """Load & enrich data for the Streamlit app.

    Notes
    -----
    - Computes 4-component Risk Score (legal, fake, price discrepancy, planning/dispute)
      and stores the CRITIC weights in st.session_state["risk_weights"].
    - Recomputes the summary tables from the enriched listings, so the dashboard always
      stays consistent with the current scoring logic.

    Returns
    -------
    listings_df, summary_by_district_df, top_streets_df
    """
    path = Path(path)
    listings = pd.read_excel(path, sheet_name="Listings Enriched")

    # Optional: enforce thesis scope (frontage only)
    if frontage_only and "House Type" in listings.columns:
        listings = listings[listings["House Type"] == 1].copy()

    # Basic type coercion for mapping
    for col in ["Latitude", "Longitude"]:
        if col in listings.columns:
            listings[col] = pd.to_numeric(listings[col], errors="coerce")

    # Compute Risk Score & component columns
    cfg = RiskConfig()
    listings, weights = compute_risk_score(listings, method="critic", cfg=cfg)

    # ------------------------------------------------------------------
    # Column compatibility layer
    # ------------------------------------------------------------------
    # Different data versions may store the (MarketRef/GovPrice) ratio under
    # slightly different names. The dashboard expects a canonical column name.
    canonical_gap = "Price Gap Corrected (MarketRef / GovPrice)"
    if canonical_gap not in listings.columns:
        candidates = [
            "Price Gap Corrected",
            "Price Gap (MarketRef / GovPrice)",
            "Price Gap",
        ]
        found = next((c for c in candidates if c in listings.columns), None)

        if found is not None:
            listings[canonical_gap] = pd.to_numeric(listings[found], errors="coerce")
        else:
            # Last-resort: compute from MarketRef and GovPrice if available.
            market_col = "Market Reference Unit Price (median, million VND/m²)"
            if market_col in listings.columns and cfg.gov_price_col in listings.columns:
                m = pd.to_numeric(listings[market_col], errors="coerce")
                g = pd.to_numeric(listings[cfg.gov_price_col], errors="coerce").replace(0, pd.NA)
                listings[canonical_gap] = m / g
            else:
                listings[canonical_gap] = pd.NA

    # Optional alias for match type (older/newer datasets)
    if "Match Type" not in listings.columns and "Gov Price Match Type" in listings.columns:
        listings["Match Type"] = listings["Gov Price Match Type"]

    # Make weights accessible across pages
    st.session_state["risk_weights"] = weights

    # --- Summary by district ---
    summary = (
        listings.groupby("District", dropna=False)
        .agg(
            Total_Listings=("Risk Score", "size"),
            Median_UnitPrice=("Unit Price (million VND/m²)", "median"),
            Median_GovPrice=(cfg.gov_price_col, "median"),
            Median_MarketRef=("Market Reference Unit Price (median, million VND/m²)", "median"),
            Median_PriceGap=("Price Gap Corrected (MarketRef / GovPrice)", "median"),
            Mean_Risk=("Risk Score", "mean"),
        )
        .reset_index()
    )

    # --- Top streets table (for drill-down & ranking) ---
    # Keep streets with enough listings so medians are meaningful
    street_grp = listings.groupby(["District", "Ward", "Street"], dropna=False)

    top_streets = (
        street_grp.agg(
            Listings=("Risk Score", "size"),
            Median_MarketRef=("Market Reference Unit Price (median, million VND/m²)", "median"),
            Median_GovPrice=(cfg.gov_price_col, "median"),
            Median_PriceGap=("Price Gap Corrected (MarketRef / GovPrice)", "median"),
            Mean_Risk=("Risk Score", "mean"),
            Match_Type=("Match Type", _mode_or_na) if "Match Type" in listings.columns else ("Risk Score", _mode_or_na),
        )
        .reset_index()
    )

    return listings, summary, top_streets
