from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.wallet import WalletCreate, WalletResponse
from app.services.wallet_service import WalletService


router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(
    payload: WalletCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        return WalletService(db).create_wallet(
            payload.family_id,
            payload.name,
            payload.balance,
            current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("", response_model=list[WalletResponse])
def list_wallets(
    current_user: CurrentUser,
    family_id: int = Query(...),
    db: Session = Depends(get_db),
):
    try:
        return WalletService(db).list_wallets(family_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
