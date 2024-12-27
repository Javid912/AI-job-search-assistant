"""
Job Search Automation System
Main entry point for running the job search automation workflow.
"""

import asyncio
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

from src.workflows.job_search import JobSearchWorkflow
from config import load_config, update_config, SEARCH_PREFERENCES

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Configure logging based on settings"""
    logging_config = config["logging_config"]
    
    logging.basicConfig(
        level=logging_config["level"],
        format=logging_config["format"],
        filename=logging_config["file"],
        filemode="a"
    )
    
    logger = logging.getLogger("job_search")
    return logger

async def run_job_search(config: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Run the job search workflow
    
    Args:
        config (dict): Application configuration
        logger (logging.Logger): Logger instance
    """
    try:
        # Initialize workflow
        workflow = JobSearchWorkflow()
        
        # Run job search with configured preferences
        results = await workflow.run_job_search(config["search_preferences"])
        
        logger.info(
            f"Job search completed - Found: {results['jobs_found']}, "
            f"Processed: {results['jobs_processed']}, "
            f"Applied: {results['applications_sent']}"
        )
        
        # Start monitoring for responses
        while True:
            status = await workflow.check_application_status()
            logger.info(
                f"Status check - New responses: {status['new_responses']}, "
                f"Active: {status['active_applications']}, "
                f"Completed: {status['completed_applications']}"
            )
            
            # Wait before next check
            await asyncio.sleep(3600)  # Check every hour
            
    except Exception as e:
        logger.error(f"Error in job search workflow: {str(e)}", exc_info=True)
        raise

def update_search_preferences(updates: Dict[str, Any]) -> None:
    """Update job search preferences"""
    update_config("search_preferences", updates)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Job Search Automation System")
    
    parser.add_argument(
        "--update-preferences",
        action="store_true",
        help="Update job search preferences"
    )
    
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="Job search keywords"
    )
    
    parser.add_argument(
        "--locations",
        nargs="+",
        help="Job locations"
    )
    
    parser.add_argument(
        "--job-types",
        nargs="+",
        help="Types of jobs to search for"
    )
    
    parser.add_argument(
        "--experience-levels",
        nargs="+",
        help="Required experience levels"
    )
    
    parser.add_argument(
        "--posted-within-days",
        type=int,
        help="Only consider jobs posted within this many days"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        logger = setup_logging(config)
        
        if args.update_preferences:
            # Update search preferences if provided
            updates = {}
            if args.keywords:
                updates["keywords"] = args.keywords
            if args.locations:
                updates["locations"] = args.locations
            if args.job_types:
                updates["job_types"] = args.job_types
            if args.experience_levels:
                updates["experience_levels"] = args.experience_levels
            if args.posted_within_days:
                updates["posted_within_days"] = args.posted_within_days
            
            if updates:
                update_search_preferences(updates)
                logger.info("Updated search preferences")
                print("Search preferences updated successfully")
            else:
                print("No preference updates provided")
            
            return
        
        # Run the job search workflow
        print("Starting job search automation...")
        logger.info("Starting job search automation")
        
        asyncio.run(run_job_search(config, logger))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if logger:
            logger.error("Fatal error in main", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
