import numpy as np
import pandas as pd
import streamlit as st

from utils.io import load_data
from utils.scoring import normalize_price_gap, RiskConfig

st.set_page_config(page_title="Price Lookup", layout="wide")

st.title("Tra cứu GovPrice & MarketRef theo tuyến đường")
st.caption("Dữ liệu: tin đăng nhà ở mặt tiền (Q1, Q5) đã làm sạch; GovPrice theo Bảng giá đất TP.HCM 2026; MarketRef theo thống kê robust.")

listings_df, summary_by_district, top_streets = load_data()

cfg = RiskConfig()
GOV = cfg.gov_price_col
UNIT = cfg.unit_price_col
FAKE = cfg.fake_prob_col
MARKET = "Market Reference Unit Price (median, million VND/m²)"
GAP = "Price Gap Corrected (MarketRef / GovPrice)"
RISK = "Risk Score"
RISK_LEVEL = "Risk Level"

# Components (added by utils.scoring.compute_risk_score)
S_LEGAL = "S_legal"
S_PLAN = "S_plan"
S_PRICE = "S_price"
S_FAKE = "S_fake"
LISTING_GAP = "ListingGap"

MATCH = "Match Type"

# --- Sidebar filters ---
st.sidebar.header("Bộ lọc")
districts = sorted([d for d in top_streets["District"].dropna().unique()])
district = st.sidebar.selectbox("Quận", districts, index=0)

wards = sorted(top_streets.loc[top_streets["District"] == district, "Ward"].dropna().unique())
ward = st.sidebar.selectbox("Phường", wards, index=0 if wards else None)

streets = sorted(
    top_streets.loc[(top_streets["District"] == district) & (top_streets["Ward"] == ward), "Street"]
    .dropna()
    .unique()
)
street = st.sidebar.selectbox("Đường", streets, index=0 if streets else None)

if ward is None or street is None:
    st.info("Vui lòng chọn đủ Quận/Phường/Đường.")
    st.stop()

# Filter listing-level data
dff = listings_df[(listings_df["District"] == district) & (listings_df["Ward"] == ward) & (listings_df["Street"] == street)].copy()
if len(dff) == 0:
    st.warning("Không có dữ liệu cho lựa chọn này.")
    st.stop()

# --- Aggregated metrics (street-level) ---
m_gov = float(np.nanmedian(dff[GOV])) if GOV in dff else float("nan")
m_market = float(np.nanmedian(dff[MARKET])) if MARKET in dff else float("nan")
m_gap = float(np.nanmedian(dff[GAP])) if GAP in dff else (
    m_market / m_gov if (pd.notna(m_market) and pd.notna(m_gov) and m_gov > 0) else float("nan")
)

m_risk = float(np.nanmean(dff[RISK])) if RISK in dff else float("nan")
m_fake = float(np.nanmean(dff[S_FAKE])) if S_FAKE in dff else float("nan")
m_legal = float(np.nanmean(dff[S_LEGAL])) if S_LEGAL in dff else float("nan")
m_plan = float(np.nanmean(dff[S_PLAN])) if S_PLAN in dff else float("nan")
m_price = float(np.nanmean(dff[S_PRICE])) if S_PRICE in dff else float("nan")

s_gap = normalize_price_gap(m_gap) if pd.notna(m_gap) else float("nan")

# Match type (mode)
match_type = None
if MATCH in dff.columns:
    mm = dff[MATCH].dropna()
    if len(mm) > 0:
        match_type = mm.mode().iloc[0]

# Weights (from load_data)
weights = st.session_state.get("risk_weights", {})

# --- Display ---
left, mid, right = st.columns([1.15, 1.15, 1.2])
with left:
    st.subheader("Kết quả tra cứu")
    st.write(f"**Khu vực:** Quận {district} • {ward} • {street}")
    st.write(f"**Số tin trong nhóm:** {len(dff):,}")
    if match_type:
        st.caption(f"GovPrice match type (tham khảo): {match_type}")

with mid:
    st.metric("GovPrice 2026 (median)", f"{m_gov:,.1f} tr/m²" if pd.notna(m_gov) else "—")
    st.metric("MarketRef (median)", f"{m_market:,.1f} tr/m²" if pd.notna(m_market) else "—")

with right:
    st.metric("Price Gap (median)", f"{m_gap:,.3f}×" if pd.notna(m_gap) else "—")
    st.metric("Risk Score (mean)", f"{m_risk:,.3f}" if pd.notna(m_risk) else "—")
    st.caption(
        f"S_fake={m_fake:,.3f} • S_price={m_price:,.3f} • S_legal={m_legal:,.3f} • S_plan={m_plan:,.3f} • "
        f"S_gap (chuẩn hoá)={s_gap:,.3f}"
    )

if weights:
    st.caption(
        "Trọng số (CRITIC): "
        + ", ".join([f"{k}={v:.2f}" for k, v in weights.items()])
    )

st.divider()

with st.expander("Cách tính Risk Score (4 thành phần)", expanded=False):
    st.markdown(
        """- **S_legal (pháp lý)**: trích xuất tín hiệu từ mô tả tin đăng (ví dụ “sổ hồng/sổ đỏ” → 0; “vi bằng/giấy tay/sổ chung…” → 1; thiếu thông tin → 0.5).  
- **S_fake (tin ảo)**: xác suất P(fake) từ mô hình tham khảo (dạng % → quy đổi về 0..1).  
- **S_price (chênh lệch giá)**: chuẩn hóa log theo *ListingGap = unit_price / GovPrice*, với cap=10.  
- **S_plan (quy hoạch–tranh chấp)**: trích xuất tín hiệu “quy hoạch/lộ giới/tranh chấp…”, phân biệt câu khẳng định an toàn (“không quy hoạch…”) và câu cảnh báo (“dính quy hoạch…”).  

RiskScore = Σ w·S (trọng số w theo CRITIC). Mức rủi ro Low/Medium/High được phân theo phân vị (Q33/Q67) trên toàn bộ dữ liệu.
"""
    )

st.subheader("Chi tiết tin trong nhóm")

show_cols = [
    "Area (m²)",
    "Price (million VND)",
    UNIT,
    GOV,
    MARKET,
    GAP,
    LISTING_GAP,
    S_FAKE,
    S_PRICE,
    S_LEGAL,
    S_PLAN,
    RISK,
    RISK_LEVEL,
]
show_cols = [c for c in show_cols if c in dff.columns]

sort_col = GAP if GAP in dff.columns else (RISK if RISK in dff.columns else show_cols[0])

st.dataframe(
    dff[show_cols].sort_values(sort_col, ascending=False).head(80),
    use_container_width=True,
)
