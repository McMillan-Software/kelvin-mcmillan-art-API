import sys
import logging
from database import get_session
import service.user_service as user_service
import data_transfer_objects

# Silence passlib bcrypt warning
logging.getLogger('passlib').setLevel(logging.ERROR)

def create_user(username: str, password: str):
    
    print("Running create user script")

    session = next(get_session())

    try: 
        user_dto = data_transfer_objects.User(
            username=username,
            password=password
        )

        new_user = user_service.add_user(session, user_dto)
        print(f"User: '{new_user.username}' created successfully")
        return True
    
    except Exception as e: 
        print(f"Error creating user: {e}")
        return False
    

if __name__ == "__main__":
        if len(sys.argv) != 3:
             print("Usage: python create_user.py <username> <password>")
             sys.exit(1)

        username = sys.argv[1]
        password = sys.argv[2]

        create_user(username, password)