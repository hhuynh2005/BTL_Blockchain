# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT
> **Phụ trách:** Khanh (nhánh `feature/preprocess`) · **Dung lượng mục tiêu:** 9 trang  
> **Bố cục theo khung nhóm:** 2.1 Blockchain, token và tokenomics · 2.2 Các yếu tố ảnh hưởng đến giá · 2.3 Phương trình trao đổi MV = PQ · 2.4 NVT và luật Metcalfe · 2.5 Định giá theo dòng thu nhập · 2.6 So sánh với đối thủ · 2.7 Thanh khoản, độ sâu thị trường và AMM · 2.8 Công cụ hiện có, oracle và khoảng trống nghiên cứu  
> **Trích dẫn:** chuẩn IEEE, số thứ tự khớp với `07_tai_lieu_tham_khao.md`.

Chương này trình bày nền tảng lý thuyết cho công cụ định giá token: token là gì và được phát hành ra sao, những yếu tố nào chi phối giá, các mô hình định lượng được dùng để ước tính giá trị hợp lý, và những công cụ hiện có trên thị trường. Mỗi mô hình được trình bày theo cùng một cấu trúc gồm ý tưởng kinh tế, công thức, ví dụ số và giới hạn, để Chương 4 có thể cài đặt trực tiếp.

---

## 2.1 Blockchain, token và tokenomics

### 2.1.1 Blockchain và nền tảng Ethereum
Blockchain là một sổ cái phân tán. Các giao dịch được gom thành khối, mỗi khối chứa giá trị băm của khối trước nên tạo thành một chuỗi không thể sửa đổi mà không bị phát hiện [1]. Một cơ chế đồng thuận giúp các nút trong mạng thống nhất về trạng thái sổ cái mà không cần bên trung gian tin cậy. Bitcoin dùng bằng chứng công việc (Proof-of-Work), còn Ethereum từ năm 2022 chuyển sang bằng chứng cổ phần (Proof-of-Stake). Trong cơ chế này, các nút xác thực (validator) phải ký quỹ tối thiểu 32 ETH và sẽ bị phạt nếu hành xử gian lận.

Ethereum mở rộng blockchain thành một máy tính phân tán: ngoài chuyển tiền, mạng còn chạy được các hợp đồng thông minh (smart contract), tức là chương trình được lưu và thực thi trên máy ảo Ethereum (EVM) [2]. Với đề tài định giá, đặc điểm quan trọng nhất của blockchain là **tính minh bạch của dữ liệu**. Mọi giao dịch, số dư và sự kiện của hợp đồng đều công khai, nên mô hình định giá có thể dùng trực tiếp dữ liệu sử dụng mạng (số giao dịch, số địa chỉ hoạt động, giá trị chuyển) thay cho báo cáo tài chính do bên thứ ba lập.

### 2.1.2 Token và chuẩn ERC-20
Token là tài sản số được phát hành trên một blockchain có sẵn. Khác với coin gốc của chuỗi như BTC hay ETH, token không cần mạng riêng mà được quản lý bởi một hợp đồng thông minh. Theo chức năng, token thường được chia thành ba nhóm:
- **Token thanh toán:** dùng làm phương tiện trao đổi.
- **Token quản trị:** cho phép biểu quyết các thay đổi của giao thức, ví dụ UNI hoặc AAVE.
- **Token tiện ích:** dùng để trả phí hoặc truy cập dịch vụ, ví dụ LINK để trả phí cho oracle.

Trên Ethereum, phần lớn token tuân theo chuẩn **ERC-20** [3], [4]. Chuẩn này quy định các hàm cơ bản:
- `totalSupply()`: tổng lượng token đang tồn tại.
- `balanceOf(address)`: số dư của một địa chỉ.
- `transfer(address to, uint256 amount)`: chuyển token.
- Sự kiện `Transfer(from, to, value)`: được phát ra mỗi khi token đổi chủ.

Sự kiện `Transfer` là nguồn dữ liệu gốc để tính khối lượng giao dịch on-chain và số địa chỉ hoạt động trong ngày, hai đầu vào của mô hình NVT và Metcalfe ở Mục 2.4. Do EVM không có số thực, số dư được lưu dưới dạng số nguyên và phải quy đổi theo trường `decimals`:

