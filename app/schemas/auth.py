from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=6, max_length=20)


class LoginRequest(BaseModel):
    mobile: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    mobile: str

    class Config:
        from_attributes = True


class AuthResponse(TokenResponse):
    user: UserResponse
