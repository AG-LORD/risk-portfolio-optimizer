import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:1004@localhost:5432/risk_portfolio_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "super_secret_jwt_key"