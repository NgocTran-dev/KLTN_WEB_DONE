import pandas as pd
import streamlit as st

from utils.io import load_data
from utils.tax import (
    calc_non_agri_land_use_tax,
    calc_pit_real_estate_transfer,
    calc_registration_fee_land,
)

st.set_page_config(page_title="Tax & Fees (Tham khảo)", page_icon="🧾", layout="wide")

GOV = "Gov Price 2026 Corrected (million VND/m²)"
AREA = "Area (m²)"
TOTAL_PRICE = "Price (million VND)"

st.title("🧾 Tax & Fees (tham khảo)")
st.caption(
    "Ước tính nhanh 3 khoản phổ biến khi giao dịch BĐS: lệ phí trước bạ, thuế SDĐ phi nông nghiệp và thuế TNCN."
)

st.warning(
    "Kết quả chỉ mang tính tham khảo/giáo dục. Miễn/giảm và căn cứ tính có thể phụ thuộc hồ sơ thực tế, hạn mức địa phương và văn bản hiện hành."
)

# --- Load data ---
df, _, _ = load_data(frontage_only=True)

# --- Quick pick from dataset ---
st.subheader("1) Chọn nhanh một tin trong dữ liệu (tuỳ chọn)")

colA, colB, colC = st.columns([1, 1, 2])
with colA:
    district = st.selectbox("Quận", sorted(df["District"].dropna().unique().tolist()), index=0)
with colB:
    ward_options = sorted(df[df["District"] == district]["Ward"].dropna().unique().tolist())
    ward = st.selectbox("Phường", ward_options)
with colC:
    street_options = sorted(
        df[(df["District"] == district) & (df["Ward"] == ward)]["Street"].dropna().unique().tolist()
    )
    street = st.selectbox("Đường", street_options)

subset = df[(df["District"] == district) & (df["Ward"] == ward) & (df["Street"] == street)].copy()

st.caption(f"Số tin trong nhóm đã chọn: {len(subset):,}")

picked_row = None
if len(subset) > 0:
    # Create a lightweight selector label
    subset = subset.reset_index(drop=True)
    subset["__label__"] = (
        "#" + subset.index.astype(str)
        + " | " + subset[AREA].round(1).astype(str) + " m²"
        + " | " + subset[TOTAL_PRICE].round(0).astype(int).astype(str) + " tr"
    )
    pick_label = st.selectbox("Chọn 1 tin để autofill", subset["__label__"].tolist())
    picked_row = subset[subset["__label__"] == pick_label].iloc[0]

with st.expander("Xem nhanh dữ liệu trong nhóm (5 dòng)"):
    st.dataframe(
        subset[[AREA, TOTAL_PRICE, GOV, "Độ tin cậy tin ảo (%)", "Risk Score"]].head(5),
        use_container_width=True,
    )

# --- Inputs ---
st.subheader("2) Nhập tham số để tính (có thể chỉnh lại)")

# Default values from picked row
area_default = float(picked_row[AREA]) if picked_row is not None and pd.notna(picked_row[AREA]) else 80.0
price_default = (
    float(picked_row[TOTAL_PRICE]) if picked_row is not None and pd.notna(picked_row[TOTAL_PRICE]) else 8000.0
)
gov_default = float(picked_row[GOV]) if picked_row is not None and pd.notna(picked_row[GOV]) else 190.0

col1, col2, col3 = st.columns(3)
with col1:
    area_m2 = st.number_input("Diện tích đất (m²)", min_value=0.0, value=area_default, step=1.0)
with col2:
    gov_price_mil_per_m2 = st.number_input(
        "Giá đất tính theo bảng (triệu đồng/m²)", min_value=0.0, value=gov_default, step=1.0
    )
with col3:
    transfer_price_mil = st.number_input(
        "Giá chuyển nhượng (tổng, triệu đồng)", min_value=0.0, value=price_default, step=100.0
    )

st.markdown("---")

st.subheader("3) Miễn/giảm (tuỳ chọn)")

colx, coly, colz = st.columns(3)
with colx:
    pit_exempt = st.checkbox(
        "Miễn thuế TNCN? (VD: chuyển nhượng giữa vợ chồng/cha mẹ-con/… hoặc duy nhất 1 nhà ở)",
        value=False,
    )
with coly:
    reg_fee_exempt = st.checkbox(
        "Miễn lệ phí trước bạ? (VD: thừa kế/tặng cho giữa người thân theo quy định)",
        value=False,
    )
with colz:
    land_tax_exempt = st.checkbox(
        "Miễn thuế SDĐ phi nông nghiệp? (Điều 9 Luật 48/2010/QH12)",
        value=False,
    )

land_tax_reduce_50 = st.checkbox(
    "Giảm 50% thuế SDĐ phi nông nghiệp? (Điều 10 Luật 48/2010/QH12)",
    value=False,
    disabled=land_tax_exempt,
)

quota_m2 = st.number_input(
    "Hạn mức đất ở để tính thuế SDĐ PNN (m²) – tuỳ địa phương",
    min_value=0.0,
    value=120.0,
    step=10.0,
)

st.markdown("---")

st.subheader("4) Kết quả ước tính")

# --- Compute ---
reg_fee_mil = calc_registration_fee_land(
    area_m2=area_m2,
    gov_price_mil_per_m2=gov_price_mil_per_m2,
    is_exempt=reg_fee_exempt,
)

pit_mil = calc_pit_real_estate_transfer(
    transfer_price_mil=transfer_price_mil,
    is_exempt=pit_exempt,
)

land_tax_breakdown = calc_non_agri_land_use_tax(
    area_m2=area_m2,
    gov_price_mil_per_m2=gov_price_mil_per_m2,
    quota_m2=quota_m2,
    is_exempt=land_tax_exempt,
    is_reduce_50=land_tax_reduce_50,
)

colr1, colr2, colr3 = st.columns(3)
with colr1:
    st.metric("Lệ phí trước bạ (ước tính)", f"{reg_fee_mil:,.2f} triệu")
with colr2:
    st.metric("Thuế TNCN chuyển nhượng (ước tính)", f"{pit_mil:,.2f} triệu")
with colr3:
    st.metric("Thuế SDĐ PNN (ước tính / năm)", f"{land_tax_breakdown.total_mil:,.2f} triệu")

with st.expander("Chi tiết thuế SDĐ phi nông nghiệp (lũy tiến)"):
    st.write(
        {
            "Diện tích trong hạn mức (m²)": land_tax_breakdown.area_in_quota_m2,
            "Diện tích vượt <= 3 lần hạn mức (m²)": land_tax_breakdown.area_over_quota_up_to_3x_m2,
            "Diện tích vượt > 3 lần hạn mức (m²)": land_tax_breakdown.area_over_3x_m2,
            "Thuế phần trong hạn mức (triệu)": land_tax_breakdown.tax_in_quota_mil,
            "Thuế phần vượt <=3x (triệu)": land_tax_breakdown.tax_over_quota_up_to_3x_mil,
            "Thuế phần vượt >3x (triệu)": land_tax_breakdown.tax_over_3x_mil,
            "Tổng sau miễn/giảm (triệu)": land_tax_breakdown.total_mil,
        }
    )
)
