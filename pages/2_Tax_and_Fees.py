import streamlit as st

from utils.tax import (
    registration_fee_land_vnd,
    non_agri_land_tax_vnd,
    pit_transfer_tax_vnd,
)
from utils.style import inject_css

st.set_page_config(page_title="Tax & Fees | RegTech BĐS", page_icon="🧾", layout="wide")
inject_css()

st.title("🧾 Ước tính thuế & phí (tham khảo)")
st.markdown(
    """
<div class="small-note">
Trang này minh họa cách ước tính một số khoản phổ biến liên quan đến nhà/đất:
<b>lệ phí trước bạ</b>, <b>thuế sử dụng đất phi nông nghiệp</b> và <b>thuế TNCN khi chuyển nhượng</b>.
Các tùy chọn miễn/giảm dựa trên <b>tự khai</b> của người dùng và chỉ mang tính tham khảo.
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------
# Inputs
# ------------------------
c1, c2, c3 = st.columns(3)

with c1:
    district = st.selectbox("Quận (để gợi ý hạn mức)", options=[1, 5], index=0)
    area_m2 = st.number_input("Diện tích đất (m²)", min_value=0.0, value=80.0, step=1.0)

with c2:
    gov_price_mil_m2 = st.number_input(
        "Đơn giá Nhà nước (GovPrice) (triệu đồng/m²)",
        min_value=0.0,
        value=190.0 if district == 1 else 149.2,
        step=0.1,
        help="Bạn có thể copy từ trang Price Lookup.",
    )

with c3:
    transfer_price_bil = st.number_input(
        "Giá trị chuyển nhượng (tỷ đồng) (nếu có)",
        min_value=0.0,
        value=25.0,
        step=0.5,
        help="Dùng để tính thuế TNCN khi chuyển nhượng (2% x giá chuyển nhượng, trừ trường hợp được miễn).",
    )

st.divider()

# ------------------------
# Relief / exemption options (simplified)
# ------------------------
with st.expander("🎯 Tùy chọn miễn/giảm (tham khảo)", expanded=True):
    colA, colB, colC = st.columns(3)

    with colA:
        land_tax_relief = st.selectbox(
            "Ưu đãi thuế SDĐ phi nông nghiệp (đất ở)",
            options=[
                "Không áp dụng",
                "Miễn thuế (phần diện tích trong hạn mức)",
                "Giảm 50% (phần diện tích trong hạn mức)",
            ],
            index=0,
        )

    with colB:
        pit_exempt = st.checkbox(
            "Miễn thuế TNCN chuyển nhượng (ví dụ: giữa thân nhân, hoặc nhà/đất duy nhất...)",
            value=False,
        )

    with colC:
        regfee_exempt = st.checkbox(
            "Miễn lệ phí trước bạ (một số trường hợp tặng cho/thừa kế...)",
            value=False,
        )

    st.markdown(
        """
**Ghi chú nhanh (tóm tắt theo luật, không phải tư vấn pháp lý):**
- Thuế SDĐPNN (đất ở) là thuế **hàng năm**, có thuế suất **lũy tiến theo phần diện tích**.
- “Miễn/giảm” trong luật có điều kiện cụ thể (hộ nghèo, người có công, địa bàn khó khăn, bất khả kháng, ...).
- Thuế TNCN chuyển nhượng và lệ phí trước bạ cũng có các trường hợp miễn theo hồ sơ thực tế.
"""
    )

# quota suggestion (Q1 & Q5 share the same 160 m² in QĐ 69/2024/QĐ-UBND)
default_quota = 160.0
quota_m2 = st.number_input(
    "Hạn mức đất ở dùng để tính thuế SDĐPNN (m²)",
    min_value=0.0,
    value=default_quota,
    step=10.0,
    help="Mặc định 160 m² (áp dụng cho Quận 1 và Quận 5 theo QĐ 69/2024/QĐ-UBND). Bạn có thể chỉnh nếu trường hợp của bạn khác.",
)

relief_map = {
    "Không áp dụng": "none",
    "Miễn thuế (phần diện tích trong hạn mức)": "exempt_within_quota",
    "Giảm 50% (phần diện tích trong hạn mức)": "reduce50_within_quota",
}
relief_code = relief_map.get(land_tax_relief, "none")

# ------------------------
# Compute
# ------------------------
reg = registration_fee_land_vnd(area_m2=area_m2, gov_price_mil_m2=gov_price_mil_m2, exempt=regfee_exempt)
land_tax = non_agri_land_tax_vnd(area_m2=area_m2, gov_price_mil_m2=gov_price_mil_m2, quota_m2=quota_m2, relief=relief_code)
pit = pit_transfer_tax_vnd(transfer_price_billion_vnd=transfer_price_bil, exempt=pit_exempt)

# ------------------------
# Results
# ------------------------
st.subheader("Kết quả ước tính (VND)")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Lệ phí trước bạ (đất)", f"{reg['fee_vnd']:,.0f}")
r2.metric("Thuế SDĐPNN (năm)", f"{land_tax['tax_vnd']['total']:,.0f}")
r3.metric("Thuế TNCN chuyển nhượng", f"{pit['pit_vnd']:,.0f}")
r4.metric("Tổng (3 khoản)", f"{(reg['fee_vnd'] + land_tax['tax_vnd']['total'] + pit['pit_vnd']):,.0f}")

with st.expander("📌 Diễn giải chi tiết cách tính thuế SDĐPNN (đất ở)", expanded=False):
    seg = land_tax["segments"]
    tb = land_tax["tax_vnd_before_relief"]
    ta = land_tax["tax_vnd"]

    st.markdown(
        f"""
**Phân tách diện tích theo hạn mức:**
- Trong hạn mức: **{seg['within_quota_m2']:.1f} m²**
- Vượt hạn mức đến 3× hạn mức: **{seg['over_quota_to_3x_m2']:.1f} m²**
- Vượt trên 3× hạn mức: **{seg['over_3x_quota_m2']:.1f} m²**

**Thuế trước ưu đãi (VND):**
- Bậc 1 (0.03%): {tb['within_quota']:,.0f}
- Bậc 2 (0.07%): {tb['over_quota_to_3x']:,.0f}
- Bậc 3 (0.15%): {tb['over_3x_quota']:,.0f}
- **Tổng trước ưu đãi:** {tb['total']:,.0f}

**Sau ưu đãi đang chọn:** {land_tax['relief']}
- **Tổng sau ưu đãi:** {ta['total']:,.0f}
"""
    )

st.warning(
    """Lưu ý: Đây là công cụ ước tính học thuật. Thuế/phí thực tế phụ thuộc hồ sơ, thời điểm áp dụng văn bản, và kết luận của cơ quan thuế/cơ quan đăng ký. 
Nếu cần số liệu chính thức, bạn nên tra theo văn bản hiện hành và/hoặc hỏi cơ quan có thẩm quyền."""
)