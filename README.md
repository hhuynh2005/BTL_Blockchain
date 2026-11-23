# BTL_Blockchain: Công cụ Định giá Token Dựa trên Dữ liệu Thị trường & On-chain

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ethereum Sepolia](https://img.shields.io/badge/Network-Sepolia%20Testnet-blueviolet)](https://sepolia.etherscan.io/)
[![Framework](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B)](https://streamlit.io/)

> **Môn học:** Chuỗi khối và công nghệ sổ cái phân tán  
> **Đề tài R:** Xây dựng công cụ định giá token dựa trên dữ liệu thị trường (off-chain và on-chain), ghi kết quả định giá lên smart contract.  
> **Thời gian cập nhật:** 23/11/2026  

---

## 👥 Danh sách Nhóm & Phân công Công việc

| Thành viên | Trách nhiệm Báo cáo (36 trang) | Module Code & Trách nhiệm Kỹ thuật | Nhánh Git |
|---|---|---|---|
| **Huỳnh** *(Trưởng nhóm)* | **Chương 1** (3 tr), **Mục 4.1 - 4.3** (6 tr) | Khung repo, `base.py`, `nvt.py`, `ensemble.py`, `publisher.py`, review PR | `feature/models` |
| **Khanh** | **Chương 2** - Cơ sở lý thuyết (9 tr), **Tài liệu tham khảo** | `mv_pq.py`, `coingecko.py`, `defillama.py`, `preprocessing/`, `01_eda.ipynb` | `feature/preprocess` |
| **Kha** | **Chương 3** - Dữ liệu thị trường (9 tr), **Phụ lục Contract** | `tokens.yaml`, `SCHEMA.md`, `uniswap.py`, `onchain.py`, `twap.py`, `TokenValuation.sol`, `tests/` | `feature/data`, `feature/contract` |
| **Nam Khánh** | **Mục 4.4** (2 tr), **Chương 5** (5 tr), **Chương 6** (2 tr) | `comparable.py`, `evaluation/` (backtest, metrics), `dashboard.py`, `02_experiments.ipynb` | `feature/eval-ui` |

---

## 🏛️ Kiến trúc Hệ thống

```
  [OFF-CHAIN DATA]                 [ON-CHAIN DATA]
CoinGecko / DefiLlama          Ethereum RPC / Uniswap Pool
         │                                  │
         ▼                                  ▼
 ┌──────────────────────────────────────────────────┐
 │       src/collectors/ & src/preprocessing/       │
 │   - Làm sạch, lọc ngoại lai, đồng bộ mốc UTC     │
 │   - Tính toán Volatility, Moving Averages, TVL   │
 └─────────────────────────┬────────────────────────┘
                           │
                           ▼
 ┌──────────────────────────────────────────────────┐
 │                  src/models/                     │
 │   - NVT & Metcalfe Model (nvt.py)                │
 │   - Equation of Exchange (mv_pq.py)              │
 │   - Uniswap AMM TWAP (twap.py)                   │
 │   - Comparable Analysis MC/TVL (comparable.py)   │
 └─────────────────────────┬────────────────────────┘
                           │
                           ▼
 ┌──────────────────────────────────────────────────┐
 │             src/models/ensemble.py               │
 │   - Tối ưu hóa trọng số tối thiểu hóa sai số MAE │
 │   - Kết hợp các mức giá thành Fair Value         │
 └─────────────┬──────────────────────────┬─────────┘
               │                          │
               ▼                          ▼
  ┌─────────────────────────┐  ┌──────────────────────────┐
  │   src/chain/publisher   │  │       app/dashboard      │
  │   Ghi giá trị lên Smart │  │   Giao diện Streamlit    │
  │   Contract Sepolia      │  │   Phân tích trực quan    │
  └─────────────────────────┘  └──────────────────────────┘
```

---

## 📂 Cấu trúc Thư mục Dự án

```text
BTL_Blockchain/
├── .env.example               # Mẫu biến môi trường (RPC_URL, PRIVATE_KEY, CONTRACT)
├── .gitignore                 # Cấu hình bỏ qua file nhạy cảm và build cache
├── requirements.txt           # Danh mục thư viện Python
├── hardhat.config.js          # Cấu hình Hardhat cho Smart Contract
├── README.md                  # Hướng dẫn tổng quan dự án
├── config/
│   ├── tokens.yaml            # Danh mục 12 token và địa chỉ contract, pool
│   └── weights.yaml           # Trọng số ensemble mặc định và theo ngành
├── data/
│   ├── SCHEMA.md              # Đặc tả chuẩn 14 trường dữ liệu thị trường
│   ├── raw/                   # Dữ liệu thô thu thập từ API / RPC
│   └── processed/             # Dữ liệu đã qua làm sạch và đồng bộ
├── src/
│   ├── collectors/            # coingecko.py, defillama.py, uniswap.py, onchain.py
│   ├── preprocessing/         # clean.py, features.py
│   ├── models/                # base.py, nvt.py, mv_pq.py, twap.py, comparable.py, ensemble.py
│   ├── chain/                 # publisher.py (tương tác Web3 Sepolia)
│   └── evaluation/            # metrics.py (MAE, RMSE, MAPE), backtest.py, compare_chainlink.py
├── contracts/
│   ├── TokenValuation.sol     # Smart contract lưu trữ định giá trên Ethereum
│   ├── scripts/deploy.js      # Script deploy lên Sepolia
│   └── test/TokenValuation.test.js # Test suite kiểm thử hợp đồng
├── app/
│   └── dashboard.py           # Dashboard ứng dụng phân tích định giá Streamlit
├── notebooks/
│   ├── 01_eda.ipynb           # Phân tích khám phá dữ liệu (Khanh)
│   └── 02_experiments.ipynb   # Thử nghiệm và đánh giá sai số (Nam Khánh)
├── tests/
│   ├── test_models.py         # Kiểm thử các thuật toán định giá
│   └── test_collectors.py     # Kiểm thử các nguồn lấy dữ liệu
└── reports/
    ├── figures/               # Biểu đồ phục vụ báo cáo
    ├── tables/                # Bảng biểu tổng hợp kết quả
    └── docs/                  # Khung các chương báo cáo chi tiết
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Chuẩn bị môi trường Python & Thư viện
```bash
# Clone repository
git clone https://github.com/hhuynh2005/BTL_Blockchain.git
cd BTL_Blockchain

# Tạo và kích hoạt môi trường ảo (khuyến nghị)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt
```

### 2. Cấu hình Biến Môi trường
Sao chép `.env.example` thành `.env` và điền khóa RPC / Private key thử nghiệm:
```bash
cp .env.example .env
```

### 3. Chạy Kiểm thử Đơn vị (Unit Tests)
```bash
python -m pytest tests/ -v
```

### 4. Khởi chạy Giao diện Dashboard (Streamlit)
```bash
streamlit run app/dashboard.py
```
Mở trình duyệt tại địa chỉ: `http://localhost:8501` để xem giao diện định giá trực quan.

### 5. Smart Contract trên Sepolia
- **Contract Code:** `contracts/TokenValuation.sol`
- **Địa chỉ Sepolia:** `0x71C2E63B484e557297e68A7836376cFE94f06B0F`
- **Chức năng chính:**
  - `setValuation(address token, uint256 value)`: Cập nhật định giá (chỉ Oracle được cấp quyền).
  - `getValuation(address token)`: Truy vấn giá trị hợp lý và mốc thời gian cập nhật.
  - `isValuationStale(address token, uint256 maxAgeSec)`: Kiểm tra độ trễ dữ liệu.

---

## 📌 Quy ước Git & Phối hợp Nhóm
1. Mỗi thành viên làm việc trên nhánh tính năng riêng: `feature/models`, `feature/preprocess`, `feature/data`, `feature/contract`, `feature/eval-ui`.
2. Tạo **Pull Request (PR)** vào nhánh `main` để Huỳnh review và gộp mã nguồn.
3. Tuyệt đối **không commit file `.env`** hoặc chứa Private Key cá nhân lên GitHub.
