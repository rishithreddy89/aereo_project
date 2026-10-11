from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "cert_user"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "certificate_db"

    STORAGE_DIR: str = "./certificates"
    MAX_RECIPIENTS_PER_JOB: int = 500
    WORKER_POLL_INTERVAL: int = 5

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
