from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.family_member import FamilyMember
from app.models.limit import Limit
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def add_transaction(self, wallet_id: int, amount: Decimal, txn_type: str, user: User) -> Transaction:
        wallet = self._get_wallet_with_access(wallet_id, user.id)

        if txn_type == "debit":
            self._validate_limits(user.id, amount)
            if wallet.balance < amount:
                raise ValueError("Insufficient wallet balance")
            wallet.balance -= amount
        else:
            wallet.balance += amount

        transaction = Transaction(wallet_id=wallet.id, user_id=user.id, amount=amount, type=txn_type)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def list_transactions(self, wallet_id: int, user: User) -> list[Transaction]:
        self._get_wallet_with_access(wallet_id, user.id)
        return (
            self.db.query(Transaction)
            .options(joinedload(Transaction.user))
            .filter(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .all()
        )

    def upsert_limits(self, user: User, daily_limit: Decimal, monthly_limit: Decimal) -> Limit:
        limit = self.db.query(Limit).filter(Limit.user_id == user.id).first()
        if not limit:
            limit = Limit(user_id=user.id, daily_limit=daily_limit, monthly_limit=monthly_limit)
            self.db.add(limit)
        else:
            limit.daily_limit = daily_limit
            limit.monthly_limit = monthly_limit

        self.db.commit()
        self.db.refresh(limit)
        return limit

    def _validate_limits(self, user_id: int, amount: Decimal) -> None:
        limit = self.db.query(Limit).filter(Limit.user_id == user_id).first()
        if not limit:
            return

        now = datetime.now(timezone.utc)
        day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        daily_spend = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "debit",
                Transaction.created_at >= day_start,
            )
            .scalar()
        )
        monthly_spend = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "debit",
                Transaction.created_at >= month_start,
            )
            .scalar()
        )

        if limit.daily_limit and Decimal(daily_spend) + amount > limit.daily_limit:
            raise ValueError("Daily spending limit exceeded")
        if limit.monthly_limit and Decimal(monthly_spend) + amount > limit.monthly_limit:
            raise ValueError("Monthly spending limit exceeded")

    def _get_wallet_with_access(self, wallet_id: int, user_id: int) -> Wallet:
        wallet = self.db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise ValueError("Wallet not found")

        membership = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == wallet.family_id, FamilyMember.user_id == user_id)
            .first()
        )
        if not membership:
            raise PermissionError("You do not have access to this wallet")
        return wallet