$$\text{Số dư thực} = \frac{\text{raw\_balance}}{10^{\text{decimals}}}$$

### 2.1.3 Tokenomics
Tokenomics là "chính sách tiền tệ" của một token, mô tả cách token được phát hành, phân bổ và thu hồi [5]. Có ba nhóm đại lượng cần lượng hóa khi định giá:

1. **Các khái niệm cung:**
   - *Cung lưu hành $S_c$*: lượng token đang được giao dịch tự do. Vốn hóa thị trường được tính bằng $\text{MC} = P \cdot S_c$.
   - *Tổng cung $S_t$*: lượng token đã phát hành trừ phần đã bị đốt.
   - *Cung tối đa $S_{\max}$*: trần phát hành, ví dụ 21 triệu BTC [1]. Nhiều token không có trần này.
   - *Vốn hóa pha loãng hoàn toàn* $\text{FDV} = P \cdot S_{\max}$ (hoặc $P \cdot S_t$): khoảng cách giữa FDV và MC cho thấy lượng cung tiềm năng sẽ còn đổ ra thị trường.
2. **Lạm phát và lịch mở khóa (vesting):** token của đội ngũ và nhà đầu tư sớm thường bị khóa rồi mở dần theo lịch. Mỗi đợt mở khóa làm tăng $S_c$. Nếu nhu cầu sử dụng không tăng tương ứng, áp lực bán sẽ kéo giá xuống.
3. **Cơ chế đốt (burn):** token bị gửi tới địa chỉ không ai kiểm soát, làm giảm cung vĩnh viễn. Ví dụ điển hình là EIP-1559 trên Ethereum: phần phí cơ sở (base fee) của mỗi giao dịch bị đốt [6]. Về mặt kinh tế, đốt token tương tự việc doanh nghiệp mua lại cổ phiếu, khiến mỗi token còn lại đại diện cho phần giá trị mạng lớn hơn.

Cong, Li và Wang [5] mô hình hóa giá token như kết quả cân bằng giữa nhu cầu sử dụng của người dùng và kỳ vọng đầu cơ. Giá token phụ thuộc vào mức độ chấp nhận (adoption) của nền tảng, và ngược lại, giá token cũng ảnh hưởng tới tốc độ chấp nhận. Đây là cơ sở để các mô hình trong chương này dùng **mức độ sử dụng mạng** làm thước đo giá trị nội tại.

---

## 2.2 Các yếu tố ảnh hưởng đến giá token

Giá thị trường của token là kết quả của cung, cầu và kỳ vọng. Các yếu tố tác động có thể chia thành hai nhóm.

### 2.2.1 Yếu tố nội tại
- **Tokenomics:** tốc độ lạm phát, lịch mở khóa và cơ chế đốt quyết định phía cung (Mục 2.1.3).
- **Mức độ sử dụng thực tế:** số người dùng, số giao dịch, giá trị được chuyển trên mạng, TVL của giao thức DeFi. Đây là các đại lượng mà mô hình MV = PQ, NVT và Metcalfe dùng làm đầu vào.
- **Khả năng tạo dòng tiền:** phí mà giao thức thu được và phần chia lại cho người nắm giữ token qua staking hoặc mua lại rồi đốt. Đây là cơ sở của định giá theo dòng thu nhập (Mục 2.5).
- **Quyền quản trị và đội ngũ:** chất lượng phát triển, mức độ phi tập trung, lịch sử kiểm toán bảo mật.

### 2.2.2 Yếu tố bên ngoài
- **Xu hướng chung của thị trường:** giá các token có xu hướng biến động cùng chiều với BTC. Dữ liệu của nhóm (Chương 3) cho thấy trong 12 tháng đến 28/11/2026, BTC giảm khoảng 34%, còn ETH và SOL giảm 45–48%.
- **Tâm lý và đầu cơ:** tin tức, mạng xã hội và hiệu ứng đám đông có thể đẩy giá xa khỏi giá trị cơ bản trong thời gian dài.
- **Thanh khoản:** token có sổ lệnh mỏng hoặc bể thanh khoản nhỏ dễ bị một vài lệnh lớn làm lệch giá (Mục 2.7).
- **Pháp lý và an ninh:** quy định của cơ quan quản lý và các vụ tấn công hợp đồng thông minh có thể làm giá giảm đột ngột.

