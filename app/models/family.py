from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    admin = relationship("User", back_populates="managed_families")
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    wallets = relationship("Wallet", back_populates="family", cascade="all, delete-orphan")
