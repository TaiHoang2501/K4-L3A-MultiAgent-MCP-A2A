from __future__ import annotations

from typing import Any, List
from pydantic import BaseModel, Field

from .mcp_gateway import EvidenceGateway
from .trace import TraceWriter

# ============================================================================
# 1. CẤU TRÚC GIAO TIẾP A2A (Message Envelope) - Do Tài thiết kế
# ============================================================================
class MessageEnvelope(BaseModel):
    case_id: str
    sender: str
    receiver: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_refs_collected: List[str] = Field(default_factory=list)
    data_conflicts: List[dict[str, Any]] = Field(default_factory=list)
    turn_count: int = 0


# ============================================================================
# 2. CÁC HÀM STUB CHO CÁC SPECIALIST AGENTS (Để anh em đắp thịt vào)
# Lời khuyên: Sau này nên tách mỗi hàm này ra 1 file riêng, ví dụ agents/order_agent.py
# ============================================================================

async def call_order_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Dũng"""
    # TODO: Dũng viết logic parse payload, gọi model AI, gọi tool get_order...
    
    # Mô phỏng: Đánh dấu đã xử lý
    envelope.sender = "order_agent"
    return envelope

async def call_payment_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Long"""
    # TODO: Long viết logic kiểm tra tiền, gọi tool get_order_payments...
    envelope.sender = "payment_agent"
    return envelope

async def call_shipment_policy_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Quân"""
    # TODO: Quân viết logic kiểm tra giao hàng và chính sách...
    envelope.sender = "shipment_policy_agent"
    return envelope

async def call_verifier_agent(envelope: MessageEnvelope, trace: TraceWriter) -> dict[str, Any]:
    """Agent của anh Thắng"""
    # TODO: Thắng kiểm tra lại toàn bộ dữ liệu, lọc mảng evidence_refs_collected và xuất file JSON chuẩn.
    # Dưới đây là JSON fallback rỗng cho đỡ lỗi khi chạy thử:
    return {
        "primary_issue": "needs_investigation",
        "case_status": "needs_investigation",
        "confidence": 0.0,
        "affected_entities": {"buyer_id": None, "seller_id": None, "order_id": None, "shipment_tracking_id": None},
        "evidence_refs": envelope.evidence_refs_collected,
        "data_conflicts": envelope.data_conflicts,
    }


# ============================================================================
# 3. COORDINATOR WORKFLOW - Luồng chính (Tài phụ trách)
# ============================================================================
async def solve_case(
    case: dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> dict[str, Any]:
    """
    Luồng điều phối trung tâm của toàn hệ thống (Coordinator).
    """
    case_id = case.get("case_id", "UNKNOWN")
    
    # Emit trace log bắt đầu case
    trace.info("agent_started", {"case_id": case_id, "role": "coordinator"})
    
    # Khởi tạo Envelope mang dữ liệu gốc
    envelope = MessageEnvelope(
        case_id=case_id,
        sender="coordinator",
        receiver="order_agent",
        payload=case, 
    )
    
    try:
        # Bước 1: Giao cho Dũng (Order)
        trace.info("handoff", {"from": "coordinator", "to": "order_agent"})
        envelope = await call_order_agent(envelope, gateway, trace)
        
        # Bước 2: Giao cho Long (Payment)
        trace.info("handoff", {"from": "order_agent", "to": "payment_agent"})
        envelope = await call_payment_agent(envelope, gateway, trace)
        
        # Bước 3: Giao cho Quân (Shipment & Policy)
        trace.info("handoff", {"from": "payment_agent", "to": "shipment_policy_agent"})
        envelope = await call_shipment_policy_agent(envelope, gateway, trace)
        
        # Bước 4: Đẩy qua cho anh Thắng (Verifier) chốt sổ JSON
        trace.info("handoff", {"from": "shipment_policy_agent", "to": "verifier_agent"})
        final_output = await call_verifier_agent(envelope, trace)
        
        # Kết thúc thành công
        trace.info("handoff_completed", {"case_id": case_id})
        return final_output
        
    except Exception as e:
        # Xử lý nếu sập hệ thống (Bắt lỗi rớt mạng, lỗi LLM v.v.)
        trace.error("workflow_error", {"case_id": case_id, "error": str(e)})
        
        return {
            "primary_issue": "needs_investigation",
            "case_status": "action_required",
            "confidence": 0.0,
            "evidence_refs": [],
            "affected_entities": {"buyer_id": None, "seller_id": None, "order_id": None, "shipment_tracking_id": None},
        }
