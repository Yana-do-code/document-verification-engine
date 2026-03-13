from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Document Verification Engine"

    UPLOAD_DIR: str = "uploads"
    COMPRESSED_DIR: str = "uploads/compressed"

    IMAGE_MAX_WIDTH: int = 1600
    IMAGE_QUALITY: int = 70

    OCR_LANG: str = "en"

    class Config:
        env_file = ".env"


settings = Settings()