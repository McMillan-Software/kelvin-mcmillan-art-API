from fastapi import HTTPException, Depends, APIRouter

from database import get_session
from sqlalchemy.orm import Session

from utils.hashing import verify_password
from auth import create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

import schemas
import service.user_service as user_service
from models import User

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"],
)


#Authentication
@router.post("/login", response_model=schemas.Token)
def login(form_data: schemas.User, session: Session = Depends(get_session)):

    user = user_service.get_user(session, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")


    access_token = create_access_token(
         data={"sub": user.username}
     )
    return schemas.Token(access_token=access_token, token_type="bearer")


@router.post("/add-user", status_code=201)
def add_user_endpoint(user: schemas.User, 
                      session: Session = Depends(get_session)):
    """
    Add a new user to the database using the user_service.
    """
    try:
        new_user = user_service.add_user(session, user)
        return {"message": f"User {new_user.username} added successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/validate-authentication", status_code=200)
def validate_token(current_user: User = Depends(get_current_user)):
    """
    Validate the token and ensure the user is authenticated.
    """
    return {"message": "Token is valid", "username": current_user.username}