from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Document Verification Engine"
    APP_ENV: str = "development"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    UPLOAD_DIR: str = "uploads"

    # Max width before downscaling; min is always enforced at 1000px in preprocessor
    IMAGE_MAX_WIDTH: int = 1600

    MAX_UPLOAD_SIZE_MB: int = 5

    OCR_LANG: str = "en"

    LOG_LEVEL: str = "INFO"

    # CORS — comma-separated origins. Set to your Vercel URL in production.
    CORS_ORIGINS: str = "*"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "doc_verification"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
