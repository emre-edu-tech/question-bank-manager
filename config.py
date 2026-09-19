import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "app.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
