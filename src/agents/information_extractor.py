"""
Information Extractor Agent
Responsible for parsing and structuring job posting data.
"""

from phi.agent import Agent
from phi.tools.text import TextParsingTool
from phi.tools.llm import LLMTool

class InformationExtractorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="information_extractor",
            description="Extracts and structures job posting data",
            tools=[
                TextParsingTool(
                    patterns={
                        "salary_range": r"\$[\d,]+ *[-–] *\$[\d,]+|\$[\d,]+ *\+?(?:\/(?:year|yr|month|mo|week|wk|hour|hr))?",
                        "years_experience": r"\d+\+?\s*(?:-|to)?\s*\d*\s*(?:years?|yrs?)\s*(?:of)?\s*experience",
                        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                        "skills": r"(?:proficient|experienced|skilled)\s+in\s+([^.]*)"
                    }
                ),
                LLMTool(
                    model="gpt-4",
                    temperature=0.1
                )
            ],
            knowledge_base="job_data_schema"
        )
        
        # Define the schema for structured job data
        self.job_schema = {
            "title": str,
            "company": str,
            "location": str,
            "description": str,
            "requirements": list,
            "qualifications": list,
            "responsibilities": list,
            "salary_range": str,
            "benefits": list,
            "contact": {
                "name": str,
                "email": str,
                "phone": str
            },
            "application_url": str,
            "posting_date": str,
            "skills_required": list,
            "experience_required": str,
            "education_required": str,
            "employment_type": str,
            "remote_policy": str
        }
    
    async def extract_information(self, job_posting):
        """
        Extract structured information from a job posting
        
        Args:
            job_posting (dict): Raw job posting data
        
        Returns:
            dict: Structured job information following the schema
        """
        # Extract information using LLM
        structured_data = await self.run(
            task="Extract structured information from job posting",
            context={
                "job_posting": job_posting,
                "schema": self.job_schema
            }
        )
        
        # Extract specific patterns using regex
        patterns_data = await self._extract_patterns(job_posting["description"])
        
        # Merge and validate the extracted information
        final_data = {**structured_data, **patterns_data}
        return await self._validate_extracted_data(final_data)
    
    async def _extract_patterns(self, text):
        """
        Extract information using regex patterns
        
        Args:
            text (str): Text to extract information from
        
        Returns:
            dict: Extracted pattern matches
        """
        extracted_data = {}
        
        # Use TextParsingTool to extract patterns
        pattern_matches = await self.tools["TextParsingTool"].extract_patterns(text)
        
        # Process and structure the matches
        if "salary_range" in pattern_matches:
            extracted_data["salary_range"] = pattern_matches["salary_range"][0]
        if "years_experience" in pattern_matches:
            extracted_data["experience_required"] = pattern_matches["years_experience"][0]
        if "email" in pattern_matches:
            extracted_data["contact"] = {
                "email": pattern_matches["email"][0]
            }
        if "skills" in pattern_matches:
            extracted_data["skills_required"] = [
                skill.strip()
                for skill in pattern_matches["skills"][0].split(",")
            ]
        
        return extracted_data
    
    async def _validate_extracted_data(self, data):
        """
        Validate the extracted data against the schema
        
        Args:
            data (dict): Extracted job data
        
        Returns:
            dict: Validated and cleaned job data
        """
        validated_data = {}
        
        for field, field_type in self.job_schema.items():
            if field in data:
                if isinstance(field_type, type):
                    # Handle simple types
                    if isinstance(data[field], field_type):
                        validated_data[field] = data[field]
                    else:
                        try:
                            validated_data[field] = field_type(data[field])
                        except (ValueError, TypeError):
                            validated_data[field] = None
                elif isinstance(field_type, dict):
                    # Handle nested dictionaries
                    validated_data[field] = {
                        k: v for k, v in data[field].items()
                        if k in field_type and isinstance(v, field_type[k])
                    }
                elif isinstance(field_type, list):
                    # Handle lists
                    if isinstance(data[field], list):
                        validated_data[field] = data[field]
                    else:
                        validated_data[field] = [data[field]]
            else:
                # Set default values for missing fields
                validated_data[field] = [] if isinstance(field_type, list) else None
        
        return validated_data
