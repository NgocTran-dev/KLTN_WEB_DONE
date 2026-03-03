import streamlit as st

from utils.ui import apply_base_style

st.set_page_config(page_title="Giới thiệu", layout="wide")
apply_base_style()

st.title("Giới thiệu")

st.markdown(
    """Ứng dụng được xây dựng trong khuôn khổ **khóa luận tốt nghiệp** theo hướng RegTech (risk-based decision support):  
kết hợp **dữ liệu tin đăng online** với **Bảng giá đất TP.HCM 2026 (GovPrice)** để hỗ trợ **người mua/nhà đầu tư** tra cứu benchmark và sàng lọc rủi ro.

### Phạm vi
- **Địa lý:** Quận 1 và Quận 5 (TP.HCM)  
- **Loại hình:** **nhà ở mặt tiền** (đã loại nhà trong hẻm)

### Các chỉ số chính
- **GovPrice (2026):** giá đất Nhà nước theo (quận, phường, đường).  
- **MarketRef:** giá thị trường tham chiếu (median) từ các tin đã làm sạch.  
- **Price Gap:** MarketRef / GovPrice.  
- **Risk Score (4 thành phần):**
  - **S_legal:** tín hiệu pháp lý trong mô tả (ví dụ: “sổ hồng/sổ đỏ…”, “vi bằng/giấy tay…”)  
  - **S_fake:** xác suất tin ảo (P(fake)) dựa trên tín hiệu chất lượng tin  
  - **S_price:** mức chênh lệch giá (chuẩn hóa theo unit_price / GovPrice)  
  - **S_plan:** tín hiệu quy hoạch–tranh chấp (ví dụ: “quy hoạch/lộ giới/tranh chấp…”)
"""
)

st.markdown(
    """### Nguồn và giới hạn
- Dữ liệu tin đăng được thu thập và làm sạch phục vụ mục đích nghiên cứu.
- Một số thông tin có thể thiếu hoặc không đồng nhất giữa các nguồn.
- Kết quả hiển thị mang tính tham khảo và không thay thế tư vấn chuyên môn.
"""
)
