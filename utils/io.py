from __future__ import annotations

from pathlib import Path
import unicodedata
import re
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "RegTech_Data_Q1_Q5_2026.xlsx"

def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def normalize_text(s: object) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s

@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None]:
    """Load and standardize datasets for the Streamlit app.

    Returns:
        df_listings: listing-level table (frontage-only, Q1 & Q5)
        df_gov: unique (District, Ward, Street) gov-price table derived from listings
        summary_by_district: optional sheet if present (else None)
        top_streets: optional sheet if present (else None)
    """
    df = pd.read_excel(DATA_PATH, sheet_name="Listings Enriched")

    # -------------------------
    # Scope filters (as stated in the thesis)
    # -------------------------
    # Only District 1 & 5
    if "District" in df.columns:
        df = df[df["District"].isin([1, 5])].copy()

    # Only frontage houses (House Type == 1)
    if "House Type" in df.columns:
        df = df[df["House Type"] == 1].copy()

    # Extra safety: drop obvious alley/hẻm listings if any slipped through
    if "Listing Text" in df.columns:
        txt = df["Listing Text"].astype(str).str.lower()
        df = df[~txt.str.contains(r"\bhẻm\b|\bhxh\b|\bhx\b", regex=True)].copy()

    # -------------------------
    # Standardize commonly used columns
    # -------------------------
    unit_col = _pick_col(df, [
        "Unit Price (million VND/m²)",
        "Unit Price (million VND/m2)",
        "Unit_Price_mil_m2",
    ])
    gov_col = _pick_col(df, [
        "Gov Price 2026 Corrected (million VND/m²)",
        "Government Unit Price 2026 (million VND/m²)",
        "gov_unit_price_mil_by_pos",
        "gov_unit_price_mil",
    ])
    market_ref_col = _pick_col(df, [
        "Market Reference Unit Price (median, million VND/m²)",
        "market_ref",
        "Median_MarketRef",
    ])
    gap_col = _pick_col(df, [
        "Price Gap Corrected",
        "Price Gap (MarketRef / GovPrice)",
        "Median_PriceGap",
    ])
    fake_prob_col = _pick_col(df, [
        "Fake Probability (data quality)",
        "Độ tin cậy tin ảo (%)",
    ])
    risk_col = _pick_col(df, ["Risk Score", "Mean_Risk"])
    risk_level_col = _pick_col(df, ["Risk Level", "risk_level_gap"])

    # Create normalized internal columns (never rely on raw column names in pages)
    if unit_col:
        df["unit_price_mil_m2"] = pd.to_numeric(df[unit_col], errors="coerce")
    else:
        df["unit_price_mil_m2"] = pd.NA

    if gov_col:
        df["gov_price_mil_m2"] = pd.to_numeric(df[gov_col], errors="coerce")
    else:
        df["gov_price_mil_m2"] = pd.NA

    if market_ref_col:
        df["market_ref_mil_m2"] = pd.to_numeric(df[market_ref_col], errors="coerce")
    else:
        df["market_ref_mil_m2"] = pd.NA

    if gap_col:
        df["price_gap"] = pd.to_numeric(df[gap_col], errors="coerce")
    else:
        # fallback compute if both exist
        df["price_gap"] = df["market_ref_mil_m2"] / df["gov_price_mil_m2"]

    # Fake probability: store in [0,1]
    if fake_prob_col:
        fp = pd.to_numeric(df[fake_prob_col], errors="coerce")
        if fake_prob_col == "Độ tin cậy tin ảo (%)":
            fp = fp / 100.0
        df["fake_prob"] = fp.clip(lower=0, upper=1)
    else:
        df["fake_prob"] = pd.NA

    if risk_col:
        df["risk_score"] = pd.to_numeric(df[risk_col], errors="coerce")
    else:
        df["risk_score"] = pd.NA

    if risk_level_col:
        df["risk_level"] = df[risk_level_col].astype(str)
    else:
        df["risk_level"] = pd.NA

    # Ensure required address fields exist
    for c in ["District", "Ward", "Street"]:
        if c not in df.columns:
            df[c] = pd.NA

    # Create stable normalized keys used for matching/filtering
    if "ward_norm" not in df.columns:
        df["ward_norm"] = df["Ward"].map(normalize_text)
    if "road_norm" not in df.columns:
        # Some exports have StreetNorm already
        if "StreetNorm" in df.columns:
            df["road_norm"] = df["StreetNorm"].map(normalize_text)
        else:
            df["road_norm"] = df["Street"].map(normalize_text)

    # -------------------------
    # Gov-price table derived from listings (unique by Ward+Street+District)
    # -------------------------
    gov_match_col = _pick_col(df, ["Gov Price Match Type", "Match_Type"])
    note_col = _pick_col(df, ["Mapping Confidence Note"])

    gov_cols = ["District", "Ward", "Street", "ward_norm", "road_norm", "gov_price_mil_m2"]
    if gov_match_col:
        gov_cols.append(gov_match_col)
    if note_col:
        gov_cols.append(note_col)

    df_gov = df[gov_cols].dropna(subset=["gov_price_mil_m2"]).copy()
    df_gov = df_gov.drop_duplicates(subset=["District", "ward_norm", "road_norm"])

    # -------------------------
    # Optional precomputed sheets (if present)
    # -------------------------
    summary_by_district = None
    top_streets = None
    try:
        summary_by_district = pd.read_excel(DATA_PATH, sheet_name="Summary by District")
    except Exception:
        summary_by_district = None
    try:
        top_streets = pd.read_excel(DATA_PATH, sheet_name="Top Streets")
    except Exception:
        top_streets = None

    return df, df_gov, summary_by_district, top_streets