Mô hình định giá định lượng chỉ nắm bắt được nhóm yếu tố nội tại có thể đo đếm. Tâm lý thị trường và sự kiện bất thường nằm ngoài mô hình. Đây là giới hạn chung của công cụ và sẽ được đánh giá lại ở Mục 5.4.

---

## 2.3 Phương trình trao đổi MV = PQ

### 2.3.1 Nguồn gốc
Phương trình trao đổi do Irving Fisher phát biểu năm 1911 [7]:

$$M \cdot V = P \cdot Q$$

Trong đó $M$ là lượng tiền lưu thông, $V$ là vận tốc luân chuyển (số lần trung bình một đơn vị tiền đổi chủ trong kỳ), $P$ là mức giá và $Q$ là sản lượng giao dịch thực. Tích $P \cdot Q$ là tổng giá trị giao dịch danh nghĩa trong kỳ.

### 2.3.2 Áp dụng cho token
Burniske [8] đề xuất coi mỗi giao thức là một nền kinh tế nhỏ dùng token của chính nó làm tiền. Trước đó, Burniske và White [9] cũng là những người sớm lập luận rằng tài sản mã hóa là một lớp tài sản riêng, cần phương pháp định giá riêng. Áp dụng phương trình trao đổi vào nền kinh tế của token, ta có:
- $P \cdot Q$ là tổng giá trị giao dịch được thanh toán bằng token trong một năm. Trong đề tài, đại lượng này được ước tính bằng khối lượng giao dịch quy năm $\text{PQ} = \overline{\text{Volume}}_{24h} \times 365$, hoặc bằng khối lượng on-chain khi có, để giảm ảnh hưởng của giao dịch ảo (wash trading) trên sàn.
- $M$ là giá trị cần có của lượng token lưu hành để phục vụ lượng giao dịch đó: $M = P_{\text{fair}} \cdot S_c$.
- $V$ là vận tốc luân chuyển theo năm.

Từ $M \cdot V = P \cdot Q$ suy ra giá trị hợp lý của một token:

$$\boxed{P_{\text{fair}} = \frac{P \cdot Q}{V \cdot S_c}}$$

Công thức cho thấy **vận tốc càng cao thì mỗi token càng cần ít giá trị** để phục vụ cùng một lượng giao dịch. Đây là lý do các dự án tìm cách giảm vận tốc bằng staking hoặc khóa token.

**Ví dụ số.** Một token có tổng giá trị giao dịch $\text{PQ} = 500$ triệu USD/năm, vận tốc $V = 8$ và cung lưu hành $S_c = 50$ triệu token. Khi đó:

$$M = \frac{500}{8} = 62{,}5 \text{ triệu USD}, \qquad P_{\text{fair}} = \frac{62{,}5}{50} = 1{,}25 \text{ USD}$$

Nếu vận tốc tăng lên $V = 10$ trong khi PQ không đổi, giá hợp lý giảm còn $1{,}00$ USD. Như vậy giá hợp lý tỷ lệ nghịch với vận tốc.

### 2.3.3 Ước lượng vận tốc và vấn đề vòng lặp
Vận tốc không quan sát trực tiếp được. Cách phổ biến là tính vận tốc thực nghiệm:

$$V_t = \frac{\text{PQ}_t}{\text{MC}_t} = \frac{\overline{\text{Volume}}_{24h,t} \times 365}{P_t \cdot S_{c,t}}$$

Tuy nhiên, nếu thay chính $V_t$ này vào công thức ở Mục 2.3.2 thì $P_{\text{fair},t} = P_t$, tức mô hình chỉ lặp lại giá thị trường. Để tránh vòng lặp, $V$ phải là một **chuẩn dài hạn được ước lượng từ quá khứ**. Đề tài dùng trung vị trượt của $W = 90$ ngày **trước** ngày định giá:

