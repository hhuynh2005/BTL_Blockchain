# MỤC 4.4: GIAO DIỆN CÔNG CỤ (04b_chuong4_giao_dien)
> **Tác giả phụ trách:** Nam Khánh (Dung lượng: 2 trang)  
> **Nội dung:** Giới thiệu Dashboard tương tác Streamlit, phân tích giao diện, luồng sử dụng và ảnh chụp màn hình.

---

## 4.4 Giao diện người dùng công cụ (Dashboard Streamlit)

### 4.4.1 Mục tiêu thiết kế giao diện
Nhằm giúp người dùng dễ dàng theo dõi, so sánh và kiểm chứng kết quả định giá token mà không cần can thiệp trực tiếp vào mã nguồn, nhóm đã xây dựng giao diện tương tác bằng framework **Streamlit** (mã nguồn tại `app/dashboard.py`).

Giao diện hướng tới 3 tiêu chí chính:
1. **Trực quan và tương tác cao:** Cho phép lựa chọn token linh hoạt, tùy biến thanh trượt trọng số các mô hình định giá trong thời gian thực.
2. **Minh bạch thông tin:** Hiển thị chi tiết từng đường định giá của từng mô hình thành phần cạnh đường giá thị trường thực tế.
3. **Tích hợp on-chain:** Cung cấp thông tin trực tiếp về smart contract trên mạng Sepolia, trạng thái giao dịch Oracle và liên kết kiểm tra trên Etherscan.

### 4.4.2 Bố cục và các tính năng chính
- **Thanh điều hướng Sidebar:**
  - Danh sách chọn token (UNI, AAVE, LINK, MKR, CRV,...) lấy trực tiếp từ cấu hình `config/tokens.yaml`.
  - Bộ thanh trượt điều chỉnh trọng số $w_i$ cho 4 mô hình: NVT, MV=PQ, TWAP, Comparable MC/TVL với cơ chế tự động chuẩn hóa $\sum w_i = 1.0$.
- **Khu vực tóm tắt chỉ số chính (Metric Cards):**
  - *Giá thị trường hiện tại (Spot Price).*
  - *Giá trị hợp lý tính toán bởi Ensemble (Fair Value).*
  - *Độ lệch phần trăm và tín hiệu định giá:* Hiển thị rõ nhãn **Undervalued** (nếu lệch dương > 5%), **Overvalued** (nếu lệch âm < -5%) hoặc **Fairly Valued**.
  - *Sai số kiểm thử lịch sử MAE.*
- **Biểu đồ chuỗi thời gian chính (Interactive Line Chart):**
  - So sánh trực tiếp giữa đường giá thị trường và giá trị định giá của Ensemble.
- **Khu vực các Tab chuyên sâu:**
  - *Tab 1: Chi tiết từng mô hình:* Bóc tách đường giá của NVT, MV=PQ, TWAP và So sánh để thấy rõ sự đóng góp của từng thành phần.
  - *Tab 2: Trạng thái Smart Contract Sepolia:* Hiển thị địa chỉ contract, mã hash giao dịch Oracle gần nhất, mã token trên Sepolia và thời gian cập nhật cuối cùng.
  - *Tab 3: Bảng dữ liệu chi tiết:* Xuất bảng dữ liệu chuỗi thời gian các phiên giao dịch gần nhất.

### 4.4.3 Luồng sử dụng (User Workflow)
1. Người dùng mở trình duyệt truy cập ứng dụng Streamlit tại cổng mặc định `localhost:8501`.
2. Chọn token mục tiêu từ danh mục trên thanh bên trái.
3. Quan sát các thẻ chỉ số để nắm bắt ngay tình trạng định giá hiện tại của token.
4. Tùy chỉnh trọng số theo khẩu vị phân tích hoặc giữ nguyên trọng số tối ưu hóa MAE.
5. Kiểm tra tính xác thực của dữ liệu on-chain trong Tab Smart Contract bằng cách đối chiếu địa chỉ và mã giao dịch trên Sepolia Etherscan.
