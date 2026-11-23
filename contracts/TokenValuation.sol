// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TokenValuation
 * @notice Smart contract ghi nhận và phân phối kết quả định giá token từ các mô hình định giá off-chain / on-chain
 * @dev Thuộc đề tài "Xây dựng công cụ định giá token dựa trên dữ liệu thị trường"
 *      Môn: Chuỗi khối và công nghệ sổ cái phân tán
 *      Nhóm: Huỳnh, Khanh, Kha, Nam Khánh
 *      Deploy trên mạng thử nghiệm: Ethereum Sepolia Testnet
 */
contract TokenValuation {
    // =========================================================================
    // CẤU TRÚC DỮ LIỆU & BIẾN TRẠNG THÁI
    // =========================================================================

    struct ValuationRecord {
        uint256 valueUSD;      // Giá trị hợp lý quy đổi USD với 8 chữ số thập phân (tương thích Chainlink format: 1 USD = 10^8)
        uint256 updatedAt;     // Thời điểm block timestamp ghi nhận kết quả định giá
        uint256 blockNumber;   // Chiều cao block tại thời điểm cập nhật
        address updatedBy;     // Địa chỉ ví Oracle / Publisher thực hiện giao dịch
    }

    /// @notice Chủ sở hữu hợp đồng (Admin)
    address public owner;

    /// @notice Danh sách địa chỉ ví được cấp quyền Oracle đẩy dữ liệu định giá
    mapping(address => bool) public authorizedOracles;

    /// @notice Ánh xạ từ địa chỉ Token sang bản ghi định giá mới nhất
    mapping(address => ValuationRecord) private _valuations;

    /// @notice Danh sách các token đã từng được cập nhật định giá
    address[] private _registeredTokens;
    mapping(address => bool) private _isTokenRegistered;

    // =========================================================================
    // SỰ KIỆN (EVENTS)
    // =========================================================================

    /**
     * @notice Phát ra khi một token được cập nhật mức định giá hợp lý mới
     * @param token Địa chỉ hợp đồng của token ERC-20
     * @param value Giá trị hợp lý theo USD (định dạng 8 decimals)
     * @param timestamp Thời điểm cập nhật trên blockchain
     * @param updatedBy Địa chỉ Oracle Publisher thực hiện giao dịch
     */
    event ValuationUpdated(
        address indexed token,
        uint256 value,
        uint256 timestamp,
        address indexed updatedBy
    );

    /**
     * @notice Phát ra khi trạng thái phân quyền của Oracle thay đổi
     */
    event OracleAuthorizationChanged(address indexed oracle, bool isAuthorized);

    /**
     * @notice Phát ra khi quyền sở hữu hợp đồng được chuyển giao
     */
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // =========================================================================
    // BỘ ĐIỀU KIỆN (MODIFIERS)
    // =========================================================================

    modifier onlyOwner() {
        require(msg.sender == owner, "TokenValuation: caller is not the owner");
        _;
    }

    modifier onlyOracle() {
        require(
            msg.sender == owner || authorizedOracles[msg.sender],
            "TokenValuation: caller is not an authorized oracle"
        );
        _;
    }

    // =========================================================================
    // HÀM KHỞI TẠO (CONSTRUCTOR)
    // =========================================================================

    constructor() {
        owner = msg.sender;
        authorizedOracles[msg.sender] = true;
        emit OracleAuthorizationChanged(msg.sender, true);
    }

    // =========================================================================
    // CÁC HÀM QUẢN TRỊ (ADMIN FUNCTIONS)
    // =========================================================================

    /**
     * @notice Cấp quyền hoặc thu hồi quyền Oracle cho một địa chỉ ví
     * @param _oracle Địa chỉ ví cần thiết lập
     * @param _isAuthorized Trạng thái ủy quyền
     */
    function setOracle(address _oracle, bool _isAuthorized) external onlyOwner {
        require(_oracle != address(0), "TokenValuation: invalid oracle address");
        authorizedOracles[_oracle] = _isAuthorized;
        emit OracleAuthorizationChanged(_oracle, _isAuthorized);
    }

    /**
     * @notice Chuyển quyền sở hữu hợp đồng sang chủ mới
     * @param newOwner Địa chỉ chủ sở hữu mới
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "TokenValuation: zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // =========================================================================
    // CÁC HÀM CẬP NHẬT ĐỊNH GIÁ (WRITE FUNCTIONS - ORACLE ONLY)
    // =========================================================================

    /**
     * @notice Cập nhật kết quả định giá hợp lý cho một token đơn lẻ
     * @param token Địa chỉ của token cần định giá
     * @param value Giá trị hợp lý ước tính (USD với 8 chữ số thập phân)
     */
    function setValuation(address token, uint256 value) public onlyOracle {
        require(token != address(0), "TokenValuation: token address cannot be zero");
        require(value > 0, "TokenValuation: valuation must be strictly positive");

        _valuations[token] = ValuationRecord({
            valueUSD: value,
            updatedAt: block.timestamp,
            blockNumber: block.number,
            updatedBy: msg.sender
        });

        if (!_isTokenRegistered[token]) {
            _isTokenRegistered[token] = true;
            _registeredTokens.push(token);
        }

        emit ValuationUpdated(token, value, block.timestamp, msg.sender);
    }

    /**
     * @notice Cập nhật kết quả định giá theo lô (batch update) để tiết kiệm phí gas
     * @param tokens Mảng danh sách địa chỉ token
     * @param values Mảng giá trị định giá tương ứng
     */
    function setValuationBatch(address[] calldata tokens, uint256[] calldata values) external onlyOracle {
        require(tokens.length == values.length, "TokenValuation: array length mismatch");
        require(tokens.length > 0, "TokenValuation: empty batch");

        for (uint256 i = 0; i < tokens.length; i++) {
            setValuation(tokens[i], values[i]);
        }
    }

    // =========================================================================
    // CÁC HÀM TRUY VẤN (READ / VIEW FUNCTIONS)
    // =========================================================================

    /**
     * @notice Lấy thông tin định giá mới nhất của một token
     * @param token Địa chỉ token cần kiểm tra
     * @return value Giá trị hợp lý tính bằng USD (8 decimals)
     * @return updatedAt Mốc thời gian block cập nhật cuối cùng (Unix timestamp)
     */
    function getValuation(address token) external view returns (uint256 value, uint256 updatedAt) {
        ValuationRecord memory record = _valuations[token];
        require(record.updatedAt > 0, "TokenValuation: no valuation recorded for this token");
        return (record.valueUSD, record.updatedAt);
    }

    /**
     * @notice Lấy đầy đủ chi tiết bản ghi định giá
     * @param token Địa chỉ token
     */
    function getValuationDetail(address token) external view returns (
        uint256 valueUSD,
        uint256 updatedAt,
        uint256 blockNumber,
        address updatedBy
    ) {
        ValuationRecord memory record = _valuations[token];
        require(record.updatedAt > 0, "TokenValuation: token not found");
        return (record.valueUSD, record.updatedAt, record.blockNumber, record.updatedBy);
    }

    /**
     * @notice Kiểm tra xem mức định giá của token đã bị cũ (stale) hay chưa
     * @param token Địa chỉ token
     * @param maxAgeSec Khoảng thời gian tối đa cho phép (giây, ví dụ 86400s = 1 ngày)
     * @return isStale True nếu đã quá hạn cập nhật hoặc chưa từng có dữ liệu
     */
    function isValuationStale(address token, uint256 maxAgeSec) external view returns (bool isStale) {
        ValuationRecord memory record = _valuations[token];
        if (record.updatedAt == 0) return true;
        return (block.timestamp - record.updatedAt) > maxAgeSec;
    }

    /**
     * @notice Lấy tổng số lượng token đã được ghi nhận trên smart contract
     */
    function getRegisteredTokenCount() external view returns (uint256) {
        return _registeredTokens.length;
    }

    /**
     * @notice Lấy địa chỉ token đã đăng ký theo vị trí index
     */
    function getRegisteredToken(uint256 index) external view returns (address) {
        require(index < _registeredTokens.length, "TokenValuation: index out of bounds");
        return _registeredTokens[index];
    }
}
