from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.family import FamilyCreate, FamilyMemberAdd, FamilyResponse
from app.services.family_service import FamilyService


router = APIRouter(prefix="/families", tags=["families"])


def _serialize_family(family):
    return {
        "id": family.id,
        "name": family.name,
        "admin_id": family.admin_id,
        "members": [
            {
                "id": member.id,
                "role": member.role,
                "user_id": member.user_id,
                "name": member.user.name,
                "mobile": member.user.mobile,
            }
            for member in family.members
        ],
    }


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
def create_family(
    payload: FamilyCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = FamilyService(db)
    family = service.create_family(payload.name, current_user)
    return _serialize_family(family)


@router.post("/{family_id}/members", response_model=FamilyResponse)
def add_member(
    family_id: int,
    payload: FamilyMemberAdd,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = FamilyService(db)
    try:
        family = service.add_member(family_id, payload.mobile, payload.role, current_user)
        return _serialize_family(family)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("", response_model=list[FamilyResponse])
def list_families(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    families = FamilyService(db).list_user_families(current_user)
    return [_serialize_family(family) for family in families]
