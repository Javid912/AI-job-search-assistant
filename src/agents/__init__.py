"""
Job Search Automation Agents Module
This module contains the agent configurations for the job search automation system.
"""

from .job_collector import JobCollectorAgent
from .information_extractor import InformationExtractorAgent
from .email_agent import EmailAgent
from .scheduler import SchedulerAgent

__all__ = [
    'JobCollectorAgent',
    'InformationExtractorAgent',
    'EmailAgent',
    'SchedulerAgent',
]
