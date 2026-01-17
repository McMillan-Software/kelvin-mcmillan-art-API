from datetime import datetime, timedelta, timezone
import jwt
import models
import os
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from service.user_service import get_user
from database import get_session
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login") 

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else: 
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(session: Session = Depends(get_session), token: str = Depends(oauth2_scheme)) -> models.User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing username",
            )
        print(f"Retrieving user: {username}")
        
        # Fetch the user from the database
        user = get_user(session, username)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
        
        return user
    except jwt.DecodeError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token signature",
        )
    

def refresh_tokens(refresh_token: str, session: Session) -> tuple[str, str]:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    except jwt.ExpiredSignatureError: 
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError: 
        raise HTTPException(status_code=401, detail="Invalid token")

    new_access_token = create_access_token({"sub": username})
    new_refresh_token = create_refresh_token({"sub": username})

    return new_access_token, new_refresh_token