import os
from fastapi import UploadFile
from src.config.settings import settings


async def save_upload(file: UploadFile):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return file_path