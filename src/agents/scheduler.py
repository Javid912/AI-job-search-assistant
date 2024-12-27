"""
Scheduler Agent
Responsible for managing interview scheduling and calendar operations.
"""

from phi.agent import Agent
from phi.tools.calendar import CalendarTool
from phi.tools.email import EmailTool
from phi.tools.llm import LLMTool
from datetime import datetime, timedelta

class SchedulerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="scheduler",
            description="Manages interview scheduling",
            tools=[
                CalendarTool(
                    provider="google_calendar",
                    availability_check=True,
                    auto_confirm=False
                ),
                EmailTool(
                    provider="gmail",
                    templates_path="./email_templates",
                    tracking_enabled=True
                ),
                LLMTool(
                    model="gpt-4",
                    temperature=0.3  # Lower temperature for more consistent scheduling responses
                )
            ],
            knowledge_base="scheduling_protocols"
        )
        
        # Scheduling preferences
        self.scheduling_config = {
            "working_hours": {
                "start": "09:00",
                "end": "17:00"
            },
            "buffer_time": 30,  # Minutes before/after interviews
            "default_duration": 60,  # Default interview duration in minutes
            "timezone": "America/New_York",
            "calendar_id": "primary"
        }
        
        # Track scheduled interviews
        self.scheduled_interviews = []
    
    async def schedule_interview(self, interview_request, job_data):
        """
        Schedule an interview based on the request
        
        Args:
            interview_request (dict): Interview request details
            job_data (dict): Related job posting data
        
        Returns:
            dict: Scheduled interview details
        """
        # Extract proposed times if any
        proposed_times = await self._extract_proposed_times(interview_request["content"])
        
        if proposed_times:
            # Check availability for proposed times
            available_slots = await self._check_availability(proposed_times)
        else:
            # Find available slots in the next week
            available_slots = await self._find_available_slots(
                days_ahead=7,
                num_slots=3
            )
        
        if not available_slots:
            return {
                "success": False,
                "reason": "No available time slots found"
            }
        
        # Schedule the interview
        scheduled_time = available_slots[0]  # Take the first available slot
        interview_details = await self._create_calendar_event(
            job_data,
            scheduled_time
        )
        
        if interview_details["success"]:
            # Send confirmation email
            await self._send_confirmation_email(
                job_data,
                interview_details,
                interview_request
            )
            
            # Track the scheduled interview
            self.scheduled_interviews.append({
                "company": job_data["company"],
                "position": job_data["title"],
                "datetime": scheduled_time,
                "event_id": interview_details["event_id"],
                "status": "scheduled"
            })
        
        return interview_details
    
    async def suggest_alternative_times(self, job_data, unavailable_time):
        """
        Suggest alternative interview times
        
        Args:
            job_data (dict): Job posting data
            unavailable_time (datetime): Originally proposed time that was unavailable
        
        Returns:
            list: Alternative available time slots
        """
        # Find available slots around the unavailable time
        alternative_slots = await self._find_available_slots(
            start_date=unavailable_time.date(),
            days_ahead=5,
            num_slots=3
        )
        
        if alternative_slots:
            # Send email with alternative times
            await self._send_alternative_times_email(
                job_data,
                alternative_slots
            )
        
        return alternative_slots
    
    async def send_interview_reminder(self, interview_id, hours_before=24):
        """
        Send a reminder email for an upcoming interview
        
        Args:
            interview_id (str): Calendar event ID for the interview
            hours_before (int): Hours before interview to send reminder
        """
        interview = await self.tools["CalendarTool"].get_event(interview_id)
        
        if not interview:
            return {
                "success": False,
                "reason": "Interview not found"
            }
        
        # Calculate reminder time
        interview_time = datetime.fromisoformat(interview["start"]["dateTime"])
        reminder_time = interview_time - timedelta(hours=hours_before)
        
        if datetime.now() >= reminder_time:
            # Generate and send reminder email
            reminder_status = await self._send_reminder_email(interview)
            return reminder_status
        
        return {
            "success": False,
            "reason": "Too early for reminder"
        }
    
    async def _extract_proposed_times(self, email_content):
        """Extract proposed interview times from email content using LLM"""
        times = await self.tools["LLMTool"].analyze(
            text=email_content,
            context={
                "type": "datetime_extraction",
                "timezone": self.scheduling_config["timezone"]
            }
        )
        
        return times.get("proposed_times", [])
    
    async def _check_availability(self, time_slots):
        """Check calendar availability for given time slots"""
        available_slots = []
        
        for slot in time_slots:
            # Add buffer time to the slot
            start_time = slot - timedelta(minutes=self.scheduling_config["buffer_time"])
            end_time = slot + timedelta(
                minutes=self.scheduling_config["default_duration"] + 
                self.scheduling_config["buffer_time"]
            )
            
            # Check if slot is within working hours
            if not self._is_within_working_hours(slot):
                continue
            
            # Check calendar availability
            is_available = await self.tools["CalendarTool"].check_availability(
                start_time,
                end_time,
                calendar_id=self.scheduling_config["calendar_id"]
            )
            
            if is_available:
                available_slots.append(slot)
        
        return available_slots
    
    async def _create_calendar_event(self, job_data, interview_time):
        """Create a calendar event for the interview"""
        event_details = {
            "summary": f"Interview with {job_data['company']} - {job_data['title']}",
            "description": f"Job Interview\nCompany: {job_data['company']}\n"
                         f"Position: {job_data['title']}\n"
                         f"Location: {job_data.get('interview_location', 'To be confirmed')}",
            "start": {
                "dateTime": interview_time.isoformat(),
                "timeZone": self.scheduling_config["timezone"]
            },
            "end": {
                "dateTime": (
                    interview_time + 
                    timedelta(minutes=self.scheduling_config["default_duration"])
                ).isoformat(),
                "timeZone": self.scheduling_config["timezone"]
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30}
                ]
            }
        }
        
        return await self.tools["CalendarTool"].create_event(
            event_details,
            calendar_id=self.scheduling_config["calendar_id"]
        )
    
    def _is_within_working_hours(self, time):
        """Check if a given time is within configured working hours"""
        working_start = datetime.strptime(
            self.scheduling_config["working_hours"]["start"],
            "%H:%M"
        ).time()
        working_end = datetime.strptime(
            self.scheduling_config["working_hours"]["end"],
            "%H:%M"
        ).time()
        
        return working_start <= time.time() <= working_end
    
    async def _send_confirmation_email(self, job_data, interview_details, original_request):
        """Send interview confirmation email"""
        template = await self.tools["EmailTool"].get_template("interview_confirmation.txt")
        
        email_content = await self.tools["LLMTool"].generate(
            prompt=template,
            context={
                "job_data": job_data,
                "interview_details": interview_details,
                "original_request": original_request
            }
        )
        
        return await self.tools["EmailTool"].send_email(
            to_email=job_data["contact"]["email"],
            subject=f"Interview Confirmation - {job_data['title']} position at {job_data['company']}",
            content=email_content,
            references=[original_request["message_id"]]
        )
