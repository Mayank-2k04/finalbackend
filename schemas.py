from pydantic import BaseModel, EmailStr
from typing import Dict, Any

class User(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    metrics: Dict[str, Any]
    user_input: str