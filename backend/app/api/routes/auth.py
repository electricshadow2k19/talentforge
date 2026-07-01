from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import LoginRequest, TokenResponse, UserOut
from app.auth.deps import get_current_user
from app.auth.security import create_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.services.audit import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")
    token = create_access_token(str(user.id), {"role": user.role.value})
    log_activity(db, user, "login", "user", user.id)
    return TokenResponse(
        access_token=token,
        user=_user_out(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


def _user_out(user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return out
