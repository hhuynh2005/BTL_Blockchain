# CHƯƠNG 3: DỮ LIỆU THỊ TRƯỜNG VÀ ON-CHAIN (03_chuong3)
> **Tác giả phụ trách:** Kha (Dung lượng: 9 trang)  
> **Nội dung:** 3.1 Nguồn dữ liệu; 3.2 Các chỉ số thu thập & Schema; 3.3 Trích đoạn Code Python; 3.4 Tiền xử lý; 3.5 Phân tích khám phá dữ liệu (EDA).

---

## 3.1 Nguồn dữ liệu (2 trang)
- **Nguồn dữ liệu Off-Chain:**
  - *CoinGecko Public API:* Thu thập lịch sử giá đóng cửa, vốn hóa thị trường, khối lượng giao dịch 24 giờ.
  - *DefiLlama Open API:* Thu thập Total Value Locked (TVL) theo ngày cho các giao thức DeFi.
- **Nguồn dữ liệu On-Chain:**
  - *Ethereum RPC Node / Web3.py:* Kết nối qua RPC để đọc trạng thái pool dự trữ Uniswap V2/V3 Pair (`getReserves()`).
  - *Etherscan API:* Lấy số lượng giao dịch chuyển token, lượng cung lưu hành, số địa chỉ ví hoạt động hàng ngày (Active Addresses).

## 3.2 Các chỉ số thu thập và Bảng Schema chuẩn (2 trang)
- Bảng đặc tả 14 trường dữ liệu chuẩn hóa thống nhất theo `data/SCHEMA.md`:
  - `date`, `token`, `price_usd`, `volume_24h`, `market_cap`, `circulating_supply`, `tvl`, `tx_count`, `active_addresses`, `onchain_volume_usd`, `pool_reserve0`, `pool_reserve1`, `velocity`, `nvt_ratio`.

## 3.3 Cài đặt Module thu thập dữ liệu bằng Python (2 trang)
- Trích đoạn cấu trúc code `src/collectors/coingecko.py`, `uniswap.py`, `onchain.py`.
- Cơ chế Cache dữ liệu dạng CSV để hạn chế gửi request trùng lặp và vượt ngưỡng Rate Limit API.
- Cơ chế thử lại (exponential backoff retry) khi gặp lỗi mạng hoặc HTTP status 429.

## 3.4 Tiền xử lý dữ liệu (2 trang)
- **Xử lý giá trị thiếu (Missing Values):** Sử dụng kỹ thuật Forward-fill (kế thừa giá trị gần nhất) cho dữ liệu TVL và Active Addresses khi có sự gián đoạn mạng.
- **Lọc ngoại lai (Outlier Detection):** Ứng dụng quy tắc khoảng tứ phân vị (IQR) để khử nhiễu từ các đột biến volume ảo hoặc sự kiện trượt giá đột ngột.
- **Đồng bộ thời gian:** Quy chuẩn toàn bộ mốc thời gian từ timestamp mili-giây và giây về chuẩn ngày `YYYY-MM-DD` theo múi giờ UTC 00:00:00.
- **Chuẩn hóa đơn vị:** Chuyển đổi lượng token on-chain từ đơn vị wei ($10^{18}$) về giá trị thực tế theo chuẩn cấu hình `decimals`.

## 3.5 Phân tích Khám phá Dữ liệu (EDA) (1 trang)
- Phân phối thống kê mô tả (Mean, Median, Standard Deviation, Skewness) của giá và khối lượng.
- Ma trận tương quan Pearson giữa các biến số on-chain (Active Addresses, Tx Count) và Market Cap.
- Các biểu đồ trực quan hóa được xuất từ Notebook `notebooks/01_eda.ipynb` đưa vào `reports/figures/fig_3_1.png` và `fig_3_2.png`.
