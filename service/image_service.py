
from sqlalchemy import String
from fastapi import UploadFile

def upload_image(file: UploadFile, title: String) -> String:
    # save file to disk
    return "image_path" # return path to image file