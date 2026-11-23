# CHƯƠNG 4: THIẾT KẾ VÀ XÂY DỰNG CÔNG CỤ (04a_chuong4_thiet_ke)
> **Tác giả phụ trách:** Huỳnh (Mục 4.1 - 4.3: 6 trang)  
> **Nội dung:** 4.1 Yêu cầu & Kiến trúc hệ thống; 4.2 Thiết kế chi tiết các mô hình định giá & Ensemble; 4.3 Cài đặt Python & Smart Contract TokenValuation.sol.

---

## 4.1 Yêu cầu và Kiến trúc hệ thống (1 trang)
- **Yêu cầu chức năng:**
  1. Tự động thu thập và tiền xử lý dữ liệu từ nhiều nguồn.
  2. Thực thi độc lập và song song 4 mô hình định giá.
  3. Kết hợp bằng Ensemble có trọng số tối ưu hóa sai số MAE.
  4. Xuất bản giá trị định giá lên Smart Contract trên Ethereum Sepolia testnet.
  5. Cung cấp Dashboard Streamlit trực quan để người dùng theo dõi và kiểm tra.
- **Sơ đồ kiến trúc tổng thể:** Luồng dữ liệu chạy nối tiếp từ Data Ingestion -> Preprocessing -> Models Execution -> Weight Optimization (Ensemble) -> Smart Contract Publisher -> Dashboard.

## 4.2 Thiết kế các mô hình định giá và Mô hình kết hợp Ensemble (3 trang)
Mỗi mô hình được trình bày chuẩn hóa theo cấu trúc 4 phần:
1. **Mô hình NVT Ratio & Metcalfe:** Công thức, giả định dữ liệu on-chain phản ánh trung thực mức sử dụng mạng, dữ liệu đầu vào và ví dụ số cho token UNI.
2. **Mô hình Phương trình trao đổi MV = PQ:** Công thức, giả định vận tốc tiền tệ V ổn định trong ngắn hạn, dữ liệu đầu vào và ví dụ số cho token LINK.
3. **Mô hình Uniswap AMM TWAP:** Công thức cửa sổ tích lũy thời gian, giả định pool có thanh khoản đủ sâu, ví dụ số cho token CRV.
4. **Mô hình So sánh Tương đối (Comparable MC/TVL):** Công thức trung vị ngành, ví dụ số cho token AAVE so với nhóm Lending.
- **Cơ chế Ensemble và Tối ưu hóa Trọng số:**
  $$P_{ensemble} = w_1 P_{NVT} + w_2 P_{MVPQ} + w_3 P_{TWAP} + w_4 P_{Comp}, \quad \sum w_i = 1, \, w_i \ge 0$$
  Hàm mục tiêu tối thiểu hóa sai số tuyệt đối trung bình (MAE) trên tập huấn luyện:
  $$\min_{\{w_i\}} \frac{1}{N} \sum_{t=1}^N \left| P_{ensemble, t} - P_{market, t} \right|$$
  Sử dụng giải thuật Sequential Least Squares Programming (SLSQP) từ thư viện `scipy.optimize`.
- **Bảng ma trận:** Mức độ phù hợp của từng mô hình đối với từng phân nhóm token (DEX, Lending, Infrastructure, L2).

## 4.3 Cài đặt bằng Python và Smart Contract (2 trang)
- Cấu trúc giao diện kế thừa `ValuationModel` trong `src/models/base.py`.
- Chi tiết mã nguồn `src/models/nvt.py`, `src/models/ensemble.py`, `src/chain/publisher.py`.
- **Smart Contract `TokenValuation.sol`:**
  - Giải thích hàm `setValuation`, `getValuation`, cơ chế phân quyền Oracle modifier `onlyOracle`.
  - Cơ chế lưu trữ giá theo định dạng 8 chữ số thập phân tương thích chuẩn Chainlink Price Feeds.
  - Địa chỉ triển khai trên Sepolia: `0x71C2E63B484e557297e68A7836376cFE94f06B0F`.
  - Hash giao dịch ghi nhận định giá mẫu trên Sepolia: `0x4a7e3d8c9b2f1a6e5d0c8b7a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e`.
