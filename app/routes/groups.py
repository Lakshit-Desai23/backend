from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.group import BalanceSummaryResponse, ExpenseCreate, GroupCreate, GroupResponse, SettlementCreate
from app.services.group_service import GroupService


router = APIRouter(prefix="/groups", tags=["groups"])


def _serialize_group(group):
    return {
        "id": group.id,
        "name": group.name,
        "created_by": group.created_by,
        "members": [
            {
                "id": member.id,
                "user": {
                    "id": member.user.id,
                    "name": member.user.name,
                    "mobile": member.user.mobile,
                },
            }
            for member in group.members
        ],
        "expenses": [
            {
                "id": expense.id,
                "title": expense.title,
                "amount": expense.amount,
                "paid_by": expense.paid_by,
                "paid_by_name": expense.payer.name,
                "split_type": expense.split_type,
                "created_at": expense.created_at,
                "splits": [
                    {
                        "id": split.id,
                        "user_id": split.user_id,
                        "name": split.user.name,
                        "share_amount": split.share_amount,
                    }
                    for split in expense.splits
                ],
            }
            for expense in group.expenses
        ],
        "settlements": [
            {
                "id": payment.id,
                "from_user_id": payment.from_user_id,
                "from_user_name": payment.from_user.name,
                "to_user_id": payment.to_user_id,
                "to_user_name": payment.to_user.name,
                "amount": payment.amount,
                "settled_at": payment.settled_at,
            }
            for payment in group.settlements
        ],
    }


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        group = GroupService(db).create_group(
            payload.name,
            [member.mobile for member in payload.members],
            current_user,
        )
        return _serialize_group(group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[GroupResponse])
def list_groups(current_user: CurrentUser, db: Session = Depends(get_db)):
    groups = GroupService(db).list_groups(current_user)
    return [_serialize_group(group) for group in groups]


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        group = GroupService(db).get_group(group_id, current_user)
        return _serialize_group(group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{group_id}/expenses", response_model=GroupResponse)
def add_expense(group_id: int, payload: ExpenseCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        group = GroupService(db).add_expense(
            group_id,
            payload.title,
            payload.amount,
            payload.paid_by,
            payload.split_type,
            payload.split_between,
            [split.model_dump() for split in payload.splits],
            current_user,
        )
        return _serialize_group(group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{group_id}/balances", response_model=BalanceSummaryResponse)
def get_balances(group_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return GroupService(db).get_balances(group_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{group_id}/settlements", response_model=GroupResponse)
def settle_payment(
    group_id: int,
    payload: SettlementCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        group = GroupService(db).settle_payment(
            group_id,
            payload.from_user_id,
            payload.to_user_id,
            payload.amount,
            current_user,
        )
        return _serialize_group(group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
