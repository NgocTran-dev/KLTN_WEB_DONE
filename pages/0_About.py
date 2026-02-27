import streamlit as st

st.set_page_config(page_title="Giới thiệu", page_icon="ℹ️", layout="wide")

st.title("ℹ️ Giới thiệu & Lưu ý")

st.markdown(
    """Ứng dụng này được xây dựng trong khuôn khổ **khóa luận tốt nghiệp** theo hướng RegTech (risk-based decision support):  
kết hợp **dữ liệu tin đăng online** với **Bảng giá đất TP.HCM 2026 (GovPrice)** để hỗ trợ **nhà đầu tư/người mua** tra cứu benchmark và sàng lọc rủi ro.

### Phạm vi
- **Địa lý:** Quận 1 và Quận 5 (TP.HCM)  
- **Loại hình:** **nhà ở mặt tiền** (đã loại nhà trong hẻm)

### Các chỉ số chính
- **GovPrice (2026):** giá đất Nhà nước theo (quận, phường, đường).  
- **MarketRef:** giá thị trường tham chiếu (median) từ các tin đã làm sạch.  
- **Price Gap:** MarketRef / GovPrice (để thấy mức “vênh” giữa benchmark thị trường và benchmark chính thức).  
- **Risk Score (4 thành phần):**
  - **S_legal:** rủi ro pháp lý (tín hiệu “sổ hồng/sổ đỏ/…”, “vi bằng/giấy tay/…” trong mô tả)  
  - **S_fake:** rủi ro tin ảo/tin giả (P(fake) – tín hiệu chất lượng tin)  
  - **S_price:** rủi ro chênh lệch giá (log-normalized của unit_price / GovPrice)  
  - **S_plan:** rủi ro quy hoạch–tranh chấp (tín hiệu “quy hoạch/lộ giới/tranh chấp…”, có xét phủ định)

  RiskScore = Σ w·S, với **trọng số w theo CRITIC** (khách quan theo độ biến thiên & tương quan).

### Lưu ý quan trọng
- Các kết quả (GovPrice/MarketRef/Price Gap/Risk Score) chỉ mang tính **tham khảo/sàng lọc**, không phải kết luận pháp lý.
- Dữ liệu thị trường trong app là **giá chào bán** từ tin đăng, không phải giá giao dịch thực.
- Nghĩa vụ tài chính (thuế/phí) phụ thuộc hồ sơ, thời điểm và quy định áp dụng khi kê khai.

### Gợi ý khi sử dụng
- Dùng **Risk Score** như một *bộ lọc ưu tiên* để chọn tin/khu vực cần thẩm định sâu.
- Khi ra quyết định, hãy đối chiếu thêm:
  - giấy tờ pháp lý & ranh thửa,
  - thông tin quy hoạch chính thức (nếu có),
  - so sánh giá với nhiều nguồn,
  - văn bản thuế/phí mới nhất.
"""
)
