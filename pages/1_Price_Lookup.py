import streamlit as st
import pandas as pd

from utils.io import load_data
from utils.style import inject_css

st.set_page_config(page_title="Price Lookup | RegTech BĐS", page_icon="🔎", layout="wide")
inject_css()

st.title("🔎 Tra cứu giá đất Nhà nước & tham chiếu thị trường")
st.markdown(
    """
<div class="small-note">
Trang này giúp tra cứu nhanh theo <b>Quận → Phường → Đường</b>.
Kết quả hiển thị gồm: <b>GovPrice 2026</b> (giá Nhà nước), <b>MarketRef</b> (trung vị tham chiếu từ tin đăng đã làm sạch),
<b>Price Gap</b> và <b>Risk Score</b>.
</div>
""",
    unsafe_allow_html=True,
)

df, df_gov, _, _ = load_data()

# Sidebar filters
st.sidebar.header("Bộ lọc tra cứu")

district = st.sidebar.selectbox("Quận", options=[1, 5], index=0)

gov_d = df_gov[df_gov["District"] == district].copy()

ward_options = sorted(gov_d["Ward"].dropna().unique().tolist())
ward = st.sidebar.selectbox("Phường", options=ward_options)

gov_dw = gov_d[gov_d["Ward"] == ward].copy()

# Street search
street_search = st.sidebar.text_input("Tìm đường (gõ vài ký tự)", value="")
street_options = sorted(gov_dw["Street"].dropna().unique().tolist())
if street_search.strip():
    ss = street_search.strip().lower()
    street_options = [s for s in street_options if ss in str(s).lower()]

street = st.sidebar.selectbox("Đường", options=street_options)

# Filter listing-level table for the selected location
dff = df[(df["District"] == district) & (df["Ward"] == ward) & (df["Street"] == street)].copy()

# Pull a single gov row
gov_row = gov_dw[gov_dw["Street"] == street].head(1)

# Layout: summary metrics
left, right = st.columns([1, 1])

with left:
    st.subheader("Kết quả tra cứu")
    if gov_row.empty:
        st.error("Không tìm thấy GovPrice cho tuyến đường này trong dữ liệu hiện có.")
        gov_price = None
        match_type = None
    else:
        gov_price = float(gov_row.iloc[0]["gov_price_mil_m2"])
        match_col = "Gov Price Match Type" if "Gov Price Match Type" in gov_row.columns else None
        match_type = str(gov_row.iloc[0][match_col]) if match_col else "N/A"

        st.markdown(
            f"""
<span class="badge">GovPrice 2026</span> <b>{gov_price:,.1f}</b> triệu đồng/m²
<br>
<span class="small-note">Match type: <b>{match_type}</b></span>
""",
            unsafe_allow_html=True,
        )

    # Market reference & risk
    if not dff.empty:
        market_ref = float(dff["market_ref_mil_m2"].dropna().iloc[0]) if dff["market_ref_mil_m2"].notna().any() else None
        price_gap = float(dff["price_gap"].dropna().iloc[0]) if dff["price_gap"].notna().any() else None
        risk_score = float(dff["risk_score"].dropna().iloc[0]) if dff["risk_score"].notna().any() else None
        risk_level = str(dff["risk_level"].dropna().iloc[0]) if dff["risk_level"].notna().any() else "N/A"

        c1, c2, c3 = st.columns(3)
        if market_ref is not None:
            c1.metric("MarketRef (median)", f"{market_ref:,.1f} tr/m²")
        if price_gap is not None:
            c2.metric("Price Gap", f"{price_gap:,.2f}×")
        if risk_score is not None:
            c3.metric("Risk Score", f"{risk_score:,.3f}")

        st.markdown(f"<div class='small-note'>Phân loại rủi ro: <b>{risk_level}</b></div>", unsafe_allow_html=True)
    else:
        st.info("Chưa có tin đăng trong dữ liệu cho đúng (Quận, Phường, Đường) này.")

with right:
    st.subheader("Danh sách tin đăng (mẫu)")
    if dff.empty:
        st.write("—")
    else:
        show_cols = [
            "Price (million VND)",
            "Area (m²)",
            "unit_price_mil_m2",
            "fake_prob",
            "price_gap",
            "risk_score",
            "Listing Text",
        ]
        show_cols = [c for c in show_cols if c in dff.columns]
        preview = dff[show_cols].copy()

        # prettier formats
        if "fake_prob" in preview.columns:
            preview["fake_prob"] = (preview["fake_prob"] * 100).round(2)
            preview = preview.rename(columns={"fake_prob": "P(fake) (%)"})
        if "unit_price_mil_m2" in preview.columns:
            preview = preview.rename(columns={"unit_price_mil_m2": "Unit Price (tr/m²)"})
        if "price_gap" in preview.columns:
            preview = preview.rename(columns={"price_gap": "Price Gap"})
        if "risk_score" in preview.columns:
            preview = preview.rename(columns={"risk_score": "Risk Score"})

        st.dataframe(preview.head(30), use_container_width=True, height=420)

        # Download
        csv = preview.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Tải CSV (30 dòng đầu)",
            data=csv,
            file_name=f"price_lookup_Q{district}_{ward}_{street}.csv",
            mime="text/csv",
        )

st.divider()
st.warning(
    """Lưu ý: Dữ liệu thị trường là giá chào bán (asking price) từ tin đăng online; vị trí (lat/lon) được geocode theo đường/phường/quận nên chỉ mang tính xấp xỉ.
GovPrice/thuế/phí chỉ mang tính tham khảo học thuật."""
)