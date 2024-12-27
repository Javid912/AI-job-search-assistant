"""
Configuration settings for the job search automation system.
"""

from typing import Dict, List, Any
import os

# Job Search Preferences
SEARCH_PREFERENCES = {
    "keywords": [
        "software engineer",
        "python developer",
        "full stack developer",
        "backend engineer"
    ],
    "locations": [
        "remote",
        "San Francisco, CA",
        "New York, NY"
    ],
    "job_types": [
        "full-time",
        "contract",
        "remote"
    ],
    "experience_levels": [
        "entry",
        "mid",
        "senior"
    ],
    "posted_within_days": 30,
    "exclude_companies": [],
    "preferred_companies": []
}

# Email Settings
EMAIL_CONFIG = {
    "sender_name": os.getenv("SENDER_NAME", ""),
    "sender_email": os.getenv("SENDER_EMAIL", ""),
    "signature": os.getenv("EMAIL_SIGNATURE", ""),
    "follow_up_days": 5,
    "max_follow_ups": 2,
    "templates_path": "./email_templates"
}

# Calendar Settings
CALENDAR_CONFIG = {
    "timezone": "America/New_York",
    "working_hours": {
        "start": "09:00",
        "end": "17:00"
    },
    "buffer_time": 30,  # Minutes before/after interviews
    "default_duration": 60,  # Default interview duration in minutes
    "calendar_id": "primary"
}

# Application Materials
MATERIALS_CONFIG = {
    "resume_path": os.getenv("RESUME_PATH", ""),
    "cover_letter_template": os.getenv("COVER_LETTER_TEMPLATE", ""),
    "portfolio_url": os.getenv("PORTFOLIO_URL", "")
}

# API Credentials
API_CREDENTIALS = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "gmail_credentials": os.getenv("GMAIL_CREDENTIALS", ""),
    "calendar_credentials": os.getenv("CALENDAR_CREDENTIALS", ""),
    "linkedin_api_key": os.getenv("LINKEDIN_API_KEY", ""),
    "glassdoor_api_key": os.getenv("GLASSDOOR_API_KEY", ""),
    "indeed_api_key": os.getenv("INDEED_API_KEY", "")
}

# Job Boards Configuration
JOB_BOARDS = {
    "linkedin": {
        "enabled": True,
        "search_url": "https://www.linkedin.com/jobs/search/",
        "api_enabled": bool(API_CREDENTIALS["linkedin_api_key"])
    },
    "glassdoor": {
        "enabled": True,
        "search_url": "https://www.glassdoor.com/Job/jobs.htm",
        "api_enabled": bool(API_CREDENTIALS["glassdoor_api_key"])
    },
    "indeed": {
        "enabled": True,
        "search_url": "https://www.indeed.com/jobs",
        "api_enabled": bool(API_CREDENTIALS["indeed_api_key"])
    },
    "company_websites": {
        "enabled": True,
        "target_companies": []  # List of company career page URLs
    }
}

# Storage Configuration
STORAGE_CONFIG = {
    "type": "postgresql",  # or "csv"
    "connection_string": os.getenv("DATABASE_URL", ""),
    "csv_directory": "./data",
    "backup_enabled": True,
    "backup_frequency": "daily"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "job_search.log",
    "max_size": 10485760,  # 10MB
    "backup_count": 5
}

# LLM Configuration
LLM_CONFIG = {
    "model": "gpt-4",
    "temperature": {
        "email_generation": 0.7,
        "information_extraction": 0.1,
        "scheduling": 0.3
    },
    "max_tokens": {
        "email_generation": 500,
        "information_extraction": 1000,
        "scheduling": 300
    }
}

# Application Status Tracking
STATUS_TRACKING = {
    "statuses": [
        "identified",
        "applied",
        "follow_up_sent",
        "response_received",
        "interview_scheduled",
        "interview_completed",
        "offer_received",
        "rejected",
        "accepted",
        "withdrawn"
    ],
    "auto_follow_up": True,
    "track_response_time": True
}

def load_config() -> Dict[str, Any]:
    """
    Load and validate configuration settings
    
    Returns:
        dict: Validated configuration settings
    """
    config = {
        "search_preferences": SEARCH_PREFERENCES,
        "email_config": EMAIL_CONFIG,
        "calendar_config": CALENDAR_CONFIG,
        "materials_config": MATERIALS_CONFIG,
        "api_credentials": API_CREDENTIALS,
        "job_boards": JOB_BOARDS,
        "storage_config": STORAGE_CONFIG,
        "logging_config": LOGGING_CONFIG,
        "llm_config": LLM_CONFIG,
        "status_tracking": STATUS_TRACKING
    }
    
    # Validate required environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "GMAIL_CREDENTIALS",
        "CALENDAR_CREDENTIALS",
        "SENDER_EMAIL",
        "RESUME_PATH"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return config

def update_config(section: str, updates: Dict[str, Any]) -> None:
    """
    Update configuration settings
    
    Args:
        section (str): Configuration section to update
        updates (dict): New values to apply
    """
    config = globals().get(section.upper())
    if config is None:
        raise ValueError(f"Invalid configuration section: {section}")
    
    if isinstance(config, dict):
        config.update(updates)
    else:
        raise ValueError(f"Configuration section {section} is not updateable")
