from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    OtpDispatchResponse,
    OtpVerificationResponse,
    ResetPasswordRequest,
    SignupRequest,
    VerifyOtpRequest,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        token, user = service.signup(payload.name, payload.mobile, payload.password, payload.email)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        token, user = service.login(payload.mobile, payload.password)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me")
def me(current_user: CurrentUser):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "mobile": current_user.mobile,
    }


@router.post("/forgot-password", response_model=OtpDispatchResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        otp, otp_hint = service.request_password_reset(payload.identifier)
        return {
            "message": "OTP sent successfully",
            "otp_hint": f"Demo OTP: {otp} | Sent to {otp_hint}",
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/verify-reset-otp", response_model=OtpVerificationResponse)
def verify_reset_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        service.verify_password_reset_otp(payload.identifier, payload.otp)
        return {"message": "OTP verified successfully", "verified": True}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        service.reset_password(payload.identifier, payload.otp, payload.password)
        return {"message": "Password updated successfully"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