$$\hat V_t = \operatorname{median}\{V_{t-W}, \dots, V_{t-1}\}$$

Trung vị được chọn thay cho trung bình vì kháng được các ngày đột biến. Cửa sổ chỉ gồm các ngày trước $t$ nên không có rò rỉ dữ liệu tương lai, giúp kết quả backtest ở Chương 5 phản ánh đúng khả năng dự báo. Khi đó:

$$\frac{P_{\text{fair},t}}{P_t} = \frac{V_t}{\hat V_t}$$

Nghĩa là mô hình kết luận token **bị định giá thấp** khi mức sử dụng (giao dịch so với vốn hóa) cao hơn chuẩn lịch sử, và **bị định giá cao** khi ngược lại.

**Giới hạn.** Volume trên sàn gồm cả giao dịch đầu cơ và bán tháo. Dữ liệu của nhóm cho thấy trong đợt bán tháo đầu tháng 2/2026, volume tăng vọt khiến giá hợp lý theo MV = PQ cao gấp 2,6–3,3 lần giá thị trường. Mô hình đã hiểu nhầm volume hoảng loạn là "nhu cầu sử dụng". Vì vậy MV = PQ chỉ nên là một thành phần trong mô hình kết hợp (Mục 4.2), và cần đi kèm cờ cảnh báo khi volume bất thường.

---

## 2.4 Mô hình NVT và luật Metcalfe

### 2.4.1 Tỷ số NVT
Tỷ số NVT (Network Value to Transactions) được Willy Woo phổ biến năm 2017 [10]. Tỷ số này so sánh giá trị mạng với giá trị giao dịch on-chain mỗi ngày:

$$\text{NVT}_t = \frac{\text{MC}_t}{\text{On-chain Volume}_{24h,t}}$$

NVT thường được ví như chỉ số P/E của cổ phiếu: giá trị giao dịch đóng vai trò "lợi nhuận" mà mạng tạo ra. NVT cao bất thường cho thấy vốn hóa tăng nhanh hơn mức sử dụng, một dấu hiệu bong bóng. NVT thấp cho thấy mạng đang được sử dụng nhiều so với giá trị thị trường của nó. Về bản chất, NVT là nghịch đảo của vận tốc on-chain theo ngày, nên NVT và MV = PQ là hai cách nhìn của cùng một ý tưởng.

Để quy NVT thành giá, đề tài lấy NVT chuẩn bằng trung vị 90 ngày gần nhất của chính token đó:

$$P_{\text{NVT},t} = \frac{\text{NVT}_{\text{median},90d} \times \text{On-chain Volume}_{24h,t}}{S_{c,t}}$$

*Ví dụ:* NVT chuẩn bằng 40, volume on-chain bằng 25 triệu USD/ngày và $S_c$ bằng 50 triệu token thì $P_{\text{NVT}} = 40 \times 25 / 50 = 20$ USD.

NVT có hai điểm yếu. Thứ nhất, volume on-chain bao gồm cả giao dịch nội bộ giữa các ví của sàn. Thứ hai, NVT chỉ cho biết token đắt hay rẻ *tương đối với lịch sử của chính nó*, không cho biết giá trị tuyệt đối.

### 2.4.2 Luật Metcalfe
Luật Metcalfe phát biểu rằng giá trị của một mạng truyền thông tỷ lệ với bình phương số người dùng $n$, vì số kết nối có thể có giữa $n$ người là $n(n-1)/2$ [11]:

$$V_{\text{network}} \propto n^2$$

Trên blockchain, $n$ được đo bằng số địa chỉ hoạt động mỗi ngày (DAA). Mô hình tổng quát cho phép số mũ $\beta$ khác 2:

$$\text{MC}_t = \alpha \cdot \text{DAA}_t^{\beta} \quad\Longrightarrow\quad P_{\text{Metcalfe},t} = \frac{\alpha \cdot \text{DAA}_t^{\beta}}{S_{c,t}}$$

