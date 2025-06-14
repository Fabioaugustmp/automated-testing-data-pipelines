# app/core/config.py

class Settings:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./transactions.db"

settings = Settings()