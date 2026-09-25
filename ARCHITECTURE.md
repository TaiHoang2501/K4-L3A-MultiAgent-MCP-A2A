# L3A Architecture Record

Team phải cập nhật tài liệu này cùng source. Mục tiêu là mô tả quyết định có thể kiểm chứng, không ghi prompt bí mật hoặc chain-of-thought.

## 1. System overview

Mô hình Multi-Agent được thiết kế theo dạng Orchestrator-Workers. Coordinator nhận input, quyết định thứ tự gọi các Specialist Agents. Các Specialist lấy dữ liệu từ MCP Gateway. Sau khi thu thập đủ, Verifier đối chiếu và xuất kết quả cuối cùng.

```text
Input → Coordinator → Specialists → Verifier → Output
                         │              │
                         └── MCP ───────┴── Trace
```

## 2. Agent ownership

| Actor | Input | Trách nhiệm | Output/handoff | Quyền gọi Tool (MCP) |
| --- | --- | --- | --- | --- |
| **Coordinator** | `inputs/<case_id>.json` | Phân tích ngữ cảnh ban đầu, định tuyến tới các specialist phù hợp, quản lý workflow state. | Handoff payload cho Specialist tương ứng, chuyển cho Verifier khi xong. | *Không có quyền gọi tool* |
| **Order/item** | Thông tin khách khiếu nại (từ Coordinator) | Xác minh sự tồn tại của đơn hàng, thông tin sản phẩm và lịch sử mua hàng. | Báo cáo trạng thái đơn, giá trị đơn, tính hợp lệ của item. | `get_order`, `get_order_items`, `get_product_context` |
| **Payment** | Thông tin đơn hàng | Xác minh dòng tiền, trạng thái thanh toán, tiền hoàn trả, đối soát số dư. | Trạng thái thanh toán (đã thanh toán, nợ, hoàn trả). | `get_order_payments`, `get_payment_timeline`, `get_refund_timeline`, `get_customer_history` |
| **Shipment** | Tracking ID / Mã đơn | Kiểm tra tiến trình vận chuyển, tình trạng giao hàng, thời gian chốt. | Báo cáo tình trạng giao hàng (trễ, thất lạc, thành công). | `get_shipment_summary` |
| **Policy** | Tình huống vi phạm (từ các agent khác) | Đối chiếu điều khoản bảo hành, quy định của platform và lịch sử người bán. | Đánh giá trách nhiệm (Claim Assessment) dựa trên luật. | `get_policy`, `get_sellers` |
| **Verifier** | Báo cáo tổng hợp từ tất cả Specialist | Kiểm tra logic chéo (ví dụ: tiền trả có khớp tiền đơn), map evidence, chốt schema chuẩn. | JSON Output cuối cùng đúng format `l3a-output-v2.schema.json`. | *Không có quyền gọi tool* |

## 3. A2A protocol

*   **Message Envelope**: Mọi giao tiếp giữa các Agent phải bọc trong chuẩn envelope:
    ```json
    {
      "case_id": "L3A_CASE_001",
      "sender": "coordinator",
      "receiver": "payment_agent",
      "payload": { "order_id": "12345" },
      "evidence_refs_collected": ["evidence_8f2a"]
    }
    ```
*   **Correlation**: Mọi thông điệp và trace log phải đính kèm `case_id`.
*   **Điều kiện handoff**: Một Specialist chỉ trả kết quả (handoff) về cho Coordinator khi đã truy vấn đủ dữ liệu MCP hoặc gặp lỗi không thể phục hồi.
*   **Tránh vòng lặp**: Đặt `max_turns = 3` cho mỗi Specialist. Vượt quá 3 lần gọi tool mà chưa xong sẽ ép ngắt (timeout) và báo lỗi về Coordinator.
*   **Trace**: Hệ thống chỉ emit các Trace Observable như `agent_started`, `tool_called`, `handoff_completed`.

## 4. Evidence lifecycle

1. Khi Specialist gọi MCP tool, tool trả về Data + `evidence_ref` (ID bằng chứng).
2. Hệ thống tự động đẩy `evidence_ref` này vào danh sách `evidence_refs_collected` của Envelope.
3. Đồng thời emit log `tool_result_consumed` với `case_id` và `evidence_ref`.
4. Bằng chứng được scope 100% theo `case_id`. Không được phép sử dụng `evidence_ref` của `case_A` để làm căn cứ phán quyết cho `case_B`.

## 5. Failure policy

| Failure | Retry? | Fallback | Trace event/code |
| --- | --- | --- | --- |
| **MCP timeout / 5xx** | Có (Max 3 lần, Exponential backoff) | Bỏ qua tool, báo cáo `data_unavailable` cho Coordinator | `mcp_retry_limit_exceeded` |
| **Not found (404)** | Không | Specialist kết luận thực thể không tồn tại | `resource_not_found` |
| **Source conflict** | Không | Ghi nhận Data Conflict, đẩy cho Verifier xử lý (ghi vào mảng `data_conflicts`) | `data_conflict_detected` |
| **Invalid specialist result** | Có (Max 1 lần) | Đóng case với status `needs_investigation` | `specialist_output_invalid` |

*Lưu ý: Tuyệt đối không phỏng đoán dữ liệu (hallucinate) nếu MCP trả về Not Found hoặc Timeout.*

## 6. Verification invariants

Trước khi Verifier xuất JSON cuối cùng, các biến bất biến (invariants) sau phải được check code:
*   **Schema validation:** Output phải parse thành công Pydantic model của `l3a-output-v2.schema.json`.
*   **Evidence linkage:** Bất kỳ ID bằng chứng nào nằm trong mảng `evidence_refs` của output đều phải tồn tại trong mảng `evidence_refs_collected` ở Envelope.
*   **Financial consistency:** Tiền khách trả = Tiền hàng + Tiền ship - Khuyến mãi.
*   **Confidence bounds:** `confidence` score luôn phải nằm trong khoảng [0.0, 1.0].

## 7. Reproducibility

*   **Model**: Sử dụng cố định **`Gemini 3.1 Flash Light`**.
*   **Config**: `temperature = 0.0` cho toàn bộ Agents để đảm bảo tính tất định (deterministic).
*   **Concurrency**: Chạy lệnh giới hạn song song 10 cases (`max_workers=10`).
*   **Dependencies**: Pin cứng phiên bản trong `pyproject.toml` và `uv.lock`.
