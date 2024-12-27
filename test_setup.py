"""
Test script to verify the job search automation system setup.
Tests configuration, credentials, and basic functionality of each component.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from config import load_config
from src.agents import (
    JobCollectorAgent,
    InformationExtractorAgent,
    EmailAgent,
    SchedulerAgent
)

class SetupTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def print_header(self, message: str):
        print("\n" + "="*50)
        print(message)
        print("="*50)
    
    def print_result(self, test_name: str, passed: bool, error: str = None):
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status} - {test_name}")
        if error:
            print(f"  Error: {error}")
        
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "error": error
        })
        
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    async def test_environment_variables(self):
        """Test required environment variables"""
        self.print_header("Testing Environment Variables")
        
        required_vars = [
            "OPENAI_API_KEY",
            "GMAIL_CREDENTIALS",
            "CALENDAR_CREDENTIALS",
            "SENDER_EMAIL",
            "RESUME_PATH"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            self.print_result(
                f"Environment variable: {var}",
                bool(value),
                None if value else "Variable not set"
            )
    
    async def test_config_loading(self):
        """Test configuration loading"""
        self.print_header("Testing Configuration Loading")
        
        try:
            config = load_config()
            self.print_result(
                "Configuration loading",
                True
            )
            
            # Test specific config sections
            sections = [
                "search_preferences",
                "email_config",
                "calendar_config",
                "materials_config",
                "api_credentials"
            ]
            
            for section in sections:
                self.print_result(
                    f"Config section: {section}",
                    section in config,
                    None if section in config else f"Missing section: {section}"
                )
        
        except Exception as e:
            self.print_result(
                "Configuration loading",
                False,
                str(e)
            )
    
    async def test_file_paths(self):
        """Test required file paths"""
        self.print_header("Testing File Paths")
        
        paths_to_check = [
            ("Resume", os.getenv("RESUME_PATH")),
            ("Gmail credentials", os.getenv("GMAIL_CREDENTIALS")),
            ("Calendar credentials", os.getenv("CALENDAR_CREDENTIALS")),
            ("Email templates", "./email_templates"),
        ]
        
        for name, path in paths_to_check:
            exists = path and os.path.exists(path)
            self.print_result(
                f"File path: {name}",
                exists,
                None if exists else f"Path does not exist: {path}"
            )
    
    async def test_agent_initialization(self):
        """Test agent initialization"""
        self.print_header("Testing Agent Initialization")
        
        agents = [
            ("JobCollectorAgent", JobCollectorAgent),
            ("InformationExtractorAgent", InformationExtractorAgent),
            ("EmailAgent", EmailAgent),
            ("SchedulerAgent", SchedulerAgent)
        ]
        
        for name, agent_class in agents:
            try:
                agent = agent_class()
                self.print_result(
                    f"Agent initialization: {name}",
                    True
                )
            except Exception as e:
                self.print_result(
                    f"Agent initialization: {name}",
                    False,
                    str(e)
                )
    
    async def test_api_connections(self):
        """Test API connections"""
        self.print_header("Testing API Connections")
        
        # Test OpenAI API
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = await openai.Completion.acreate(
                engine="gpt-3.5-turbo-instruct",
                prompt="Hello",
                max_tokens=5
            )
            self.print_result(
                "OpenAI API connection",
                True
            )
        except Exception as e:
            self.print_result(
                "OpenAI API connection",
                False,
                str(e)
            )
        
        # Test other APIs based on available credentials
        apis = [
            ("LinkedIn", "LINKEDIN_API_KEY"),
            ("Glassdoor", "GLASSDOOR_API_KEY"),
            ("Indeed", "INDEED_API_KEY")
        ]
        
        for api_name, key_var in apis:
            api_key = os.getenv(key_var)
            if api_key:
                self.print_result(
                    f"{api_name} API credentials",
                    True
                )
            else:
                self.print_result(
                    f"{api_name} API credentials",
                    False,
                    "API key not configured"
                )
    
    def print_summary(self):
        """Print test results summary"""
        self.print_header("Test Summary")
        print(f"Total tests: {self.tests_passed + self.tests_failed}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        
        if self.tests_failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"- {result['name']}: {result['error']}")

async def main():
    tester = SetupTester()
    
    try:
        # Run all tests
        await tester.test_environment_variables()
        await tester.test_config_loading()
        await tester.test_file_paths()
        await tester.test_agent_initialization()
        await tester.test_api_connections()
        
        # Print summary
        tester.print_summary()
        
        # Exit with appropriate status code
        sys.exit(1 if tester.tests_failed > 0 else 0)
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