Hai tham số $\alpha$ và $\beta$ được ước lượng bằng hồi quy tuyến tính trên thang log:

$$\ln \text{MC}_t = \ln \alpha + \beta \ln \text{DAA}_t + \varepsilon_t$$

Khi $\beta = 2$, ta có đúng luật Metcalfe. Alabi [12] kiểm định trên Bitcoin, Ethereum và Dash giai đoạn 2009–2017 và cho rằng giá trị các mạng này bám theo luật Metcalfe. Tuy nhiên, kết quả phụ thuộc mạnh vào giai đoạn dữ liệu. Vì vậy đề tài ước lượng $\beta$ từ dữ liệu thay vì cố định bằng 2, và báo cáo giá trị $\beta$ thu được ở Chương 5.

Điểm yếu của mô hình là số địa chỉ hoạt động không bằng số người dùng thật. Một người có thể dùng nhiều địa chỉ, và các chiến dịch airdrop có thể làm DAA tăng ảo.

---

## 2.5 Định giá theo dòng thu nhập

### 2.5.1 Nguyên lý
Với những token mang lại thu nhập cho người nắm giữ, giá trị có thể được tính như cổ phiếu: bằng giá trị hiện tại của dòng tiền tương lai chiết khấu theo tỷ suất sinh lời yêu cầu [13]. Thu nhập của token có thể đến từ:
- chia phí giao thức cho người staking, ví dụ phí giao dịch của DEX;
- phần thưởng staking từ việc xác thực mạng Proof-of-Stake;
- mua lại rồi đốt token bằng doanh thu giao thức, giúp tăng gián tiếp giá trị của mỗi token còn lại (Mục 2.1.3).

Trong đề tài, dòng tiền của toàn mạng được lấy từ **phí** (fees, tổng người dùng trả) và **doanh thu** (revenue, phần giao thức hoặc người nắm token giữ lại) theo ngày của DefiLlama [14]. Cần phân biệt hai khái niệm này: chỉ revenue mới thực sự thuộc về người nắm giữ token.

### 2.5.2 Mô hình chiết khấu dòng tiền
Gọi $CF_k$ là dòng tiền thuộc về người nắm giữ token trong năm $k$ và $r$ là tỷ suất chiết khấu. Tổng giá trị của mạng là:

$$\text{Value}_0 = \sum_{k=1}^{N} \frac{CF_k}{(1+r)^k} + \frac{TV_N}{(1+r)^N}, \qquad TV_N = \frac{CF_{N+1}}{r - g}$$

Trong đó $TV_N$ là giá trị cuối kỳ, giả định dòng tiền tăng đều với tốc độ $g < r$ sau năm $N$. Trường hợp đơn giản nhất ($N = 0$) là mô hình tăng trưởng đều của Gordon [15]:

$$\text{Value}_0 = \frac{CF_1}{r - g}, \qquad P_{\text{income}} = \frac{\text{Value}_0}{S_c}$$

**Ví dụ số.** Giao thức có doanh thu chia cho người nắm token là $CF_1 = 20$ triệu USD/năm, tăng trưởng $g = 5\%$/năm. Do rủi ro của tài sản mã hóa rất cao, nhà đầu tư yêu cầu $r = 25\%$. Khi đó $\text{Value}_0 = 20 / (0{,}25 - 0{,}05) = 100$ triệu USD. Với $S_c = 50$ triệu token, $P_{\text{income}} = 2{,}00$ USD.

### 2.5.3 Bội số theo thu nhập
Do khó dự báo dòng tiền dài hạn, thực tế người ta còn dùng các bội số kiểu P/E. Ví dụ Token Terminal [16] dùng hai tỷ số:
- $\text{P/F} = \text{MC} / \text{Phí quy năm}$;
- $\text{P/S} = \text{MC} / \text{Doanh thu quy năm}$.

Bội số thấp hơn mức trung vị của nhóm cùng ngành gợi ý token đang rẻ so với khả năng tạo thu nhập.

