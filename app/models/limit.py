from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Limit(Base):
    __tablename__ = "limits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    user = relationship("User", back_populates="limit")
