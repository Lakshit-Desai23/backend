from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    validate_password_length,
    verify_password,
)
from app.models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def signup(self, name: str, mobile: str, password: str) -> tuple[str, User]:
        validate_password_length(password)
        existing_user = self.db.query(User).filter(User.mobile == mobile).first()
        if existing_user:
            raise ValueError("Mobile number already registered")

        user = User(name=name, mobile=mobile, password=get_password_hash(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return create_access_token(str(user.id)), user

    def login(self, mobile: str, password: str) -> tuple[str, User]:
        validate_password_length(password)
        user = self.db.query(User).filter(User.mobile == mobile).first()
        if not user or not verify_password(password, user.password):
            raise ValueError("Invalid mobile or password")
        return create_access_token(str(user.id)), user

    def get_user_from_token(self, token: str) -> User | None:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except ValueError:
            return None

        if not user_id:
            return None
        return self.db.query(User).filter(User.id == int(user_id)).first()
