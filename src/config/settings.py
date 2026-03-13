from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Document Verification Engine"
    debug: bool = False
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = ["pdf", "png", "jpg", "jpeg", "tiff"]
    ocr_language: str = "eng"

    class Config:
        env_file = ".env"


settings = Settings()
