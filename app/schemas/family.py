from pydantic import BaseModel, Field


class FamilyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class FamilyMemberAdd(BaseModel):
    mobile: str
    role: str = Field(default="member", max_length=50)


class FamilyMemberResponse(BaseModel):
    id: int
    role: str
    user_id: int
    name: str
    mobile: str


class FamilyResponse(BaseModel):
    id: int
    name: str
    admin_id: int
    members: list[FamilyMemberResponse]
