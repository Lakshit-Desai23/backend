from decimal import Decimal

from app.core.security import get_password_hash
from app.database import SessionLocal
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.limit import Limit
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("Seed skipped: data already exists.")
            return

        admin = User(name="Riya Sharma", mobile="9999999991", password=get_password_hash("password123"))
        member = User(name="Aman Sharma", mobile="9999999992", password=get_password_hash("password123"))
        db.add_all([admin, member])
        db.flush()

        family = Family(name="Sharma Family", admin_id=admin.id)
        db.add(family)
        db.flush()

        db.add_all(
            [
                FamilyMember(family_id=family.id, user_id=admin.id, role="admin"),
                FamilyMember(family_id=family.id, user_id=member.id, role="member"),
            ]
        )

        wallet = Wallet(family_id=family.id, name="Main Family Wallet", balance=Decimal("8500.00"))
        db.add(wallet)
        db.flush()

        db.add(Limit(user_id=member.id, daily_limit=Decimal("1500.00"), monthly_limit=Decimal("15000.00")))
        db.add_all(
            [
                Transaction(wallet_id=wallet.id, user_id=admin.id, amount=Decimal("10000.00"), type="credit"),
                Transaction(wallet_id=wallet.id, user_id=member.id, amount=Decimal("1500.00"), type="debit"),
            ]
        )
        db.commit()
        print("Seed data created.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
