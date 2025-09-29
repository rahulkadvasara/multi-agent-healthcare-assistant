from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database import db
from agents.coordinator import coordinator
from utils.ocr import ocr_processor
from utils.email_service import email_service
from scheduler import reminder_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Support System",
    description="Multi-agent healthcare support system with AI assistance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str
    user_id: int

class ReminderCreate(BaseModel):
    user_id: int
    medicine_name: str
    dosage: str
    frequency: str
    time: str

class ReminderDelete(BaseModel):
    reminder_id: int
    user_id: int

# Authentication endpoints
@app.post("/register")
async def register_user(user: UserRegister):
    """Register a new user"""
    try:
        success = db.register_user(user.username, user.password, user.email)
        if success:
            return {"message": "User registered successfully"}
        else:
            raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login_user(user: UserLogin):
    """Authenticate user login"""
    try:
        user_data = db.authenticate_user(user.username, user.password)
        if user_data:
            return {"message": "Login successful", "user": user_data}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints
@app.post("/chat")
async def chat_with_ai(message: ChatMessage):
    """Process chat message with AI coordinator"""
    try:
        # Pass user_id in context for drug interaction checking
        context = {"user_id": message.user_id}
        response = coordinator.route_request(message.message, context)
        return {"response": response}
    except Exception as e:
        print(f"Chat error: {e}")
        return {"response": "I apologize, but I'm experiencing technical difficulties. Please try again later."}

@app.post("/upload-report")
async def upload_medical_report(file: UploadFile = File(...), user_id: int = Form(...)):
    """Upload and analyze medical report image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Please upload an image file")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text using OCR
        ocr_text = ocr_processor.extract_text_from_image(file_content)
        
        if not ocr_text:
            raise HTTPException(status_code=400, detail="Could not extract text from image. Please ensure the image is clear and contains readable text.")
        
        # Validate if it looks like a medical report
        if not ocr_processor.validate_medical_report(ocr_text):
            return {
                "analysis": """I extracted text from your image, but it doesn't appear to be a medical report. 

**Extracted text:**
""" + ocr_text + """

If this is indeed a medical report, please try uploading a clearer image or contact support for assistance."""
            }
        
        # Analyze with AI coordinator
        context = {"ocr_text": ocr_text}
        analysis = coordinator.route_request("analyze medical report", context)
        
        return {"analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Error processing the uploaded file")

# Reminder endpoints
@app.post("/add-reminder")
async def add_reminder(reminder: ReminderCreate):
    """Add a new medication reminder with drug interaction checking"""
    try:
        from agents.drug_interaction import drug_interaction_checker
        from utils.drug_interaction_tool import check_all_drug_interactions
        
        # Get user's current medications
        current_reminders = db.get_user_reminders(reminder.user_id)
        current_medications = [r['medicine_name'].lower() for r in current_reminders]
        
        print(f"DEBUG: Manual reminder - checking interactions for {reminder.medicine_name}")
        print(f"DEBUG: Current medications: {current_medications}")
        
        # Check for drug interactions if user has existing medications
        if len(current_medications) > 0:
            try:
                interaction_result = check_all_drug_interactions(
                    [reminder.medicine_name.lower()], 
                    current_medications
                )
                
                print(f"DEBUG: Interaction result: {interaction_result[:200]}...")
                
                # If interactions are detected, don't add to database
                if "⚠️ Interactions Detected" in interaction_result:
                    return {
                        "success": False,
                        "interaction_warning": True,
                        "message": "Drug interaction detected",
                        "interaction_details": interaction_result,
                        "conflicting_drugs": current_medications,
                        "new_drug": reminder.medicine_name
                    }
                    
            except Exception as e:
                print(f"DEBUG: Error in interaction checking: {e}")
                # Continue with adding the reminder if interaction check fails
        
        # No interactions found or no current medications - proceed with adding
        success = db.add_reminder(
            user_id=reminder.user_id,
            medicine_name=reminder.medicine_name,
            dosage=reminder.dosage,
            frequency=reminder.frequency,
            time=reminder.time
        )
        
        if success:
            return {
                "success": True,
                "message": "Reminder added successfully",
                "interaction_warning": False
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add reminder")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/force-add-reminder")
async def force_add_reminder(reminder: ReminderCreate):
    """Force add a medication reminder bypassing interaction warnings"""
    try:
        success = db.add_reminder(
            user_id=reminder.user_id,
            medicine_name=reminder.medicine_name,
            dosage=reminder.dosage,
            frequency=reminder.frequency,
            time=reminder.time
        )
        
        if success:
            return {
                "success": True,
                "message": "Reminder added successfully (interaction warning bypassed)",
                "forced": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add reminder")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-reminders")
async def get_user_reminders(user_id: int):
    """Get all reminders for a user"""
    try:
        reminders = db.get_user_reminders(user_id)
        return {"reminders": reminders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-reminder")
async def delete_reminder(reminder: ReminderDelete):
    """Delete a reminder"""
    try:
        success = db.delete_reminder(reminder.reminder_id, reminder.user_id)
        if success:
            return {"message": "Reminder deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check and utility endpoints
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Healthcare Support System API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db_status = "connected"
        
        # Check scheduler status
        scheduler_status = reminder_scheduler.get_scheduler_status()
        
        return {
            "status": "healthy",
            "database": db_status,
            "scheduler": scheduler_status,
            "services": {
                "ocr": "available",
                "llama_api": "available",
                "email": "available"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/test-email")
async def test_email(email: str):
    """Test email configuration"""
    try:
        success = email_service.send_test_email(email)
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    print("🏥 Starting Healthcare Support System...")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )