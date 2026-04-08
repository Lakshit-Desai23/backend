from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    wallet_id: int
    destination_wallet_id: int | None = None
    amount: Decimal = Field(gt=0)
    type: str = Field(pattern="^(credit|debit|transfer)$")
    note: str | None = Field(default=None, max_length=255)


class TransactionResponse(BaseModel):
    id: int
    wallet_id: int
    destination_wallet_id: int | None = None
    user_id: int
    amount: Decimal
    type: str
    note: str | None = None
    created_at: datetime
    user_name: str
    wallet_name: str
    destination_wallet_name: str | None = None


class SpendingLimitUpsert(BaseModel):
    daily_limit: Decimal = Field(ge=0)
    monthly_limit: Decimal = Field(ge=0)
