"""
Job Collector Agent
Responsible for collecting job postings from various platforms and sources.
"""

from phi.agent import Agent
from phi.tools.web import WebScrapingTool
from phi.tools.api import APIRequestTool

class JobCollectorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="job_collector",
            description="Collects job postings from various platforms",
            tools=[
                WebScrapingTool(
                    allowed_domains=[
                        "linkedin.com",
                        "glassdoor.com",
                        "indeed.com",
                        "google.com/jobs"
                    ]
                ),
                APIRequestTool(
                    base_urls=[
                        "https://api.linkedin.com",
                        "https://api.glassdoor.com",
                        "https://api.indeed.com"
                    ]
                )
            ],
            knowledge_base="job_search_patterns"
        )
        
        # Configure agent-specific settings
        self.search_preferences = {
            "keywords": [],
            "locations": [],
            "job_types": ["full-time", "contract", "remote"],
            "experience_levels": ["entry", "mid", "senior"],
            "posted_within_days": 30
        }
    
    async def search_jobs(self, criteria):
        """
        Search for jobs based on given criteria
        
        Args:
            criteria (dict): Job search criteria including:
                - keywords (list): List of job-related keywords
                - locations (list): Desired job locations
                - job_types (list): Types of jobs to search for
                - experience_levels (list): Required experience levels
        
        Returns:
            list: Collection of job postings matching the criteria
        """
        # Update search preferences with provided criteria
        self.search_preferences.update(criteria)
        
        # Execute job search across platforms
        jobs = await self.run(
            task="Search for jobs matching criteria",
            context={
                "search_preferences": self.search_preferences,
                "platforms": ["LinkedIn", "Glassdoor", "Indeed", "Google Jobs"]
            }
        )
        
        return jobs
    
    async def validate_posting(self, job_posting):
        """
        Validate a job posting for completeness and relevance
        
        Args:
            job_posting (dict): Job posting data to validate
        
        Returns:
            tuple: (bool, str) - (is_valid, reason)
        """
        required_fields = [
            "title",
            "company",
            "location",
            "description",
            "requirements",
            "posting_date"
        ]
        
        # Check for required fields
        missing_fields = [field for field in required_fields if field not in job_posting]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate posting date is within preferences
        if not self._is_posting_recent(job_posting["posting_date"]):
            return False, "Posting is too old"
        
        return True, "Valid posting"
    
    def _is_posting_recent(self, posting_date):
        """Check if the posting date is within the preferred time range"""
        from datetime import datetime, timedelta
        
        post_date = datetime.fromisoformat(posting_date)
        cutoff_date = datetime.now() - timedelta(days=self.search_preferences["posted_within_days"])
        
        return post_date >= cutoff_date
