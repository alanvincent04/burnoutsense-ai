#!/usr/bin/env python3
"""
Authentication utilities: JWT generation, password hashing, user management.
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from pymongo import MongoClient

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 8))

db = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))["burnout_db"]


def generate_token(employee_id: str, role: str) -> str:
    """Generate a JWT token for authenticated sessions."""
    payload = {
        "sub": employee_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def authenticate_user(email: str, password: str) -> dict | None:
    """Authenticate a user and return a JWT token on success."""
    user = db.employees.find_one({"email": email})
    if not user or not verify_password(password, user.get("password_hash", "")):
        return None
    token = generate_token(user["employee_id"], user.get("role", "employee"))
    return {"token": token, "role": user.get("role"), "employee_id": user["employee_id"]}
