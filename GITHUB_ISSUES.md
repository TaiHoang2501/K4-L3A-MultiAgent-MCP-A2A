# Danh sách GitHub Issues - Dự án L3A Multi-Agent

Dưới đây là danh sách các Issue bạn có thể copy/paste trực tiếp lên GitHub (mục **Issues -> New Issue**).

---

## 🏗️ Issue #1: Khởi tạo kiến trúc A2A Protocol & Message Envelope
**Title:** `[Foundation] Thiết kế Message Envelope và chuẩn hóa giao tiếp A2A`

**Description:**
Thiết lập nền tảng giao tiếp giữa các Agents theo tài liệu ARCHITECTURE.md.
- [ ] Định nghĩa class/Pydantic model cho `MessageEnvelope` (chứa `case_id`, `sender`, `receiver`, `payload`, `evidence_refs_collected`).
- [ ] Cài đặt cơ chế timeout và đếm số lượt (max_turns = 3) để chống vòng lặp (infinite loop).
- [ ] Xây dựng khung (Base Agent) để các Agent khác kế thừa.
- [ ] Tích hợp logic xử lý lỗi MCP (retry tối đa 3 lần với 5xx/Timeout).

**Assignee:** Thành viên 1 (Coordinator)
**Labels:** `architecture`, `core`, `priority: high`

---

## 🤖 Issue #2: Xây dựng Coordinator Agent
**Title:** `[Agent] Xây dựng Coordinator Agent định tuyến luồng xử lý`

**Description:**
Xây dựng não bộ trung tâm của hệ thống.
- [ ] Đọc input từ `inputs/<case_id>.json` và khởi tạo Envelope.
- [ ] Viết prompt/logic để đánh giá ngữ cảnh và quyết định gọi Specialist Agent nào trước (ví dụ: luôn gọi Order Agent trước).
- [ ] Nhận kết quả từ Specialist, quyết định gọi Specialist tiếp theo hoặc chuyển thẳng cho Verifier nếu đã đủ thông tin.
- [ ] Bắt lỗi nếu Specialist trả về kết quả không hợp lệ hoặc quá timeout.

**Assignee:** Thành viên 1 (Coordinator)
**Labels:** `agent`, `coordinator`

---

## 📦 Issue #3: Xây dựng Order & Item Agent
**Title:** `[Agent] Xây dựng Order & Item Agent (Kiểm tra đơn hàng)`

**Description:**
Xây dựng Agent chuyên trách về thông tin đơn hàng và sản phẩm.
- [ ] Khai báo và bọc các MCP tools: `get_order`, `get_order_items`, `get_product_context`.
- [ ] Xử lý Prompt: Lấy thông tin từ Coordinator, gọi tool tương ứng để xác minh đơn hàng có tồn tại không.
- [ ] Trích xuất `evidence_ref` từ kết quả của MCP tool.
- [ ] Đóng gói kết quả (Status đơn hàng, tính hợp lệ của item) và trả về cho Coordinator.

**Assignee:** Thành viên 2 (Order & Payment Expert)
**Labels:** `agent`, `order`

---

## 💰 Issue #4: Xây dựng Payment Agent
**Title:** `[Agent] Xây dựng Payment Agent (Kiểm tra thanh toán & dòng tiền)`

**Description:**
Xây dựng Agent chuyên trách đối soát tiền bạc.
- [ ] Khai báo và bọc các MCP tools: `get_order_payments`, `get_payment_timeline`, `get_refund_timeline`, `get_customer_history`.
- [ ] Phân tích lịch sử thanh toán, phát hiện các lỗi như trừ tiền 2 lần (duplicate_charge) hoặc thanh toán lệch (payment_mismatch).
- [ ] Nếu MCP tool trả về `Not Found` (404), trả về kết quả `data_unavailable` (không được hallucinate).
- [ ] Trích xuất và đẩy `evidence_ref` vào Envelope.

**Assignee:** Thành viên 3 (Payment Expert)
**Labels:** `agent`, `payment`

---

## 🚚 Issue #5: Xây dựng Shipment & Policy Agent
**Title:** `[Agent] Xây dựng Shipment & Policy Agent (Vận chuyển & Chính sách)`

**Description:**
Xây dựng Agent chuyên trách truy vết vận chuyển và đối chiếu luật của platform.
- [ ] Khai báo và bọc MCP tools: `get_shipment_summary`, `get_policy`, `get_sellers`.
- [ ] Kiểm tra tình trạng giao hàng (đúng hạn, trễ, thất lạc).
- [ ] Dựa vào tình trạng vận chuyển, gọi tool Policy để kiểm tra xem lỗi thuộc về ai (Seller hay Logistics).
- [ ] Đưa ra kết luận (Claim Assessment) dựa trên bằng chứng thu thập được.

**Assignee:** Thành viên 4 (Shipment & Policy Expert)
**Labels:** `agent`, `shipment-policy`

---

## ⚖️ Issue #6: Xây dựng Verifier Agent & Chốt Output
**Title:** `[Agent] Xây dựng Verifier Agent và kiểm tra Invariants`

**Description:**
Xây dựng Agent đứng cuối luồng để ra phán quyết cuối cùng.
- [ ] Nhận toàn bộ context từ Coordinator.
- [ ] Xác định `primary_issue`, `case_status`, và `confidence` score.
- [ ] Kiểm tra chéo (Financial consistency): Đảm bảo số tiền khớp nhau.
- [ ] Map và xác minh `evidence_refs` hợp lệ (không chứa evidence ảo).
- [ ] Đảm bảo dữ liệu JSON đầu ra map 100% với Pydantic model của `l3a-output-v2.schema.json`.

**Assignee:** Thành viên 5 (Verifier & QA)
**Labels:** `agent`, `verifier`, `priority: high`

---

## 📊 Issue #7: Xử lý Evidence Lifecycle & Trace Logging
**Title:** `[Core] Xây dựng hệ thống Tracking Evidence & Observability`

**Description:**
Đảm bảo hệ thống pass qua các bài test tự động (`day09 validate`).
- [ ] Viết hàm tự động bắt và đẩy `evidence_ref` từ mọi MCP response vào `evidence_refs_collected`.
- [ ] Emit chính xác event log: `tool_result_consumed`, `data_conflict_detected`, `resource_not_found`... theo định dạng yêu cầu của lệnh check.
- [ ] Đảm bảo bằng chứng scope 100% theo `case_id`, chặn hoàn toàn việc rò rỉ dữ liệu giữa các case.

**Assignee:** Thành viên 5 (Data & Evidence Expert)
**Labels:** `core`, `logging`, `evidence`
