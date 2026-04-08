import re
from datetime import datetime, timedelta, timezone
from random import SystemRandom

from sqlalchemy import false, or_
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    validate_password_length,
    verify_password,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self._otp_random = SystemRandom()

    def signup(self, name: str, mobile: str, password: str, email: str | None = None) -> tuple[str, User]:
        validate_password_length(password)
        normalized_mobile = mobile.strip()
        normalized_email = self._normalize_email(email)

        existing_user = (
            self.db.query(User)
            .filter(
                or_(
                    User.mobile == normalized_mobile,
                    User.email == normalized_email if normalized_email else false(),
                )
            )
            .first()
        )
        if existing_user:
            if existing_user.mobile == normalized_mobile:
                raise ValueError("Mobile number already registered")
            raise ValueError("Email already registered")

        user = User(
            name=name.strip(),
            email=normalized_email,
            mobile=normalized_mobile,
            password=get_password_hash(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return create_access_token(str(user.id)), user

    def login(self, mobile: str, password: str) -> tuple[str, User]:
        validate_password_length(password)
        user = self.db.query(User).filter(User.mobile == mobile.strip()).first()
        if not user or not verify_password(password, user.password):
            raise ValueError("Invalid mobile or password")
        return create_access_token(str(user.id)), user

    def request_password_reset(self, identifier: str) -> tuple[str, str]:
        normalized_identifier = self._normalize_identifier(identifier)
        user = self._find_user_by_identifier(normalized_identifier)
        if not user:
            raise ValueError("No user found with that email or mobile")

        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).delete(synchronize_session=False)

        otp_code = f"{self._otp_random.randint(0, 999999):06d}"
        token = PasswordResetToken(
            user_id=user.id,
            identifier=normalized_identifier,
            otp_code=otp_code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        self.db.add(token)
        self.db.commit()
        return otp_code, self._obfuscate_identifier(normalized_identifier)

    def verify_password_reset_otp(self, identifier: str, otp: str) -> None:
        token = self._get_active_reset_token(identifier, otp)
        token.verified_at = datetime.now(timezone.utc)
        self.db.add(token)
        self.db.commit()

    def reset_password(self, identifier: str, otp: str, password: str) -> None:
        validate_password_length(password)
        token = self._get_active_reset_token(identifier, otp)
        if token.verified_at is None:
            raise ValueError("Verify the OTP before setting a new password")

        token.user.password = get_password_hash(password)
        token.used_at = datetime.now(timezone.utc)
        self.db.add(token.user)
        self.db.add(token)
        self.db.commit()

    def get_user_from_token(self, token: str) -> User | None:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except ValueError:
            return None

        if not user_id:
            return None
        return self.db.query(User).filter(User.id == int(user_id)).first()

    def _find_user_by_identifier(self, identifier: str) -> User | None:
        if "@" in identifier:
            return self.db.query(User).filter(User.email == identifier).first()
        return self.db.query(User).filter(User.mobile == identifier).first()

    def _get_active_reset_token(self, identifier: str, otp: str) -> PasswordResetToken:
        normalized_identifier = self._normalize_identifier(identifier)
        token = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.identifier == normalized_identifier,
                PasswordResetToken.otp_code == otp.strip(),
                PasswordResetToken.used_at.is_(None),
            )
            .order_by(PasswordResetToken.id.desc())
            .first()
        )
        if not token:
            raise ValueError("Invalid OTP")
        if token.expires_at < datetime.now(timezone.utc):
            raise ValueError("OTP has expired")
        return token

    def _normalize_email(self, email: str | None) -> str | None:
        if not email:
            return None
        normalized_email = email.strip().lower()
        if not EMAIL_REGEX.match(normalized_email):
            raise ValueError("Enter a valid email address")
        return normalized_email

    def _normalize_identifier(self, identifier: str) -> str:
        normalized_identifier = identifier.strip().lower()
        if "@" in normalized_identifier and not EMAIL_REGEX.match(normalized_identifier):
            raise ValueError("Enter a valid email address")
        return normalized_identifier

    def _obfuscate_identifier(self, identifier: str) -> str:
        if "@" in identifier:
            name, domain = identifier.split("@", 1)
            safe_name = f"{name[:2]}***" if len(name) > 2 else "***"
            return f"{safe_name}@{domain}"
        return f"***{identifier[-4:]}"
