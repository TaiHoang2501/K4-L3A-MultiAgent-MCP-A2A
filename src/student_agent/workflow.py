from __future__ import annotations

from typing import Any, List
from pydantic import BaseModel, Field

from .mcp_gateway import EvidenceGateway
from .trace import TraceWriter


class MessageEnvelope(BaseModel):
    case_id: str
    sender: str
    receiver: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_refs_collected: List[str] = Field(default_factory=list)
    data_conflicts: List[dict[str, Any]] = Field(default_factory=list)
    turn_count: int = 0



async def call_order_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Dũng"""
   
    envelope.sender = "order_agent"
    return envelope

async def call_payment_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Long"""
  
    envelope.sender = "payment_agent"
    return envelope

async def call_shipment_policy_agent(envelope: MessageEnvelope, gateway: EvidenceGateway, trace: TraceWriter) -> MessageEnvelope:
    """Agent của Quân"""

    envelope.sender = "shipment_policy_agent"
    return envelope

async def call_verifier_agent(envelope: MessageEnvelope, trace: TraceWriter) -> dict[str, Any]:
    return {
        "primary_issue": "needs_investigation",
        "case_status": "needs_investigation",
        "confidence": 0.0,
        "affected_entities": {"buyer_id": None, "seller_id": None, "order_id": None, "shipment_tracking_id": None},
        "evidence_refs": envelope.evidence_refs_collected,
        "data_conflicts": envelope.data_conflicts,
    }

async def solve_case(
    case: dict[str, Any], gateway: EvidenceGateway, trace: TraceWriter
) -> dict[str, Any]:
    """
    Luồng điều phối trung tâm của toàn hệ thống (Coordinator).
    """
    case_id = case.get("case_id", "UNKNOWN")
    

    trace.emit(case_id=case_id, event_type="agent_started", actor="coordinator")
    
    envelope = MessageEnvelope(
        case_id=case_id,
        sender="coordinator",
        receiver="order_agent",
        payload=case, 
    )
    
    try:
        trace.emit(case_id=case_id, event_type="handoff", actor="coordinator", target="order_agent")
        envelope = await call_order_agent(envelope, gateway, trace)
        
        trace.emit(case_id=case_id, event_type="handoff", actor="order_agent", target="payment_agent")
        envelope = await call_payment_agent(envelope, gateway, trace)
        
        trace.emit(case_id=case_id, event_type="handoff", actor="payment_agent", target="shipment_policy_agent")
        envelope = await call_shipment_policy_agent(envelope, gateway, trace)
        
        trace.emit(case_id=case_id, event_type="handoff", actor="shipment_policy_agent", target="verifier_agent")
        final_output = await call_verifier_agent(envelope, trace)
        
        trace.emit(case_id=case_id, event_type="handoff_completed", actor="coordinator")
        return final_output
        
    except Exception as e:
        trace.emit(case_id=case_id, event_type="workflow_error", actor="coordinator", attributes={"error": str(e)})
        
        return {
            "primary_issue": "needs_investigation",
            "case_status": "action_required",
            "confidence": 0.0,
            "evidence_refs": [],
            "affected_entities": {"buyer_id": None, "seller_id": None, "order_id": None, "shipment_tracking_id": None},
        }
