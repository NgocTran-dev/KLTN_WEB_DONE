import streamlit as st

from utils.io import load_data
from utils.style import inject_css

st.set_page_config(
    page_title="RegTech BĐS | KLTN",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

st.title("🏠 RegTech hỗ trợ tra cứu giá đất, ước tính thuế/phí & cảnh báo rủi ro tin đăng")
st.markdown(
    """
<div class="small-note">
Ứng dụng minh họa cho khóa luận tốt nghiệp (phạm vi dữ liệu: <b>Quận 1</b> & <b>Quận 5</b>, TP.HCM; chỉ xét <b>nhà ở mặt tiền</b>).
Tất cả kết quả chỉ mang tính <b>tham khảo học thuật</b>, không thay thế kết quả chính thức từ cơ quan có thẩm quyền.
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("🧭 Hướng dẫn sử dụng nhanh", expanded=True):
    st.markdown(
        """
- **Price Lookup**: chọn Quận → Phường → Đường để xem **GovPrice 2026**, **MarketRef**, **Price Gap** và **Risk Score**.
- **Tax & Fees**: nhập diện tích + giá trị để ước tính **lệ phí trước bạ**, **thuế SDĐ phi nông nghiệp**, **thuế TNCN chuyển nhượng** (có lựa chọn miễn/giảm).
- **Dashboard**: xem tổng quan theo khu vực, bảng xếp hạng tuyến đường và bản đồ nhiệt (heatmap).

💡 Mẹo: Nếu bạn không chắc đơn giá Nhà nước, hãy tra ở trang **Price Lookup** rồi copy sang trang **Tax & Fees**.
"""
    )

df, df_gov, summary_by_district, top_streets = load_data()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Số tin đăng (frontage)", f"{len(df):,}")
c2.metric("Số tuyến đường (unique)", f"{df[['District','ward_norm','road_norm']].drop_duplicates().shape[0]:,}")
c3.metric("Quận", "1 & 5")
c4.metric("Nguồn GovPrice", "Bảng giá đất 2026")

st.divider()

tab1, tab2 = st.tabs(["Phạm vi dữ liệu", "Lưu ý pháp lý / Disclaimer"])

with tab1:
    st.markdown(
        """
**Phạm vi được chuẩn hóa trong dữ liệu demo:**
- Không gian: **Quận 1** và **Quận 5** (TP.HCM).
- Loại hình: **nhà ở mặt tiền** (lọc loại bỏ tin đăng trong hẻm/hxh để giảm nhiễu & tăng độ khớp bảng giá).
- Nguồn thị trường: tin đăng online (giá chào bán) → có thể khác giá giao dịch thực tế.
- Vị trí bản đồ: tọa độ geocoding theo **đường/phường/quận** nên chỉ mang tính xấp xỉ theo tuyến đường.
"""
    )

with tab2:
    st.warning(
        """Ứng dụng không kiểm tra hồ sơ pháp lý thực tế, không thay thế quy trình định giá/thuế của cơ quan nhà nước.
Các tùy chọn “miễn/giảm” trong trang Tax & Fees dựa trên **tự khai của người dùng** để minh họa cách tính."""
    )

# Optional: show quick summary tables if available
if summary_by_district is not None:
    st.subheader("📌 Tóm tắt nhanh theo quận (từ file dữ liệu)")
    st.dataframe(summary_by_district, use_container_width=True)

if top_streets is not None:
    with st.expander("📈 Top tuyến đường theo Price Gap (từ file dữ liệu)", expanded=False):
        st.dataframe(top_streets.head(20), use_container_width=True)