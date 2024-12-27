"""
Job Search Workflow
Coordinates the job search automation process using multiple agents.
"""

from phi.workflow import Workflow
from datetime import datetime
from typing import List, Dict, Any

from ..agents import (
    JobCollectorAgent,
    InformationExtractorAgent,
    EmailAgent,
    SchedulerAgent
)

class JobSearchWorkflow(Workflow):
    def __init__(self):
        # Initialize agents
        self.job_collector = JobCollectorAgent()
        self.info_extractor = InformationExtractorAgent()
        self.email_agent = EmailAgent()
        self.scheduler = SchedulerAgent()
        
        # Workflow state
        self.active_applications = []
        self.completed_applications = []
        
        super().__init__(
            name="job_search_automation",
            description="Automates the job search process from finding positions to scheduling interviews",
            agents=[
                self.job_collector,
                self.info_extractor,
                self.email_agent,
                self.scheduler
            ]
        )
    
    async def run_job_search(self, search_criteria: Dict[str, Any]):
        """
        Execute the complete job search workflow
        
        Args:
            search_criteria (dict): Job search parameters including:
                - keywords (list): Job-related keywords
                - locations (list): Desired locations
                - job_types (list): Types of positions
                - experience_levels (list): Required experience levels
        """
        # Step 1: Collect job postings
        job_postings = await self._collect_jobs(search_criteria)
        
        # Step 2: Process and filter postings
        processed_jobs = await self._process_jobs(job_postings)
        
        # Step 3: Apply to positions
        for job in processed_jobs:
            await self._apply_to_job(job)
        
        # Step 4: Set up monitoring for responses
        await self._setup_response_monitoring()
        
        return {
            "jobs_found": len(job_postings),
            "jobs_processed": len(processed_jobs),
            "applications_sent": len(self.active_applications)
        }
    
    async def check_application_status(self):
        """Check status of all active applications and handle responses"""
        # Check for new responses
        responses = await self.email_agent.check_responses()
        
        for response in responses:
            await self._handle_application_response(response)
        
        # Send follow-ups if needed
        await self._process_follow_ups()
        
        return {
            "new_responses": len(responses),
            "active_applications": len(self.active_applications),
            "completed_applications": len(self.completed_applications)
        }
    
    async def _collect_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect job postings based on search criteria"""
        jobs = await self.job_collector.search_jobs(criteria)
        
        # Log the search results
        self.log.info(f"Found {len(jobs)} potential job postings")
        
        return jobs
    
    async def _process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and structure job posting data"""
        processed_jobs = []
        
        for job in jobs:
            # Validate the job posting
            is_valid, reason = await self.job_collector.validate_posting(job)
            
            if is_valid:
                # Extract structured information
                processed_job = await self.info_extractor.extract_information(job)
                processed_jobs.append(processed_job)
            else:
                self.log.warning(f"Skipping invalid job posting: {reason}")
        
        return processed_jobs
    
    async def _apply_to_job(self, job: Dict[str, Any]):
        """Apply to a specific job position"""
        # Send application email
        application_status = await self.email_agent.send_application(
            job_data=job,
            resume_path="path/to/resume.pdf",  # TODO: Make configurable
            cover_letter_path="path/to/cover_letter.pdf"  # TODO: Make configurable
        )
        
        if application_status["success"]:
            self.active_applications.append({
                "job": job,
                "status": "applied",
                "application_date": datetime.now(),
                "message_id": application_status["message_id"]
            })
            
            self.log.info(f"Successfully applied to {job['title']} at {job['company']}")
        else:
            self.log.error(f"Failed to apply to {job['title']} at {job['company']}")
    
    async def _handle_application_response(self, response: Dict[str, Any]):
        """Handle responses to job applications"""
        # Find the corresponding application
        application = next(
            (app for app in self.active_applications 
             if app["message_id"] == response["reference_id"]),
            None
        )
        
        if not application:
            self.log.warning("Received response for unknown application")
            return
        
        if "interview" in response["type"].lower():
            # Handle interview request
            interview_details = await self.scheduler.schedule_interview(
                interview_request=response,
                job_data=application["job"]
            )
            
            if interview_details["success"]:
                application["status"] = "interview_scheduled"
                application["interview_details"] = interview_details
        
        elif "rejection" in response["type"].lower():
            # Handle rejection
            application["status"] = "rejected"
            self._move_to_completed(application)
        
        self.log.info(f"Handled response for {application['job']['title']}")
    
    async def _process_follow_ups(self):
        """Process follow-ups for applications without responses"""
        current_time = datetime.now()
        
        for application in self.active_applications:
            if application["status"] == "applied":
                # Check if follow-up is needed
                await self.email_agent.send_follow_up(
                    job_data=application["job"],
                    previous_email_id=application["message_id"]
                )
    
    async def _setup_response_monitoring(self):
        """Set up monitoring for application responses"""
        # Configure email monitoring
        monitoring_status = await self.email_agent.setup_response_monitoring(
            [app["message_id"] for app in self.active_applications]
        )
        
        self.log.info("Set up response monitoring for active applications")
        return monitoring_status
    
    def _move_to_completed(self, application: Dict[str, Any]):
        """Move an application to the completed list"""
        self.active_applications.remove(application)
        self.completed_applications.append({
            **application,
            "completion_date": datetime.now()
        })
