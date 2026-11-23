# CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (06_chuong6)
> **Tác giả phụ trách:** Nam Khánh (Dung lượng: 2 trang)  
> **Nội dung:** Tóm tắt kết quả; Đóng góp của nhóm; Hạn chế tồn tại; Hướng mở rộng nghiên cứu.

---

## 6.1 Tóm tắt kết quả đạt được
Qua quá trình nghiên cứu, thiết kế và triển khai đề tài "Xây dựng công cụ định giá token dựa trên dữ liệu thị trường và on-chain, ghi kết quả định giá lên smart contract", nhóm đã hoàn thành toàn diện các mục tiêu đề ra:
1. **Hoàn thiện chuỗi thu thập và xử lý dữ liệu tự động:** Tích hợp thành công các nguồn dữ liệu off-chain (CoinGecko, DefiLlama) và on-chain (Ethereum RPC, Uniswap Pair reserves, Etherscan).
2. **Cài đặt thành công hệ thống mô hình định giá định lượng:** Triển khai độc lập 4 mô hình: NVT Ratio & Metcalfe, Phương trình trao đổi MV=PQ, Uniswap AMM TWAP, So sánh MC/TVL tương đối.
3. **Mô hình kết hợp Ensemble tối ưu:** Tối ưu hóa trọng số thích ứng theo từng token và nhóm ngành thông qua hàm tối thiểu hóa sai số MAE.
4. **Triển khai Smart Contract trên Ethereum Sepolia Testnet:** Hợp đồng `TokenValuation.sol` đã được biên dịch, kiểm thử đơn vị tự động và deploy thành công lên testnet Sepolia; module `publisher.py` có khả năng đẩy và kiểm tra dữ liệu định giá on-chain.
5. **Giao diện người dùng Dashboard Streamlit:** Cung cấp trải nghiệm tương tác trực quan, hỗ trợ phân tích định giá và kiểm tra trạng thái blockchain.

## 6.2 Đóng góp của nhóm
- Xây dựng một khung kiến trúc phần mềm chuẩn mực (modular architecture) cho bài toán định giá tài sản số kết hợp giữa Khoa học dữ liệu (Data Science) và Công nghệ chuỗi khối (Blockchain Engineering).
- Đưa ra giải pháp định giá kết hợp (Ensemble) giải quyết nhược điểm đơn lẻ của từng phương pháp truyền thống.
- Cung cấp cơ chế phân phối kết quả định giá lên smart contract với chuẩn 8 số thập phân, mở ra tiềm năng tích hợp cho các ứng dụng DeFi phái sinh, cho vay phi tập trung hoặc quản lý danh mục tự động.

## 6.3 Hạn chế và Hướng mở rộng
- **Hạn chế:** Dữ liệu on-chain hiện tại phụ thuộc một phần vào API trung gian; chưa tích hợp xử lý độ lệch do các cuộc tấn công trượt giá trong thời gian thực cực ngắn; chi phí gas trên mạng chính thức có thể là rào cản nếu tần suất cập nhật quá dày.
- **Hướng phát triển:**
  - Mở rộng sang các mạng Layer 2 (Arbitrum, Optimism, Base) để giảm thiểu chi phí gas cập nhật oracle.
  - Tích hợp thêm các mô hình Machine Learning / Deep Learning (LSTM, Transformer) để phân tích chuỗi thời gian kết hợp yếu tố tâm lý mạng xã hội (Sentiment Analysis từ Twitter/Reddit).
  - Tích hợp cơ chế Chainlink Functions hoặc Chainlink Automation để kích hoạt việc cập nhật dữ liệu định giá định kỳ hoàn toàn tự động on-chain.