### 2.5.4 Giới hạn
Kết quả của mô hình rất nhạy với $r$ và $g$. Chẳng hạn, trong ví dụ trên, giảm $r$ từ 25% xuống 20% làm giá trị tăng 33%. Ngoài ra, nhiều token quản trị không được hưởng trực tiếp doanh thu nào, nên $CF = 0$ và mô hình không áp dụng được. Với BTC, dòng tiền là phí trả cho thợ đào chứ không thuộc về người nắm giữ, nên phương pháp này chỉ mang tính tham khảo. Báo cáo cần nêu rõ giả định $r$ và $g$, và trình bày phân tích độ nhạy theo hai tham số này.

---

## 2.6 Định giá so sánh với đối thủ

### 2.6.1 Nguyên lý
Phương pháp so sánh (comparable analysis) định giá một tài sản dựa trên bội số của các tài sản tương tự, giống cách dùng P/E hay EV/EBITDA trung bình ngành trong định giá doanh nghiệp [13]. Với giao thức DeFi, thước đo quy mô tương ứng là **TVL**: tổng giá trị tài sản người dùng gửi vào hợp đồng của giao thức. Bội số phổ biến nhất là:

$$\text{Multiple}_{\text{MC/TVL}} = \frac{\text{MC}}{\text{TVL}}$$

Có thể dùng thêm P/F và P/S ở Mục 2.5.3.

### 2.6.2 Quy trình
1. **Chọn nhóm so sánh** cùng lĩnh vực: DEX (UNI, CRV, SUSHI, BAL), cho vay (AAVE, COMP, MKR), hạ tầng (LINK, GRT), lớp 1 và lớp 2 (ETH, SOL, ARB).
2. **Tính bội số chuẩn ngành** bằng trung vị. Trung vị được dùng thay cho trung bình để một token dẫn đầu không làm lệch chuẩn:
   $$\text{Multiple}_{\text{sector}} = \operatorname{median}_{i \in \text{peer}} \frac{\text{MC}_i}{\text{TVL}_i}$$
3. **Suy ra giá hợp lý:**
   $$P_{\text{comp}} = \frac{\text{Multiple}_{\text{sector}} \times \text{TVL}_{\text{target}}}{S_{c,\text{target}}}$$

### 2.6.3 Giới hạn
- **TVL tính bằng USD nên phụ thuộc vào giá tài sản bị khóa.** Dữ liệu của nhóm cho thấy hệ số tương quan giữa biến động ngày của TVL và giá là 0,91 với ETH và 0,79 với SOL. Khi thị trường giảm, cả MC lẫn TVL cùng giảm, nên MC/TVL ít thay đổi.
- **Không áp dụng được cho BTC.** TVL của hệ DeFi trên Bitcoin rất nhỏ so với vốn hóa (MC/TVL khoảng 320).
- **Phương pháp chỉ cho giá trị tương đối.** Nếu cả ngành đang bị thổi phồng thì token mục tiêu cũng bị định giá cao theo.

---

## 2.7 Thanh khoản, độ sâu thị trường và AMM

### 2.7.1 Thanh khoản và độ sâu thị trường
Thanh khoản là khả năng mua hoặc bán một lượng tài sản lớn mà giá thay đổi ít. Độ sâu thị trường đo lượng tài sản có thể khớp quanh giá hiện tại. Token thanh khoản thấp có thể bị đẩy giá bằng vài lệnh lớn, nên giá thị trường của nó kém tin cậy để làm chuẩn so sánh. Vì vậy, mỗi kết quả định giá trong đề tài kèm một **điểm tin cậy thanh khoản** $s \in [0, 1]$, nội suy tuyến tính theo thang log của volume 24 giờ:

$$s = \operatorname{clip}\!\left(\frac{\log_{10}\text{Volume}_{24h} - 6}{3},\; 0,\; 1\right)$$

Theo đó, volume dưới 1 triệu USD/ngày cho $s = 0$, trên 1 tỷ USD/ngày cho $s = 1$. Điểm này được dùng để cảnh báo người dùng và để giảm trọng số của token kém thanh khoản khi đánh giá.

