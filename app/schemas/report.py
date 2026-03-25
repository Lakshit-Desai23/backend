from decimal import Decimal

from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class SummaryResponse(BaseModel):
    total_balance: Decimal
    wallets_count: int
    members_count: int
    total_income: Decimal
    total_expense: Decimal
    recent_transactions: list[TransactionResponse]
