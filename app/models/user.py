from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    managed_families = relationship("Family", back_populates="admin")
    family_memberships = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    created_groups = relationship("Group", back_populates="creator")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    paid_expenses = relationship("Expense", back_populates="payer")
    expense_splits = relationship("ExpenseSplit", back_populates="user", cascade="all, delete-orphan")
    sent_settlements = relationship("SettlementPayment", foreign_keys="SettlementPayment.from_user_id")
    received_settlements = relationship("SettlementPayment", foreign_keys="SettlementPayment.to_user_id")
    transactions = relationship("Transaction", back_populates="user")
    limit = relationship("Limit", back_populates="user", uselist=False, cascade="all, delete-orphan")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
