from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.transaction import SpendingLimitUpsert, TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService


router = APIRouter(prefix="/transactions", tags=["transactions"])


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


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        transaction = service.add_transaction(
            payload.wallet_id,
            payload.amount,
            payload.type,
            current_user,
            payload.destination_wallet_id,
            payload.note,
        )
        transaction.user = current_user
        return _serialize_transaction(transaction)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    current_user: CurrentUser,
    wallet_id: int = Query(...),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        transactions = service.list_transactions(wallet_id, current_user)
        return [_serialize_transaction(transaction) for transaction in transactions]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.put("/limits")
def upsert_limits(
    payload: SpendingLimitUpsert,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return TransactionService(db).upsert_limits(
        current_user,
        payload.daily_limit,
        payload.monthly_limit,
    )
