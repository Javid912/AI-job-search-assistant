"""
FastAPI web application for the job search automation service.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError

from .tasks import start_job_search, check_application_status
from ..workflows.job_search import JobSearchWorkflow
from config import SEARCH_PREFERENCES

# Initialize FastAPI app
app = FastAPI(
    title="Job Search Automation API",
    description="API for automating job search workflows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "your-secret-key"  # TODO: Move to environment variable
ALGORITHM = "HS256"

# Pydantic models
class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class JobSearchPreferences(BaseModel):
    keywords: List[str]
    locations: List[str]
    job_types: List[str]
    experience_levels: List[str]
    posted_within_days: int = 30

class ApplicationStatus(BaseModel):
    job_title: str
    company: str
    status: str
    last_updated: datetime

# Authentication functions
def get_user(username: str):
    # TODO: Implement user database
    # This is a mock implementation
    return UserInDB(
        username=username,
        email=f"{username}@example.com",
        hashed_password="mock_hashed_password"
    )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# API endpoints
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement proper password verification
    access_token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow()},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/job-search/start")
async def start_new_job_search(
    preferences: JobSearchPreferences,
    current_user: User = Depends(get_current_user)
):
    """Start a new job search with given preferences"""
    try:
        task = start_job_search.delay(
            preferences.dict(),
            current_user.username
        )
        return {
            "task_id": task.id,
            "message": "Job search started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/job-search/status/{task_id}")
async def get_job_search_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a job search task"""
    task = start_job_search.AsyncResult(task_id)
    if task.ready():
        return {
            "status": "completed",
            "result": task.get()
        }
    return {
        "status": "in_progress",
        "info": task.info
    }

@app.get("/applications/status")
async def get_applications_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all job applications"""
    try:
        task = check_application_status.delay(current_user.username)
        result = task.get(timeout=10)
        return {
            "active_applications": result["active_applications"],
            "completed_applications": result["completed_applications"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/preferences/update")
async def update_search_preferences(
    preferences: JobSearchPreferences,
    current_user: User = Depends(get_current_user)
):
    """Update job search preferences"""
    try:
        # Update user-specific preferences in database
        # TODO: Implement database storage
        return {
            "message": "Preferences updated successfully",
            "preferences": preferences.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/applications/{application_id}")
async def get_application_details(
    application_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific application"""
    # TODO: Implement application details retrieval
    try:
        return {
            "application_id": application_id,
            "status": "pending",
            "details": {}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
