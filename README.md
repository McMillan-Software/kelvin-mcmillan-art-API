# Kelvin McMillan Art API 



## 🔧 First Time Setup Instructions

## 1. Create virtual environment and Activate (only first time)

   On Windows PowerShell:

   ``` powershell
   python -m venv venv 
   .\venv\Scripts\Activate.ps1
   ```

Terminal should look something like: 
    ```
    (venv) PS C:\Users\Angus\git\kelvin-mcmillan-art-API>
    ```
## 2. Install Dedpendencies (venv active)
```
    pip install -r requirements.txt
```

## venv and vscode

vscode should detect and offer to automatically link the venv to the project so you do not need to activate every time


### Running the Application locally: (venv active)
```
uvicorn main:app --reload
```


## Creating users: 

create users by running script

activate venv if not already:
```
source venv/bin/activate
```

```
python create_user_script.py <username> <password>
```

## Technologies

# see requirements.text

### API framework:
Fast API - https://fastapi.tiangolo.com/

### Server:
uvicorn - https://www.uvicorn.org/

### Database:
Sqlite - https://docs.python.org/3/library/sqlite3.html

### ORM:
pip install SQLAlchemy
SQLAlchemy - https://www.sqlalchemy.org/

### Hashing:
Passlib - https://passlib.readthedocs.io/en/stable/

### For form data - not 100% sure if this is needed but chatgpt said so... 
Passlib - https://passlib.readthedocs.io/en/stable/

### AWS:
pip install boto3
boto3 - https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
