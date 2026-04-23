from __future__ import annotations

import os


class Config:
    TESTING = False

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ai_visibility.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TIMEOUT_S = int(os.getenv("OPENAI_TIMEOUT_S", "30"))

    DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
    DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
    DATAFORSEO_TIMEOUT_S = int(os.getenv("DATAFORSEO_TIMEOUT_S", "30"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
