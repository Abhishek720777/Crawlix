import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        # Check if username or email already exists
        existing_user_query = select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
        result = await db.execute(existing_user_query)
        existing_user = result.scalars().first()
        
        if existing_user:
            if existing_user.email == user_in.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this username already exists."
                )

        # Create new user
        new_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_admin=False
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Generate JWT token
        access_token = create_access_token(data={"sub": new_user.id, "username": new_user.username})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        query = select(User).where(
            (User.email == user_in.username_or_email) | (User.username == user_in.username_or_email)
        )
        result = await db.execute(query)
        user = result.scalars().first()

        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated."
            )

        access_token = create_access_token(data={"sub": user.id, "username": user.username})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )
