
from sqlalchemy import String
from fastapi import UploadFile
from pathlib import Path
import boto3
import time
import re


def upload_image(file: UploadFile, title: String) -> String:
    s3 = boto3.client('s3')
    file_name = generate_file_path(title, file.filename)
    s3.upload_fileobj(file.file, 'kelvin-mcmillan-images', file_name)
    return file_name


def generate_file_path(painting_title: String, original_filename: str) -> str:
    file_extension = Path(original_filename).suffix.lower()

    filename = re.sub(r"[^a-zA-Z0-9_-]", "", painting_title)  # Remove unsafe chars
    filename = filename.lower().replace(" ", "-")  # Convert to lowercase and replace spaces

    timestamp = int(time.time())  
    safe_filename = f"{filename}-{timestamp}{file_extension}"

    return safe_filename