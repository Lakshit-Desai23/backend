from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class GroupMemberCreate(BaseModel):
    mobile: str = Field(min_length=10, max_length=20)


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    members: list[GroupMemberCreate] = Field(default_factory=list)


class ExpenseSplitInput(BaseModel):
    user_id: int
    share_amount: Decimal = Field(gt=0)


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    amount: Decimal = Field(gt=0)
    paid_by: int
    split_type: str = Field(default="equal", pattern="^(equal|custom)$")
    split_between: list[int] = Field(min_length=1)
    splits: list[ExpenseSplitInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payload(self):
        if self.split_type == "custom" and not self.splits:
            raise ValueError("Custom split requires split amounts for each member")
        return self


class SettlementCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: Decimal = Field(gt=0)


class GroupUserResponse(BaseModel):
    id: int
    name: str
    mobile: str


class GroupMemberResponse(BaseModel):
    id: int
    user: GroupUserResponse


class ExpenseSplitResponse(BaseModel):
    id: int
    user_id: int
    name: str
    share_amount: Decimal


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: Decimal
    paid_by: int
    paid_by_name: str
    split_type: str
    created_at: datetime
    splits: list[ExpenseSplitResponse]


class SettlementResponse(BaseModel):
    id: int
    from_user_id: int
    from_user_name: str
    to_user_id: int
    to_user_name: str
    amount: Decimal
    settled_at: datetime


class GroupResponse(BaseModel):
    id: int
    name: str
    created_by: int
    members: list[GroupMemberResponse]
    expenses: list[ExpenseResponse] = Field(default_factory=list)
    settlements: list[SettlementResponse] = Field(default_factory=list)


class BalanceEntryResponse(BaseModel):
    from_user_id: int
    from_user_name: str
    to_user_id: int
    to_user_name: str
    amount: Decimal


class UserBalanceResponse(BaseModel):
    user_id: int
    name: str
    net_balance: Decimal
    status: str


class BalanceSummaryResponse(BaseModel):
    group_id: int
    balances: list[UserBalanceResponse]
    settlements: list[BalanceEntryResponse]
