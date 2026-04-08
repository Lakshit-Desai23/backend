from pydantic import BaseModel, Field, field_validator


class MessageResponse(BaseModel):
    message: str


class OtpDispatchResponse(MessageResponse):
    otp_hint: str


class OtpVerificationResponse(MessageResponse):
    verified: bool


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str | None = None
    mobile: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    mobile: str
    password: str


class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(min_length=4, max_length=255)


class VerifyOtpRequest(BaseModel):
    identifier: str = Field(min_length=4, max_length=255)
    otp: str = Field(min_length=4, max_length=6)

    @field_validator("otp")
    @classmethod
    def digits_only(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("OTP must contain digits only")
        return value


class ResetPasswordRequest(VerifyOtpRequest):
    password: str = Field(min_length=6, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    mobile: str

    class Config:
        from_attributes = True


class AuthResponse(TokenResponse):
    user: UserResponse
