import os
import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass


PORTONE_API_URL = "https://api.portone.io"
PORTONE_API_SECRET = os.getenv("PORTONE_API_SECRET", "")


@dataclass
class PaymentRequest:
    payment_id: str
    order_name: str
    amount: int
    currency: str = "KRW"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


@dataclass
class PaymentResult:
    payment_id: str
    status: str
    amount: int
    paid_at: Optional[str] = None
    message: Optional[str] = None


class PortOnePaymentService:
    """포트원 V2 결제 서비스 스켈레톤."""

    def __init__(self):
        self.api_secret = PORTONE_API_SECRET
        self.base_url = PORTONE_API_URL

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"PortOne {self.api_secret}",
            "Content-Type": "application/json",
        }

    async def create_payment(self, req: PaymentRequest) -> Dict[str, Any]:
        """결제 요청 생성 (프론트엔드에서 SDK 호출 전 서버 사이드 준비)."""
        # 실제 구현 시 포트원 SDK 또는 API 호출
        return {
            "payment_id": req.payment_id,
            "order_name": req.order_name,
            "amount": req.amount,
            "currency": req.currency,
            "status": "pending",
            "message": "결제 준비 완료. 프론트엔드에서 포트원 SDK로 결제를 진행하세요.",
        }

    async def verify_payment(self, payment_id: str) -> PaymentResult:
        """결제 검증 - 포트원 서버에서 결제 상태 조회."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/payments/{payment_id}",
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return PaymentResult(
                        payment_id=payment_id,
                        status=data.get("status", "unknown"),
                        amount=data.get("amount", {}).get("total", 0),
                        paid_at=data.get("paidAt"),
                    )
                else:
                    return PaymentResult(
                        payment_id=payment_id,
                        status="error",
                        amount=0,
                        message=f"API 오류: {response.status_code}",
                    )
            except Exception as e:
                return PaymentResult(
                    payment_id=payment_id,
                    status="error",
                    amount=0,
                    message=str(e),
                )

    async def cancel_payment(
        self,
        payment_id: str,
        reason: str,
        amount: Optional[int] = None,
    ) -> Dict[str, Any]:
        """결제 취소 (전체 또는 부분 취소)."""
        payload: Dict[str, Any] = {"reason": reason}
        if amount is not None:
            payload["cancel_amount"] = amount

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/payments/{payment_id}/cancel",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0,
                )
                return {
                    "payment_id": payment_id,
                    "status": "cancelled" if response.status_code == 200 else "error",
                    "data": response.json() if response.status_code == 200 else {},
                }
            except Exception as e:
                return {"payment_id": payment_id, "status": "error", "message": str(e)}

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """포트원 웹훅 처리."""
        event_type = payload.get("type", "")
        payment_id = payload.get("data", {}).get("paymentId", "")

        if event_type == "Transaction.Paid":
            result = await self.verify_payment(payment_id)
            return {
                "event": event_type,
                "payment_id": payment_id,
                "verified": result.status == "PAID",
                "amount": result.amount,
            }
        elif event_type == "Transaction.Cancelled":
            return {"event": event_type, "payment_id": payment_id, "status": "cancelled"}
        else:
            return {"event": event_type, "payment_id": payment_id, "status": "unhandled"}
