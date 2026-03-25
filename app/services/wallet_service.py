from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.user import User
from app.models.wallet import Wallet


class WalletService:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, family_id: int, name: str, balance: Decimal, user: User) -> Wallet:
        self._ensure_family_access(family_id, user.id)
        wallet = Wallet(family_id=family_id, name=name, balance=balance)
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def list_wallets(self, family_id: int, user: User) -> list[Wallet]:
        self._ensure_family_access(family_id, user.id)
        return (
            self.db.query(Wallet)
            .filter(Wallet.family_id == family_id)
            .order_by(Wallet.id.desc())
            .all()
        )

    def _ensure_family_access(self, family_id: int, user_id: int) -> Family:
        family = self.db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise ValueError("Family not found")

        membership = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
            .first()
        )
        if not membership:
            raise PermissionError("You do not belong to this family")
        return family
