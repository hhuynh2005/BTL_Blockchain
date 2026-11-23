# CHUẨN ĐẶC TẢ DỮ LIỆU THỊ TRƯỜNG VÀ ON-CHAIN (SCHEMA.MD)
> **Tác giả phụ trách:** Kha (Nhóm Đề tài R - BTL Chuỗi khối)  
> **Cập nhật:** 23/11/2026  
> **Áp dụng:** Toàn bộ luồng thu thập dữ liệu (Collectors), Tiền xử lý (Preprocessing), Mô hình định giá (Models) và Đánh giá (Evaluation).

---

## 1. Mục đích và Quy ước chung
Tài liệu này xác định cấu trúc dữ liệu chuẩn (Unified Schema) đồng nhất cho dữ liệu chuỗi thời gian (time-series) của từng token. Mỗi dòng trong tệp dữ liệu đã qua tiền xử lý đại diện cho dữ liệu của một token tại một ngày giao dịch theo múi giờ chuẩn **UTC**.

- **Định dạng lưu trữ:** CSV (RFC 4180) và Parquet cho dữ liệu lớn.
- **Múi giờ chuẩn:** Coordinated Universal Time (UTC) 00:00:00.
- **Đơn vị tiền tệ chuẩn:** Đô la Mỹ (USD).
- **Quy đổi số thập phân On-Chain:** Toàn bộ số lượng token on-chain (wei) phải được chia cho $10^{\text{decimals}}$ (thông thường là $10^{18}$) trước khi đưa vào schema.

---

## 2. Bảng Schema chuẩn (14 trường dữ liệu)

| STT | Tên trường (Field) | Kiểu dữ liệu | Nguồn gốc | Đơn vị | Mô tả chi tiết & Công thức |
|---|---|---|---|---|---|
| 1 | `date` | `YYYY-MM-DD` | Hệ thống | Date | Ngày ghi nhận dữ liệu (UTC) |
| 2 | `token` | `string` | Config | Ticker | Ký hiệu mã token (VD: `UNI`, `AAVE`, `LINK`) |
| 3 | `price_usd` | `float64` | CoinGecko / Binance | USD | Giá đóng cửa thực tế thị trường (Spot Price) |
| 4 | `volume_24h` | `float64` | CoinGecko / DEX | USD | Tổng khối lượng giao dịch trong 24 giờ |
| 5 | `market_cap` | `float64` | CoinGecko / On-chain | USD | Vốn hóa thị trường = $price\_usd \times circulating\_supply$ |
| 6 | `circulating_supply` | `float64` | Etherscan / CoinGecko | Token | Lượng token thực tế đang lưu hành tự do |
| 7 | `tvl` | `float64` | DefiLlama | USD | Tổng giá trị tài sản khóa trong giao thức (Total Value Locked) |
| 8 | `tx_count` | `int64` | Etherscan / RPC | Tx | Tổng số giao dịch chuyển token on-chain trong 24h |
| 9 | `active_addresses` | `int64` | Etherscan / RPC | Addr | Số địa chỉ ví duy nhất phát sinh giao dịch trong ngày |
| 10 | `onchain_volume_usd` | `float64` | RPC / Etherscan | USD | Giá trị giao dịch chuyển token trên chuỗi khối tính bằng USD |
| 11 | `pool_reserve0` | `float64` | Uniswap V2/V3 Pair | Token | Lượng dự trữ token mục tiêu trong liquidity pool chính |
| 12 | `pool_reserve1` | `float64` | Uniswap V2/V3 Pair | ETH/USD | Lượng dự trữ tài sản đối ứng (WETH hoặc USDC) trong pool |
| 13 | `velocity` | `float64` | Tính toán | Ratio | Tốc độ vòng quay của token $V = \frac{\text{On-chain Volume}}{\text{Market Cap}}$ |
| 14 | `nvt_ratio` | `float64` | Tính toán | Ratio | Chỉ số NVT Ratio = $\frac{\text{Market Cap}}{\text{On-chain Volume}}$ |

---

## 3. Các quy tắc kiểm tra tính hợp lệ (Validation Rules)

1. **Tính đơn điệu và liên tục của thời gian:**  
   Không được có khoảng trống ngày (missing days). Nếu ngày lễ hoặc mất kết nối API, sử dụng thuật toán nội suy `forward-fill` (tối đa 3 ngày liên tiếp).
2. **Giá trị không âm:**  
   $price\_usd > 0$, $volume\_24h \ge 0$, $circulating\_supply > 0$, $pool\_reserve0 > 0$, $pool\_reserve1 > 0$.
3. **Giới hạn tỷ lệ dự trữ AMM:**  
   Tỷ giá ngầm định từ AMM $P_{AMM} = \frac{pool\_reserve1}{pool\_reserve0}$ không được lệch quá $\pm 25\%$ so với $price\_usd$ (nếu vượt quá, đánh dấu có trượt giá mạnh hoặc biến cố thanh khoản).
4. **Xử lý giá trị ngoại lai (Outliers):**  
   Các phiên có đột biến volume gấp 10 lần trung bình 30 ngày cần được đánh cờ `is_anomaly = True` để mô hình NVT cân nhắc làm mịn bằng Moving Median.
