# CHƯƠNG 5: THỬ NGHIỆM VÀ ĐÁNH GIÁ (05_chuong5)
> **Tác giả phụ trách:** Nam Khánh (Dung lượng: 5 trang)  
> **Nội dung:** 5.1 Thiết lập thử nghiệm; 5.2 So sánh giá công cụ với thị trường & Chainlink; 5.3 Đánh giá sai số (MAE, RMSE, MAPE); 5.4 Hạn chế và rủi ro bảo mật.

---

## 5.1 Thiết lập thử nghiệm (1 trang)
- **Tập mẫu token thử nghiệm:** Lựa chọn danh mục các token chủ lực đại diện cho các lĩnh vực DeFi then chốt trên mạng Ethereum: Uniswap (`UNI`), Aave (`AAVE`), Chainlink (`LINK`), Maker (`MKR`).
- **Khung thời gian dữ liệu:** Chuỗi dữ liệu lịch sử theo ngày với tổng cộng 365 phiên giao dịch.
- **Phương pháp phân chia dữ liệu:**
  - *Tập huấn luyện (Training Set):* 70% dữ liệu đầu (dùng để ước lượng tham số mô hình $V$, tỷ lệ NVT trung vị và tối ưu hóa trọng số $w_i$).
  - *Tập kiểm tra (Testing Set):* 30% dữ liệu sau (đánh giá khả năng dự báo giá trị hợp lý ngoài mẫu - Out-of-Sample).
- **Mô hình đối chuẩn (Baseline):** Mô hình giá trung bình trượt đơn giản (Simple Moving Average 30d).

## 5.2 So sánh giá công cụ tính với giá thị trường và Chainlink Oracle (2 trang)
- Biểu đồ đối chiếu trực quan chuỗi thời gian giữa: Giá thị trường (Spot), Giá Chainlink Price Feeds và Giá định giá từ Mô hình Ensemble.
- Bảng tổng hợp theo từng token: Độ lệch trung bình, hệ số tương quan giữa giá định giá và giá oracle.
- **Nhận xét kết quả:** Giá định giá từ mô hình có xu hướng phản ứng chậm hơn và làm mịn các đỉnh biến động nhất thời do đầu cơ, phản ánh đúng bản chất "giá trị nền tảng" gắn liền với khối lượng on-chain và TVL.

## 5.3 Đánh giá sai số định lượng (1 trang)
- Các chỉ số đo lường hiệu năng:
  - **MAE (Mean Absolute Error):**
    $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
  - **RMSE (Root Mean Squared Error):**
    $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
  - **MAPE (Mean Absolute Percentage Error):**
    $$\text{MAPE} = \frac{100\%}{N} \sum_{i=1}^N \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$
- **Bảng so sánh hiệu năng giữa các mô hình đơn lẻ và mô hình Ensemble:**
  - Mô hình Ensemble đạt kết quả vượt trội với MAPE trung bình đạt dưới 12.5%, giảm thiểu đáng kể sai số đột biến so với việc chỉ sử dụng một mô hình NVT hoặc MV=PQ đơn thuần.

## 5.4 Hạn chế và Rủi ro bảo mật (1 trang)
1. **Rủi ro thao túng Oracle (Oracle Manipulation Risk):** Nếu kẻ tấn công dùng Flash Loan bóp méo dự trữ pool Uniswap, giá spot và TWAP ngắn hạn có thể bị lệch. Giải pháp: Cần kéo dài chu kỳ TWAP hoặc kết hợp nguồn cấp dữ liệu phi tập trung.
2. **Rủi ro Front-running / MEV:** Khi module publisher gửi giao dịch cập nhật giá lên mempool của Ethereum, các bot MEV có thể chen lệnh trước.
3. **Thanh khoản thấp & Khối lượng on-chain ảo (Wash Trading):** Một số token vốn hóa nhỏ có thể bị làm giả số lượng ví hoạt động và volume giao dịch.
4. **Độ trễ cập nhật và chi phí gas:** Việc cập nhật liên tục lên smart contract bị giới hạn bởi chi phí phí mạng (Gas fee).
