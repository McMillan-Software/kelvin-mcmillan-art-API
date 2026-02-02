
from sqlalchemy import String
from fastapi import UploadFile
from pathlib import Path
import boto3
import time
import re


def upload_image(file: UploadFile, title: String, painting_type: String) -> String:
    s3 = boto3.client('s3')
    file_name = generate_file_path(title, file.filename, painting_type)
    s3.upload_fileobj(file.file, 'kelvin-mcmillan-images', file_name)
    print(f"Sucessfully uploaded image to AWS with filename: {file_name}")
    return file_name


def generate_file_path(painting_title: String, original_filename: str, painting_type: String) -> str:
    file_extension = Path(original_filename).suffix.lower()

    filename = re.sub(r"[^a-zA-Z0-9_-]", "", painting_title)  # Remove unsafe chars
    filename = filename.lower().replace(" ", "-")  # Convert to lowercase and replace spaces
    kelvin = "Kelvin-McMillan-Art"
    timestamp = int(time.time())  
    safe_filename = f"{filename}-{kelvin}-{painting_type}-{timestamp}{file_extension}"

    return safe_filename