import string
import models
import schemas
from sqlalchemy.orm import Session
from fastapi import HTTPException
from utils.hashing import hash_password

def add_user(session: Session, user: schemas.User) -> models.User:
    print(f"Creating new user: {user.username}")

    # Check if the user already exists
    # Exploding on the line below.
    existing_user = session.query(models.User).filter_by(username=user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    print('User does not already exist')

    try:
        password_hash = hash_password(user.password)
    except Exception as e:
        print(f"Password hashing failed: {e}")
        raise HTTPException(status_code=500, detail="Password hashing failed")

    newUser = models.User(
        username = user.username,
        password_hash  = password_hash
    )

    session.add(newUser)
    print('new user added')
    session.commit()
    session.close()
    return newUser

def get_user(session: Session, username: string) -> models.User:
    print(f"Retrieving user: {username}")
    
    user = session.query(models.User).filter_by(username=username).first()

    if user is None:
        print(f"No user found with username: {username}")
        raise HTTPException(status_code=404, detail=f"No user found with username: {username}")
    
    return user 