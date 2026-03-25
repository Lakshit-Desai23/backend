from sqlalchemy.orm import Session, joinedload

from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.user import User


class FamilyService:
    def __init__(self, db: Session):
        self.db = db

    def create_family(self, name: str, admin: User) -> Family:
        family = Family(name=name, admin_id=admin.id)
        self.db.add(family)
        self.db.flush()

        self.db.add(FamilyMember(family_id=family.id, user_id=admin.id, role="admin"))
        self.db.commit()
        return self._get_family_with_members(family.id)

    def add_member(self, family_id: int, mobile: str, role: str, requester: User) -> Family:
        family = self._get_family_with_members(family_id)
        if not family:
            raise ValueError("Family not found")
        if family.admin_id != requester.id:
            raise PermissionError("Only family admin can add members")

        user = self.db.query(User).filter(User.mobile == mobile).first()
        if not user:
            raise ValueError("User with the provided mobile number does not exist")

        existing = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user.id)
            .first()
        )
        if existing:
            raise ValueError("User is already a family member")

        self.db.add(FamilyMember(family_id=family_id, user_id=user.id, role=role))
        self.db.commit()
        return self._get_family_with_members(family_id)

    def list_user_families(self, user: User) -> list[Family]:
        return (
            self.db.query(Family)
            .join(FamilyMember, FamilyMember.family_id == Family.id)
            .options(joinedload(Family.members).joinedload(FamilyMember.user))
            .filter(FamilyMember.user_id == user.id)
            .all()
        )

    def get_family_with_members(self, family_id: int) -> Family | None:
        return self._get_family_with_members(family_id)

    def _get_family_with_members(self, family_id: int) -> Family | None:
        return (
            self.db.query(Family)
            .options(joinedload(Family.members).joinedload(FamilyMember.user))
            .filter(Family.id == family_id)
            .first()
        )
