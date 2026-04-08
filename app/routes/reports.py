from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.report import SummaryResponse
from app.services.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["reports"])


def _serialize_transaction(transaction):
    return {
        "id": transaction.id,
        "wallet_id": transaction.wallet_id,
        "destination_wallet_id": transaction.destination_wallet_id,
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "note": transaction.note,
        "created_at": transaction.created_at,
        "user_name": transaction.user.name if transaction.user else "",
        "wallet_name": transaction.wallet.name if transaction.wallet else "",
        "destination_wallet_name": (
            transaction.destination_wallet.name if transaction.destination_wallet else None
        ),
    }


@router.get("/summary", response_model=SummaryResponse)
def summary(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    data = ReportService(db).dashboard_summary(current_user)
    data["recent_transactions"] = [
        _serialize_transaction(transaction) for transaction in data["recent_transactions"]
    ]
    return data
