# CHƯƠNG 1: MỞ ĐẦU (01_chuong1)
> **Tác giả phụ trách:** Huỳnh (Dung lượng: 3 trang)  
> **Nội dung:** 1.1 Lý do chọn đề tài (1 tr); 1.2 Mục tiêu và phạm vi (1 tr); 1.3 Phương pháp và bố cục (1 tr).

---

## 1.1 Lý do chọn đề tài
Trong kỷ nguyên phát triển mạnh mẽ của công nghệ sổ cái phân tán (Distributed Ledger Technology - DLT) và tài chính phi tập trung (DeFi), token không chỉ đơn thuần là phương tiện trao đổi giá trị mà còn là đại diện cho quyền quản trị, tiện ích sử dụng hoặc cổ phần kinh tế của các giao thức blockchain. Tuy nhiên, thị trường tiền mã hóa vốn nổi tiếng với mức độ biến động cực kỳ gay gắt, dễ chịu ảnh hưởng bởi tâm lý đầu cơ bầy đàn và thông tin bất cân xứng. Nhiều token bị thổi phồng giá trị (overvalued) gấp nhiều lần giá trị thực chất hoặc bị định giá thấp (undervalued) do thiếu thanh khoản.

Các nền tảng theo dõi dữ liệu phổ biến hiện nay như CoinGecko, CoinMarketCap chủ yếu cung cấp giá spot tức thời và vốn hóa thị trường nhưng không cung cấp thước đo định giá hợp lý (fair value) gắn với hoạt động thực tế trên chuỗi khối (on-chain activity). Hơn nữa, các nguồn dữ liệu tập trung dễ có nguy cơ thao túng hoặc sai lệch. Do đó, nhu cầu cấp thiết là xây dựng một công cụ định giá token minh bạch, kết hợp dữ liệu thị trường off-chain và dữ liệu giao dịch on-chain, đồng thời **ghi nhận kết quả định giá trực tiếp lên smart contract** trên chuỗi khối để các ứng dụng phi tập trung khác có thể khai thác một cách bảo mật và tin cậy.

## 1.2 Mục tiêu và phạm vi đề tài
- **Mục tiêu:** Xây dựng hệ thống công cụ tự động hóa toàn diện nhằm thu thập dữ liệu thị trường và on-chain, áp dụng phối hợp nhiều mô hình định giá định lượng (NVT, Metcalfe, Phương trình trao đổi MV=PQ, Uniswap TWAP, So sánh MC/TVL tương đối), kết hợp bằng mô hình Ensemble tối thiểu hóa sai số và xuất bản kết quả định giá lên smart contract Sepolia.
- **Phạm vi nghiên cứu:** Đề tài tập trung vào 10 đến 20 token ERC-20 tiêu biểu trên mạng Ethereum (bao gồm các nhóm DEX, Lending, Infrastructure, Liquid Staking như UNI, AAVE, LINK, MKR, CRV, LDO,...).
- **Yêu cầu cốt lõi:** *Công cụ dùng dữ liệu off-chain, on-chain và ghi kết quả lên smart contract.*

## 1.3 Phương pháp thực hiện và bố cục báo cáo
Nhóm tiến hành theo quy trình kỹ thuật 5 giai đoạn:
1. **Thu thập dữ liệu:** Khai thác API CoinGecko, DefiLlama kết hợp Web3.py/RPC truy vấn dữ liệu on-chain và pool Uniswap.
2. **Tiền xử lý dữ liệu:** Làm sạch, khử trùng lặp, lọc ngoại lai IQR, đồng bộ thời gian UTC.
3. **Mô hình hóa định giá:** Triển khai độc lập 4 mô hình định giá chuyên biệt cho tài sản số.
4. **Mô hình kết hợp (Ensemble):** Tối ưu hóa trọng số dựa trên hàm mất mát MAE.
5. **Thực thi Smart Contract & Trực quan hóa:** Viết và kiểm thử `TokenValuation.sol`, phát triển module `publisher.py` đẩy dữ liệu lên Sepolia và xây dựng Dashboard Streamlit.

Báo cáo gồm 6 chương: Chương 1 Mở đầu; Chương 2 Cơ sở lý thuyết; Chương 3 Dữ liệu thị trường; Chương 4 Thiết kế và xây dựng công cụ; Chương 5 Thử nghiệm và đánh giá; Chương 6 Kết luận và hướng phát triển.
