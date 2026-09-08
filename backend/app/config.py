from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://paimonitor:paimonitor@db:5432/paimonitor"

    # --- Auth ---
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # --- AWS S3 (device image ingestion) ---
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    s3_bucket: str = "paimonitor-trap-images"
    # SQS queue that receives S3 "ObjectCreated" event notifications.
    # This is how the backend learns a new image has landed, without polling.
    s3_event_queue_url: str = ""

    # --- ML ---
    model_weights_path: str = "/app/app/ml/weights/insect_detector.pt"
    detection_confidence: float = 0.35

    class Config:
        env_file = ".env"


settings = Settings()