### 2.7.2 AMM theo tích không đổi
Phần lớn sàn phi tập trung trên Ethereum dùng cơ chế tạo lập thị trường tự động (AMM) thay cho sổ lệnh. Uniswap v2 [17] giữ hai lượng dự trữ $x$ (token A) và $y$ (token B) sao cho:

$$x \cdot y = k$$

Giá giao ngay của A tính theo B là $P_{\text{spot}} = y / x$. Khi bán $\Delta x$ token A vào bể với phí $f$ (bằng 0,3% ở Uniswap v2), người bán nhận về:

$$\Delta y = \frac{y \cdot \Delta x (1-f)}{x + \Delta x (1-f)}$$

**Ví dụ số.** Bể có $x = 1.000.000$ A và $y = 2.000.000$ USDC, nên $P_{\text{spot}} = 2{,}0$. Bán $\Delta x = 50.000$ A:
- Khi bỏ qua phí, người bán nhận $\Delta y = 2.000.000 \times 50.000 / 1.050.000 \approx 95.238$ USDC. Giá khớp trung bình là 1,905, thấp hơn giá giao ngay **4,8%**. Đây là tác động giá (price impact).
- Khi tính phí 0,3%, người bán nhận khoảng 94.966 USDC.
- Sau giao dịch, giá giao ngay mới còn $1.904.762 / 1.050.000 \approx 1{,}81$, tức giảm 9,3%.

Tác động giá xấp xỉ $\Delta x / (x + \Delta x)$, nên bể càng nhỏ so với lệnh thì giá càng lệch. *Trượt giá* (slippage) là chênh lệch giữa giá dự kiến khi đặt lệnh và giá thực nhận. Trượt giá gồm tác động giá của chính lệnh đó cộng với biến động do các giao dịch khác chen vào trước.

Uniswap v3 [18] cho phép nhà cung cấp thanh khoản tập trung vốn vào một khoảng giá. Cách này tăng độ sâu quanh giá hiện tại nhưng làm thanh khoản ngoài khoảng đó mỏng đi.

### 2.7.3 Giá trung bình theo thời gian (TWAP)
Giá giao ngay của AMM có thể bị thao túng trong một khối. Kẻ tấn công vay một lượng lớn tài sản, đẩy giá, khai thác giao thức đang đọc giá này, rồi trả nợ ngay trong cùng giao dịch [19]. Để chống lại, Uniswap lưu một biến tích lũy giá theo thời gian, từ đó tính được giá trung bình trên một khoảng $[t_1, t_2]$ [17]:

$$\text{TWAP}_{t_1,t_2} = \frac{1}{t_2 - t_1}\int_{t_1}^{t_2} P(t)\,dt \approx \frac{\sum_i P_i \,\Delta t_i}{\sum_i \Delta t_i}$$

Muốn làm lệch TWAP, kẻ tấn công phải giữ giá lệch qua nhiều khối liên tiếp và chịu thua lỗ do người khác kinh doanh chênh lệch giá. Chi phí này tăng theo độ dài cửa sổ và độ sâu của bể [20]. Đổi lại, TWAP phản ứng chậm với biến động thật. Trong đề tài, TWAP được dùng làm một mức giá tham chiếu khó thao túng (mô hình `twap.py`).

---

## 2.8 Công cụ hiện có, oracle và khoảng trống nghiên cứu

### 2.8.1 Các công cụ dữ liệu và phân tích
**Bảng 2.1. So sánh các công cụ hiện có**

| Công cụ | Cung cấp | Có đưa ra giá trị hợp lý? |
|---|---|---|
| CoinGecko [21], CoinMarketCap [22] | Giá, vốn hóa, volume, cung lưu hành của hàng chục nghìn token; có API miễn phí | Không, chỉ hiển thị dữ liệu thị trường |
| DefiLlama [14] | TVL, phí, doanh thu của giao thức và blockchain; mã nguồn mở | Không, nhưng là nguồn dữ liệu cơ bản tốt |
| Messari [23] | Báo cáo nghiên cứu, hồ sơ tokenomics, chỉ số on-chain | Một phần, qua báo cáo phân tích thủ công |
| Token Terminal [16] | Doanh thu và phí giao thức, bội số P/F và P/S | Một phần, cung cấp bội số để tự so sánh |
| Binance API [24], Etherscan [25] | Dữ liệu nến khung ngắn; giao dịch và sự kiện on-chain | Không, là dữ liệu thô |
| Chainlink Data Feeds [26] | Giá thị trường tổng hợp, đưa lên blockchain | Không, phản ánh giá thị trường chứ không phải giá trị |

