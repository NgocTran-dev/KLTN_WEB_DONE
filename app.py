import streamlit as st

st.set_page_config(
    page_title="RegTech BĐS TP.HCM (Quận 1 & 5)",
    page_icon="🏙️",
    layout="wide",
)

# --- Simple styling (kept lightweight for Streamlit Cloud) ---
st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; padding-bottom: 2rem; }
      [data-testid="stMetricValue"] { font-size: 1.6rem; }
      .small-muted { color: rgba(49, 51, 63, 0.7); font-size: 0.9rem; }
      .badge { display:inline-block; padding:0.15rem 0.5rem; border-radius: 999px; background:#f1f3f6; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏙️ RegTech BĐS TP.HCM")
st.caption("Tra cứu chênh lệch giá Nhà nước – thị trường (tham khảo) & chấm điểm rủi ro dữ liệu tin đăng")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Phạm vi dữ liệu**")
    st.markdown("- 02 quận: **Quận 1** và **Quận 5**")
    st.markdown("- Loại hình: **nhà ở mặt tiền** (đã loại nhà trong hẻm)")
with col2:
    st.markdown("**Tính năng chính**")
    st.markdown("- Tra cứu **GovPrice 2026** theo đường/phường")
    st.markdown("- Tính **MarketRef (median)**, **Price Gap**, **Risk Score**")
with col3:
    st.markdown("**Cảnh báo pháp lý**")
    st.markdown(
        "<span class='badge'>Chỉ mang tính tham khảo</span> ",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='small-muted'>Kết quả không phải kết luận pháp lý/định giá chính thức. Khi dùng thực tế nên đối chiếu hồ sơ pháp lý, vị trí thửa đất, và văn bản thuế hiện hành.</div>",
        unsafe_allow_html=True,
    )

st.divider()

st.markdown(
    """
**Cách dùng nhanh**
1. Vào trang **Price Lookup** để chọn **Quận → Phường → Đường** và xem GovPrice 2026, MarketRef, Price Gap và Risk Score.
2. Vào trang **Tax & Fees** để ước tính *tham khảo* các khoản thuế/phí phổ biến và thử bật **miễn/giảm** theo từng trường hợp.
3. Vào trang **Dashboard** để xem phân bố Price Gap/Risk và bản đồ heatmap.

> Gợi ý: Nếu bạn đang làm phần *minh họa thao tác web* cho khóa luận, hãy chụp màn hình ở các trang trên (có thể bật/tắt bộ lọc để ra đúng ví dụ bạn muốn trình bày).
"""
)

st.info(
    "Nếu heatmap nhìn bị dồn 1 chỗ: hãy thử (1) chuyển sang chế độ **Theo tuyến đường**; (2) giảm **bán kính heatmap**; (3) zoom gần hơn theo từng quận."
)
