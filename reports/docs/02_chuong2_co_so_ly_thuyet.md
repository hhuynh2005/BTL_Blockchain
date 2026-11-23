# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT (02_chuong2)
> **Tác giả phụ trách:** Khanh (Dung lượng: 9 trang)  
> **Nội dung:** 2.1 Blockchain & Tokenomics; 2.2 Các yếu tố ảnh hưởng giá; 2.3 Phương trình MV=PQ; 2.4 NVT & Metcalfe; 2.5 Định giá dòng tiền; 2.6 So sánh MC/TVL; 2.7 AMM & TWAP; 2.8 Oracle & Rủi ro bảo mật.

---

## 2.1 Blockchain, Token và Tokenomics (1.5 trang)
- Công nghệ sổ cái phân tán (DLT), cơ chế đồng thuận PoS trên Ethereum.
- Chuẩn giao tiếp hợp đồng thông minh ERC-20: cơ chế chuyển nhượng, số dư (`balanceOf`, `transfer`).
- Cấu trúc kinh tế học token (Tokenomics): Cung lưu hành (Circulating Supply) so với Tổng cung tối đa (Max Supply / Total Supply), lịch mở khóa token (vesting schedule), cơ chế phát hành (mint) và cơ chế tiêu hủy (burn - EIP-1559).

## 2.2 Các yếu tố ảnh hưởng đến giá token (1 trang)
- Quy luật cung cầu thị trường và độ sâu thanh khoản.
- Tiện ích nội tại (Utility): dùng trả phí giao dịch (gas), thế chấp vay mượn, bỏ phiếu quản trị DAO.
- Tâm lý thị trường (Market Sentiment) và hiệu ứng mạng lưới.

## 2.3 Phương trình trao đổi MV = PQ áp dụng cho Token (1 trang)
- Công thức cổ điển từ Kinh tế học tiền tệ của Irving Fisher:
  $$M \times V = P \times Q$$
  Trong đó:
  - $M$: Giá trị quy đổi của lượng token lưu hành (Vốn hóa $M = P_{fair} \times S$).
  - $V$: Tốc độ lưu thông / luân chuyển của token trong nền kinh tế.
  - $P \times Q$: Tổng giá trị giao dịch kinh tế thực tế được xử lý trong kỳ (USD).
- Vận tốc lưu thông $V$ được ước lượng bằng tỷ số giữa khối lượng giao dịch quy năm và vốn hóa:
  $$V = \frac{\text{Volume}_{24h} \times 365}{\text{Market Cap}}$$
- Giá trị hợp lý suy diễn:
  $$P_{fair} = \frac{P \times Q}{V \times S}$$
- **Ví dụ số minh họa:** Một token có $PQ = 500$ triệu USD/năm, $V = 8.0$, cung lưu hành $S = 50$ triệu token. Khi đó $M = 500 / 8 = 62.5$ triệu USD, giá hợp lý $P_{fair} = 62.5 / 50 = 1.25$ USD.

## 2.4 Chỉ số NVT và Luật Metcalfe (1.5 trang)
- **Tỷ lệ NVT (Network Value to Transactions):** Tương đương chỉ số P/E trong thị trường chứng khoán truyền thống:
  $$\text{NVT} = \frac{\text{Market Cap}}{\text{Daily On-Chain Transaction Volume}}$$
- Mức NVT chuẩn (Benchmark) tính bằng trung vị động 90 ngày. Giá trị hợp lý:
  $$P_{NVT} = \frac{\text{NVT}_{median\_90d} \times \text{Daily On-Chain Volume}}{\text{Circulating Supply}}$$
- **Luật Metcalfe áp dụng cho mạng blockchain:** Giá trị mạng lưới tỷ lệ thuận với bình phương số người dùng hoạt động:
  $$V_{network} \propto n^2 \quad \Rightarrow \quad P_{Metcalfe} = \alpha \times \frac{\text{ActiveAddresses}^2}{\text{Circulating Supply}}$$

## 2.5 Định giá theo dòng thu nhập (1 trang)
- Chiết khấu dòng tiền (Discounted Cash Flow - DCF) cho các giao thức DeFi có chia sẻ doanh thu phí giao thức (Protocol Fees) và lợi tức Staking Yield.

## 2.6 Định giá so sánh tương đối với đối thủ (Comparable Analysis) (1 trang)
- Chỉ số Bội số Vốn hóa trên Tổng giá trị khóa (MC/TVL Multiple).
- Lựa chọn nhóm token cùng lĩnh vực kinh doanh (DEX, Lending, L2) và sử dụng giá trị trung vị (Median Multiple) để tránh độ lệch từ các trường hợp dị biệt:
  $$P_{Comparable} = \frac{\text{Median}\left(\frac{\text{MarketCap}_{peer}}{\text{TVL}_{peer}}\right) \times \text{TVL}_{target}}{\text{CirculatingSupply}_{target}}$$

## 2.7 Thanh khoản, độ sâu thị trường và AMM (1 trang)
- Mô hình Tạo lập thị trường tự động Uniswap Constant Product:
  $$x \times y = k$$
- Tác động giá (Price Impact), Trượt giá (Slippage) khi giao dịch khối lượng lớn.
- **Giá trung bình theo trọng số thời gian (TWAP - Time-Weighted Average Price):** Cơ chế tích lũy tích lũy giá theo thời gian để miễn nhiễm với các biến động tức thời do tấn công rút vốn.

## 2.8 Công cụ hiện hữu và Rủi ro Oracle (1 trang)
- Khảo sát các nền tảng: CoinGecko, DefiLlama, Chainlink Decentralized Oracle Networks.
- Rủi ro thao túng giá spot (Spot Price Manipulation) thông qua vay nhanh không thế chấp (Flash Loan Attacks). Tầm quan trọng của việc cập nhật định giá an toàn lên Smart Contract.
