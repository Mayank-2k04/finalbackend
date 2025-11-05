from fastapi import FastAPI, UploadFile, File, HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from schemas import User, UserLogin, ChatRequest
import querylogics
from functions import process_document
from auth import get_current_user
from datetime import datetime, timezone
from db import users
from bson import ObjectId
from typing import List,Dict,Any
from rag import summary, qabot

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
        "message": "Report added successfully to user"
    }

@app.get("/reports")
async def get_user_reports(current_user: dict = Depends(get_current_user)):
    try:
        user_object_id = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Find the user document
    user_doc = users.find_one({"_id": user_object_id}, {"reports": 1, "_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract only structured_data from each report
    reports = [
        report.get("structured_data", {})
        for report in user_doc.get("reports", [])
        if "structured_data" in report
    ]

    return {
        "user_email": current_user["user_email"],
        "report_history": reports
    }


@app.post("/analyze-blood-report")
async def analyze_blood_report(metrics: List[Dict[str, Any]]):
    try:
        if not metrics or len(metrics) == 0:
            raise HTTPException(status_code=400, detail="No metrics provided.")
        test_data = metrics[-1]
        suggestion = summary.get_suggestion(test_data)
        if isinstance(suggestion, (dict, list)):
            suggestion = "\n".join([str(v) for v in suggestion.values()]) if isinstance(suggestion,dict) else "\n".join(suggestion)
        return {"results":str(suggestion)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-blood-report")
async def chat_blood_report(
        request: ChatRequest,
        current_user: dict = Depends(get_current_user)
):
    try:
        print(f"[Chat] Request from user: {current_user['user_email']}")
        print(f"[Chat] Metrics received: {request.metrics}")
        print(f"[Chat] User question: {request.user_input}")

        if not request.metrics:
            raise HTTPException(status_code=400, detail="No metrics provided. Please upload a blood report first.")

        if not request.user_input or not request.user_input.strip():
            raise HTTPException(status_code=400, detail="No question provided. Please ask a question.")

        print("[Chat] Calling RAG chatbot...")
        response = qabot.chat_with_blood_ai(request.metrics, request.user_input)
        print(f"[Chat] RAG response length: {len(response)} characters")

        return {
            "response": response.replace("*",""),
            "status": "success"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Chat] Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/reports/analytics")
async def get_user_reports_with_analytics(current_user: dict = Depends(get_current_user)):
    try:
        user_object_id = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user_doc = users.find_one({"_id": user_object_id}, {"reports": 1, "_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    analytics_data = []
    for report in user_doc.get("reports", []):
        structured = report.get("structured_data", {})
        if not structured:
            continue

        metrics = []
        for key, value in structured.items():
            metrics.append({
                "name": key,
                "value": value,
            })

        analytics_data.append({
            "report_id": str(report.get("_id", ObjectId())),
            "filename": report.get("filename", "Unknown Report"),
            "date": report.get("uploaded_at", datetime.utcnow().isoformat()),
            "metrics": metrics
        })

    return {
        "user_email": current_user["user_email"],
        "analytics": analytics_data
    }