from fastapi import HTTPException, Depends, APIRouter

from database import get_session
from sqlalchemy.orm import Session

from utils.hashing import verify_password
from auth import create_access_token, create_refresh_token, get_current_user, refresh_tokens
from fastapi.security import OAuth2PasswordRequestForm

import data_transfer_objects
import service.user_service as user_service
from models import User

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"],
)


#Authentication
@router.post("/login", response_model=data_transfer_objects.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):

    user = user_service.get_user(session, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")


    access_token = create_access_token(
         data={"sub": user.username}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )

    return data_transfer_objects.Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


# @router.post("/add-user", status_code=201)
# def add_user_endpoint(user: data_transfer_objects.User, 
#                       session: Session = Depends(get_session),
#                       current_user: User = Depends(get_current_user)):
#     """
#     Add a new user to the database using the user_service.
#     """
#     print(f"Adding new user: {user.username} by user: {current_user.username}")

#     try:
#         new_user = user_service.add_user(session, user)
#         return {"message": f"User {new_user.username} added successfully."}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/validate-authentication", status_code=200)
def validate_token(current_user: User = Depends(get_current_user)):
    """
    Validate the token and ensure the user is authenticated.
    """
    return {"message": "Token is valid", "username": current_user.username}


@router.post("/refresh", response_model=data_transfer_objects.Token)
def refresh_token(request: data_transfer_objects.RefreshTokenRequest, session: Session = Depends(get_session)):
    """
    Issue a new token set from a refresh token
    """
    access_token, refresh_token = refresh_tokens(request.refresh_token, session)

    return data_transfer_objects.Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )



    