### 2.8.2 Oracle và rủi ro dữ liệu giá
Hợp đồng thông minh không thể tự gọi API bên ngoài vì mọi nút phải thực thi ra cùng một kết quả. **Oracle** là hạ tầng đưa dữ liệu ngoài chuỗi vào blockchain. Mạng oracle phi tập trung của Chainlink [26] hoạt động như sau:
- nhiều nút độc lập cùng lấy giá từ nhiều nguồn;
- một hợp đồng tổng hợp lấy trung vị các câu trả lời;
- giá được cập nhật khi lệch quá một ngưỡng nhất định, hoặc sau một khoảng thời gian tối đa (heartbeat).

Có hai rủi ro chính:
1. **Thao túng giá giao ngay bằng vay nhanh (flash loan)** [19]: như mô tả ở Mục 2.7.3. Giao thức đọc trực tiếp giá giao ngay của một bể nhỏ đặc biệt dễ bị tấn công.
2. **Dữ liệu lỗi thời:** khi mạng tắc nghẽn, giá trên chuỗi có thể không được cập nhật kịp. Vì vậy hợp đồng `TokenValuation.sol` của đề tài lưu thời điểm cập nhật kèm mỗi định giá và cung cấp hàm `isValuationStale(token, maxAgeSec)`, để ứng dụng đọc dữ liệu có thể từ chối giá trị quá cũ (chi tiết ở Phụ lục).

### 2.8.3 Khoảng trống mà đề tài nhắm tới
Các công cụ trên hoặc chỉ hiển thị dữ liệu thị trường, hoặc cung cấp chỉ số rời rạc để người dùng tự diễn giải. Chưa có công cụ mở nào **tự động kết hợp nhiều mô hình định giá** (MV = PQ, NVT, Metcalfe, dòng thu nhập, so sánh) thành một giá trị hợp lý duy nhất, **đánh giá sai số** của giá trị đó so với giá thực tế, và **ghi kết quả lên blockchain** để hợp đồng khác sử dụng. Đề tài lấp khoảng trống này bằng một công cụ Python mã nguồn mở có các tính năng sau:
- lấy dữ liệu từ CoinGecko và DefiLlama;
- tính giá hợp lý bằng nhiều mô hình rồi kết hợp có trọng số;
- báo cáo MAE, RMSE và MAPE;
- công bố kết quả lên hợp đồng thông minh trên mạng thử nghiệm Sepolia.

Như đã nêu ở Chương 1, công cụ chỉ phục vụ tham khảo, không phải khuyến nghị đầu tư.

---

## Tiểu kết Chương 2
Chương 2 đã trình bày các khái niệm nền tảng về blockchain, token và tokenomics, các yếu tố chi phối giá token, và năm nhóm phương pháp định giá:
- phương trình trao đổi MV = PQ;
- NVT và luật Metcalfe;
- chiết khấu dòng thu nhập;
- so sánh bội số MC/TVL;
- giá tham chiếu TWAP từ AMM.

Mỗi phương pháp dựa trên một giả định riêng về nguồn gốc giá trị của token và đều có điểm yếu riêng. MV = PQ nhạy với volume đầu cơ, NVT và Metcalfe phụ thuộc vào chất lượng dữ liệu on-chain, DCF nhạy với tỷ suất chiết khấu, còn phương pháp so sánh chỉ cho giá trị tương đối. Đây là lý do Chương 4 kết hợp các mô hình theo trọng số tối ưu hóa trên sai số lịch sử thay vì dựa vào một mô hình duy nhất. Chương 3 tiếp theo trình bày nguồn dữ liệu và quy trình tiền xử lý để cung cấp đầu vào cho các mô hình này.
