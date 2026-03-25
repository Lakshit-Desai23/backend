from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    wallet_id: int
    amount: Decimal = Field(gt=0)
    type: str = Field(pattern="^(credit|debit)$")


class TransactionResponse(BaseModel):
    id: int
    wallet_id: int
    user_id: int
    amount: Decimal
    type: str
    created_at: datetime
    user_name: str


class SpendingLimitUpsert(BaseModel):
    daily_limit: Decimal = Field(ge=0)
    monthly_limit: Decimal = Field(ge=0)
