import os
from celery import Celery
from pymongo import MongoClient
import json
# Add OpenAI and httpx imports for LLM usage
from openai import OpenAI
import httpx
from dotenv import load_dotenv
import logging

# Import your scrapers and services
from scrapers import linkedin_scraper, github_scraper, leetcode_scraper, kaggle_scraper
from dataCompare.main import compare_multi_source_data # We will create this function

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Celery Configuration ---
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# --- DB Connection ---
# Use environment variables for this in production!
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['document_aggregation']
jobs_collection = db['jobs']

# Update Celery config to know about the Flask app context (optional but good practice)
def init_celery(app):
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

# Create the OpenRouter client for LLM calls
llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=httpx.Timeout(180.0),
)

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@celery.task
def process_verification_job(job_id):
    """The master background task to run all scrapers and the final analysis."""
    try:
        jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "Processing: Scraping LinkedIn..."}})
        
        job = jobs_collection.find_one({"_id": job_id})
        if not job:
            logger.error(f"[!] Job {job_id} not found in database. Aborting.")
            return True

        resume_data = job['data']['resume']

        # --- 1. LinkedIn Scraper ---
        linkedin_id_raw = resume_data.get('linkedin_id')
        if linkedin_id_raw:
            # Clean the ID robustly before using it
            import re
            match = re.search(r'linkedin\.com/in/([^/]+)', linkedin_id_raw)
            linkedin_id = match.group(1) if match else linkedin_id_raw.split('/in/')[-1].strip('/')

            logger.info(f"[{job_id}] Scraping LinkedIn for: {linkedin_id}")
            linkedin_result = linkedin_scraper.scrape(linkedin_id)
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.linkedin": {"status": "COMPLETED", "data": linkedin_result}}}
            )
        else:
            logger.warning(f"[{job_id}] No LinkedIn ID found in resume. Skipping.")
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.linkedin": {"status": "SKIPPED", "data": {"error": "No LinkedIn ID provided in resume."}}}}
            )

        jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "Processing: Scraping GitHub..."}})
        # --- 2. GitHub Scraper ---
        github_id_raw = resume_data.get('github_id')
        github_email = resume_data.get('contact_info', {}).get('email')
        
        # Try to find a usable GitHub identifier
        github_id = None
        if github_id_raw:
            # Extract username from URL if it's a URL
            if 'github.com' in github_id_raw:
                github_id = github_id_raw.split('github.com/')[-1].strip('/')
            else:
                github_id = github_id_raw
        elif github_email:
            # Fallback: derive from email
            github_id = github_email.split('@')[0]
            logger.info(f"[{job_id}] No GitHub ID in resume. Deriving from email: {github_id}")

        if github_id:
            logger.info(f"[{job_id}] Scraping GitHub for: {github_id}")
            github_result = github_scraper.scrape(github_id)
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.github": {"status": "COMPLETED", "data": github_result}}}
            )
        else:
            logger.warning(f"[{job_id}] No GitHub ID found or derivable. Skipping.")
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.github": {"status": "SKIPPED", "data": {"error": "No GitHub ID provided in resume."}}}}
            )

        # --- 3. LeetCode Scraper ---
        leetcode_id = resume_data.get('leetcode_id')
        if leetcode_id:
            # UPDATE STATUS *BEFORE* RUNNING THE SCRAPER
            jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "Processing: Scraping LeetCode..."}})
            logger.info(f"Job {job_id}: Scraping LeetCode for: {leetcode_id}")
            leetcode_result = leetcode_scraper.scrape(leetcode_id)
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.leetcode": {"status": "COMPLETED", "data": leetcode_result}}}
            )
        else:
            logger.warning(f"Job {job_id}: No LeetCode ID found. Skipping.")
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.leetcode": {"status": "SKIPPED", "data": {"error": "No LeetCode ID provided in resume."}}}}
            )

        # --- 4. Kaggle Scraper ---
        kaggle_id = resume_data.get('kaggle_id')
        if kaggle_id:
            # UPDATE STATUS *BEFORE* RUNNING THE SCRAPER
            jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "Processing: Scraping Kaggle..."}})
            logger.info(f"Job {job_id}: Scraping Kaggle for: {kaggle_id}")
            kaggle_result = kaggle_scraper.scrape(kaggle_id)
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.kaggle": {"status": "COMPLETED", "data": kaggle_result}}}
            )
        else:
            logger.warning(f"Job {job_id}: No Kaggle ID found. Skipping.")
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {"data.sources.kaggle": {"status": "SKIPPED", "data": {"error": "No Kaggle ID provided in resume."}}}}
            )

        jobs_collection.update_one({"_id": job_id}, {"$set": {"status": "Processing: Performing Final Analysis..."}})
        # --- Final Analysis ---
        logger.info(f"[{job_id}] All scrapers finished. Running final analysis.")
        final_job_data = jobs_collection.find_one({"_id": job_id})
        final_report_str = compare_multi_source_data(final_job_data['data'])

        # === NEW LOGIC HERE ===
        if final_report_str is None:
            # The AI call failed. Mark the job as FAILED.
            logger.error(f"[!] The final AI comparison failed for job {job_id}.")
            jobs_collection.update_one(
                {"_id": job_id},
                {"$set": {
                    "status": "FAILED", 
                    "final_report": {"error": "The final AI analysis step failed. This could be due to an API error or insufficient credits."}
                }}
            )
        else:
            # The AI call succeeded. Proceed as normal.
            try:
                final_report_json = json.loads(final_report_str)
                
                # --- THE FIX: Extract the score and prepare for top-level update ---
                consistency_score = final_report_json.get('consistency_score')

                update_payload = {
                    "status": "COMPLETED",
                    "final_report": final_report_json
                }
                
                # Only add the score if it's a valid number
                if isinstance(consistency_score, (int, float)):
                    update_payload["consistency_score"] = consistency_score
                
                # Update the document with the full report AND the top-level score
                jobs_collection.update_one(
                    {"_id": job_id},
                    {"$set": update_payload}
                )
                logger.info(f"Job {job_id}: COMPLETED with consistency score: {consistency_score}")
            except json.JSONDecodeError:
                # The AI returned a non-JSON string. Mark as FAILED.
                jobs_collection.update_one(
                    {"_id": job_id},
                    {"$set": {
                        "status": "FAILED", 
                        "final_report": {"error": "The AI returned an invalid JSON response.", "raw_output": final_report_str}
                    }}
                )
    except Exception as e:
        logger.error(f"[!] Unhandled exception in process_verification_job for job {job_id}: {e}", exc_info=True)
        jobs_collection.update_one(
            {"_id": job_id},
            {"$set": {
                "status": "FAILED",
                "final_report": {"error": f"Unhandled exception: {str(e)}"}
            }}
        )
        return False
    return True # Always return True so Celery knows the task is done