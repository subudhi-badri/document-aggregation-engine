# ==============================================================================
#  LinkedIn/main.py - CORRECTED INPUT FOR APIFY ACTOR
# ==============================================================================

from apify_client import ApifyClient
import json
import os
from dotenv import load_dotenv
# --- CONFIGURATION ---
load_dotenv()  # Load environment variables from .env file
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
LINKEDIN_SCRAPER_ACTOR_ID = "dev_fusion/linkedin-profile-scraper"

def get_linkedin_data_via_api(linkedin_id):
    """
    Uses the Apify platform to run a LinkedIn scraping Actor and fetch the
    clean JSON results using the correct input schema.
    """
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        
        profile_url = f'https://www.linkedin.com/in/{linkedin_id}'
        
        # MODIFIED: Use the correct input schema required by this specific Actor.
        # It wants a list of strings in a key named 'profileUrls'.
        actor_input = {
            "profileUrls": [profile_url],
            "maxProfiles": 1,
        }

        print(f"[*] Starting Apify Actor '{LINKEDIN_SCRAPER_ACTOR_ID}' with correct input...")
        
        # Start the Actor run
        run_info = client.actor(LINKEDIN_SCRAPER_ACTOR_ID).start(run_input=actor_input)

        print("[*] Apify Actor run started. Waiting for it to finish...")

        # Wait for the run to complete
        run_detail = client.run(run_info['id']).wait_for_finish()

        if run_detail['status'] != 'SUCCEEDED':
            error_message = f"Apify Actor finished with status '{run_detail['status']}'. Check the run in the Apify Console for details."
            print(f"[!] {error_message}")
            return None, error_message

        print("[*] Apify Actor run finished successfully. Fetching results...")
        
        items = [item for item in client.dataset(run_info['defaultDatasetId']).iterate_items()]

        if not items:
            return None, "Apify Actor finished but returned no data."

        profile_json = items[0]
        
        if profile_json.get('error'):
            return None, f"Apify Actor returned an error: {profile_json['error']}"
            
        print("[✓] Successfully received structured JSON from Apify.")
        
        # ... (save file logic) ...

        return profile_json, None

    except Exception as e:
        error_message = f"An unexpected error occurred with the Apify API: {e}"
        print(f"[!] {error_message}")
        return None, error_message