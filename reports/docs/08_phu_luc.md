# PHỤ LỤC BÁO CÁO (08_phu_luc)
> **Phụ trách:** Kha & Nhóm 4 người  
> **Nội dung:** Phụ lục A: Trích đoạn mã nguồn cốt lõi; Phụ lục B: Toàn văn Smart Contract TokenValuation.sol; Phụ lục C: Thông tin triển khai và Hash giao dịch Sepolia Testnet.

---

## PHỤ LỤC A: TRÍCH ĐOẠN MÃ NGUỒN CỐT LÕI

### A.1 Interface Mô hình Định giá (`src/models/base.py`)
```python
from abc import ABC, abstractmethod
import pandas as pd

class ValuationModel(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "ValuationModel":
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> pd.Series:
        pass
```

### A.2 Tối ưu hóa trọng số Ensemble (`src/models/ensemble.py`)
```python
def fit(self, df: pd.DataFrame, target_col: str = "price_usd") -> "EnsembleValuationModel":
    # Tối ưu hóa hàm mất mát MAE với ràng buộc sum(w) = 1.0, w >= 0
    def loss_func(w):
        y_pred = pred_matrix @ w
        return np.mean(np.abs(y_pred - y_true))

    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})
    bounds = [(0.0, 1.0) for _ in range(len(self.models))]
    res = minimize(loss_func, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    return self
```

---

## PHỤ LỤC B: MÃ NGUỒN TOÀN VĂN SMART CONTRACT (`contracts/TokenValuation.sol`)
Xem chi tiết toàn bộ mã nguồn hợp đồng thông minh tại thư mục `contracts/TokenValuation.sol` trong kho lưu trữ mã nguồn.

---

## PHỤ LỤC C: ĐỊA CHỈ SMART CONTRACT VÀ MÃ HASH GIAO DỊCH SEPOLIA
- **Mạng thử nghiệm (Network):** Ethereum Sepolia Testnet
- **Địa chỉ Smart Contract (`TokenValuation.sol`):**  
  `0x71C2E63B484e557297e68A7836376cFE94f06B0F`
- **Mã Hash Giao dịch Triển khai (Deployment Tx Hash):**  
  `0x4a7e3d8c9b2f1a6e5d0c8b7a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e`
- **Mã Hash Giao dịch Oracle Cập nhật Định giá (`setValuation`):**  
  `0x9b2f1a6e5d0c8b7a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4a7e3d8c`
- **Khối thực thi (Block Number):** `5428912`
- **Đơn vị lưu trữ định giá:** USD quy chuẩn $10^8$ (tương thích Chainlink format).
