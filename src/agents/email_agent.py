"""
Email Agent
Responsible for handling email communications with recruiters.
"""

from phi.agent import Agent
from phi.tools.email import EmailTool
from phi.tools.llm import LLMTool
from datetime import datetime, timedelta

class EmailAgent(Agent):
    def __init__(self):
        super().__init__(
            name="email_agent",
            description="Handles email communication with recruiters",
            tools=[
                EmailTool(
                    provider="gmail",
                    templates_path="./email_templates",
                    tracking_enabled=True
                ),
                LLMTool(
                    model="gpt-4",
                    temperature=0.7  # Higher temperature for more creative email writing
                )
            ],
            knowledge_base="email_templates"
        )
        
        # Email tracking and management
        self.email_status = {
            "sent": [],
            "responses": [],
            "follow_ups_needed": [],
            "completed": []
        }
        
        # Configure email settings
        self.email_config = {
            "follow_up_days": 5,  # Days to wait before follow-up
            "max_follow_ups": 2,  # Maximum number of follow-ups per application
            "signature": None,  # Will be set during initialization
            "templates": {
                "application": "application_template.txt",
                "follow_up": "follow_up_template.txt",
                "thank_you": "thank_you_template.txt"
            }
        }
    
    async def send_application(self, job_data, resume_path, cover_letter_path=None):
        """
        Send a job application email
        
        Args:
            job_data (dict): Structured job posting data
            resume_path (str): Path to resume file
            cover_letter_path (str, optional): Path to cover letter file
        
        Returns:
            dict: Email sending status and tracking information
        """
        # Generate email content using LLM
        email_content = await self._generate_email_content(
            "application",
            job_data,
            include_cover_letter=bool(cover_letter_path)
        )
        
        # Prepare attachments
        attachments = [resume_path]
        if cover_letter_path:
            attachments.append(cover_letter_path)
        
        # Send email
        email_status = await self.tools["EmailTool"].send_email(
            to_email=job_data["contact"]["email"],
            subject=f"Application for {job_data['title']} position at {job_data['company']}",
            content=email_content,
            attachments=attachments
        )
        
        # Track email
        if email_status["success"]:
            self._track_email(
                job_data["company"],
                "application",
                email_status["message_id"]
            )
        
        return email_status
    
    async def check_responses(self):
        """
        Check for responses to sent applications
        
        Returns:
            list: New responses received
        """
        responses = await self.tools["EmailTool"].check_responses(
            message_ids=[email["message_id"] for email in self.email_status["sent"]]
        )
        
        for response in responses:
            if response["message_id"] not in [r["message_id"] for r in self.email_status["responses"]]:
                self.email_status["responses"].append(response)
                await self._handle_response(response)
        
        return responses
    
    async def send_follow_up(self, job_data, previous_email_id):
        """
        Send a follow-up email for an application
        
        Args:
            job_data (dict): Job application data
            previous_email_id (str): ID of the previous email
        
        Returns:
            dict: Follow-up email status
        """
        # Check if follow-up is needed
        if not self._should_send_follow_up(previous_email_id):
            return {"success": False, "reason": "Follow-up not needed yet"}
        
        # Generate follow-up content
        follow_up_content = await self._generate_email_content(
            "follow_up",
            job_data
        )
        
        # Send follow-up
        follow_up_status = await self.tools["EmailTool"].send_email(
            to_email=job_data["contact"]["email"],
            subject=f"Following up on {job_data['title']} application - {job_data['company']}",
            content=follow_up_content,
            references=[previous_email_id]
        )
        
        # Track follow-up
        if follow_up_status["success"]:
            self._track_email(
                job_data["company"],
                "follow_up",
                follow_up_status["message_id"],
                reference_id=previous_email_id
            )
        
        return follow_up_status
    
    async def _generate_email_content(self, email_type, job_data, **kwargs):
        """Generate email content using templates and LLM"""
        template_path = self.email_config["templates"][email_type]
        
        # Get template content
        template = await self.tools["EmailTool"].get_template(template_path)
        
        # Generate content using LLM
        content = await self.tools["LLMTool"].generate(
            prompt=template,
            context={
                "job_data": job_data,
                "email_type": email_type,
                **kwargs
            }
        )
        
        return f"{content}\n\n{self.email_config['signature']}"
    
    def _track_email(self, company, email_type, message_id, reference_id=None):
        """Track sent email for follow-up management"""
        email_data = {
            "company": company,
            "type": email_type,
            "message_id": message_id,
            "reference_id": reference_id,
            "sent_date": datetime.now(),
            "follow_ups_sent": 0
        }
        
        self.email_status["sent"].append(email_data)
    
    def _should_send_follow_up(self, email_id):
        """Determine if a follow-up email should be sent"""
        email_data = next(
            (email for email in self.email_status["sent"] if email["message_id"] == email_id),
            None
        )
        
        if not email_data:
            return False
        
        # Check if maximum follow-ups reached
        if email_data["follow_ups_sent"] >= self.email_config["max_follow_ups"]:
            return False
        
        # Check if enough time has passed
        days_since_last = (datetime.now() - email_data["sent_date"]).days
        return days_since_last >= self.email_config["follow_up_days"]
    
    async def _handle_response(self, response):
        """Handle received email responses"""
        # Analyze response using LLM
        analysis = await self.tools["LLMTool"].analyze(
            text=response["content"],
            context={"type": "email_response"}
        )
        
        if analysis["type"] == "rejection":
            self._mark_application_completed(response["reference_id"], "rejected")
        elif analysis["type"] == "interview_request":
            self._mark_application_completed(response["reference_id"], "interview_scheduled")
            # Trigger interview scheduling workflow
            await self.run(
                task="Schedule interview",
                context={"response": response, "analysis": analysis}
            )
        elif analysis["type"] == "positive_response":
            # Send thank you email
            await self._send_thank_you(response)
