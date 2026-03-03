import streamlit as st

from utils.ui import apply_base_style

st.set_page_config(
    page_title="RegTech BĐS TP.HCM (Quận 1 & 5)",
    layout="wide",
)

apply_base_style()

st.title("RegTech BĐS TP.HCM")
st.caption("Tra cứu chênh lệch giá Nhà nước – thị trường và chấm điểm rủi ro dữ liệu tin đăng (tham khảo).")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Phạm vi dữ liệu**")
    st.markdown("- 02 quận: **Quận 1** và **Quận 5**")
    st.markdown("- Loại hình: **nhà ở mặt tiền** (đã loại nhà trong hẻm)")
with col2:
    st.markdown("**Chức năng**")
    st.markdown("- Tra cứu **GovPrice 2026** theo đường/phường")
    st.markdown("- Tính **MarketRef (median)**, **Price Gap**, **Risk Score**")
with col3:
    st.markdown("**Lưu ý**")
    st.markdown("<span class='badge'>Tham khảo</span>", unsafe_allow_html=True)
    st.markdown(
        "<div class='muted'>Kết quả không phải kết luận pháp lý/định giá chính thức. Khi sử dụng thực tế cần đối chiếu hồ sơ pháp lý, vị trí thửa đất và văn bản hiện hành.</div>",
        unsafe_allow_html=True,
    )

st.divider()

st.markdown(
    """
### Hướng dẫn sử dụng
- **Price Lookup:** chọn Quận → Phường → Đường để xem GovPrice 2026, MarketRef, Price Gap và Risk Score.
- **Tax & Fees:** ước tính tham khảo các khoản thuế/phí phổ biến trong giao dịch.
- **Dashboard:** xem phân bố Price Gap/Risk và bản đồ heatmap.

Nếu dữ liệu hiển thị chưa như mong muốn, bạn có thể điều chỉnh bộ lọc theo quận/phường/đường hoặc thay đổi chế độ bản đồ trong trang Dashboard.
"""
)
