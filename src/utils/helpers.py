import os
from fastapi import UploadFile
from src.config.settings import settings


async def save_upload(file: UploadFile) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    dest = os.path.join(settings.upload_dir, file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())
    return dest
