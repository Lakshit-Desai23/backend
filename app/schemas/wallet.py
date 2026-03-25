from decimal import Decimal

from pydantic import BaseModel, Field


class WalletCreate(BaseModel):
    family_id: int
    name: str = Field(min_length=2, max_length=120)
    balance: Decimal = Decimal("0.00")


class WalletResponse(BaseModel):
    id: int
    family_id: int
    name: str
    balance: Decimal

    class Config:
        from_attributes = True
