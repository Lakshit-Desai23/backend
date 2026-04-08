from decimal import Decimal

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session, joinedload

from app.models.family_member import FamilyMember
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def dashboard_summary(self, user: User) -> dict:
        family_ids = [
            row[0]
            for row in self.db.query(FamilyMember.family_id).filter(FamilyMember.user_id == user.id).all()
        ]
        if not family_ids:
            return {
                "total_balance": Decimal("0"),
                "wallets_count": 0,
                "members_count": 0,
                "total_income": Decimal("0"),
                "total_expense": Decimal("0"),
                "recent_transactions": [],
            }

        wallets = self.db.query(Wallet).filter(Wallet.family_id.in_(family_ids)).all()
        total_balance = sum((wallet.balance for wallet in wallets), Decimal("0"))

        transactions = (
            self.db.query(Transaction)
            .join(Wallet, Wallet.id == Transaction.wallet_id)
            .options(
                joinedload(Transaction.user),
                joinedload(Transaction.wallet),
                joinedload(Transaction.destination_wallet),
            )
            .filter(Wallet.family_id.in_(family_ids))
            .order_by(Transaction.created_at.desc())
            .limit(10)
            .all()
        )

        totals = (
            self.db.query(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Wallet, Wallet.id == Transaction.wallet_id)
            .filter(Wallet.family_id.in_(family_ids))
            .group_by(Transaction.type)
            .all()
        )

        income = Decimal("0")
        expense = Decimal("0")
        for txn_type, total in totals:
            if txn_type == "credit":
                income = Decimal(total)
            elif txn_type == "debit":
                expense = Decimal(total)

        members_count = (
            self.db.query(func.count(distinct(FamilyMember.user_id)))
            .filter(FamilyMember.family_id.in_(family_ids))
            .scalar()
        )

        return {
            "total_balance": total_balance,
            "wallets_count": len(wallets),
            "members_count": members_count or 0,
            "total_income": income,
            "total_expense": expense,
            "recent_transactions": transactions,
        }
