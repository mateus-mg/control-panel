from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.security import create_access_token, verify_admin_credentials
from app.api.schemas.auth import Token, UserLogin, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin) -> Token:
    """API endpoint for login - returns JWT token."""
    if not verify_admin_credentials(user_data.username, user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user_data.username}
    )
    return Token(access_token=access_token)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> dict:
    """API endpoint for logout."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user info."""
    return current_user