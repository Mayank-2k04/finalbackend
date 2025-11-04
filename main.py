from fastapi import FastAPI, UploadFile, File, HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from schemas import User, UserLogin
import querylogics
from functions import process_document
from auth import get_current_user
from datetime import datetime, timezone
from db import users
from bson import ObjectId

app = FastAPI(title="Campus Safety & Item Recovery")

app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])


@app.post("/signup")
def signup(user: User):
    return querylogics.signup(user)

@app.post("/login")
def login(user: UserLogin):
    return querylogics.login(user)

@app.post("/extract")
async def extract_lab_report(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    if not file.filename.lower().endswith(('.png', '.pdf')):
        raise HTTPException(status_code=400, detail="File must be PNG or PDF")

    file_bytes = await file.read()
    structured_data = process_document(file_bytes)

    # Build the report object
    report_obj = {
        "report_id": str(datetime.now(timezone.utc).timestamp()),  # unique key
        "filename": file.filename,
        "uploaded_at": datetime.now(timezone.utc),
        "structured_data": structured_data
    }

    # Add the report to the user's reports array
    result = users.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$push": {"reports": report_obj}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "Report added successfully to user",
        "report": report_obj
    }

# @app.get("/homepage")
# def homepage(current_user: dict = Depends(get_current_user)):
#     return current_user