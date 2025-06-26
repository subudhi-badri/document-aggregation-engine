# scrapers/kaggle_scraper.py
import httpx
from bs4 import BeautifulSoup
import json # Use json to parse the script tag data
import backoff # Import the library

@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
def _make_kaggle_api_request(url):
    """A private helper for making the Kaggle profile GET request with backoff."""
    with httpx.Client(timeout=15.0, headers={"User-Agent": "My-Resume-Scraper/1.0"}) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text

def scrape(kaggle_username: str):
    """
    Scrapes a user's public profile from Kaggle by parsing the HTML
    and the embedded JSON data for better reliability.

    Args:
        kaggle_username (str): The Kaggle username.

    Returns:
        dict: A dictionary of the user's stats or an error dictionary.
    """
    if not kaggle_username:
        return {"error": "No Kaggle username provided."}

    profile_url = f"https://www.kaggle.com/{kaggle_username}"
    
    try:
        print(f"[*] Fetching Kaggle profile for: {kaggle_username}")
        html = _make_kaggle_api_request(profile_url)
        soup = BeautifulSoup(html, "lxml")

        # --- A MUCH MORE ROBUST METHOD: Parse the embedded JSON data ---
        # Kaggle embeds a script tag with all the user data as JSON. This is more stable.
        script_tag = soup.find('script', id='site-initial-data')
        if not script_tag:
            print(f"[!] Could not find initial data script. Full HTML: {html[:1000]}")
            return {"error": "Could not find initial data script on Kaggle page. The site structure may have changed."}
        try:
            data = json.loads(script_tag.string)
        except Exception as e:
            print(f"[!] Failed to parse Kaggle embedded JSON. Script content: {script_tag.string[:1000]}")
            return {"error": "Failed to parse Kaggle embedded JSON. The site structure may have changed."}
        
        # Navigate through the JSON to find the user profile data
        user_profile = data.get('userProfile')
        if not user_profile:
            return {"error": f"Kaggle user '{kaggle_username}' data not found in page script."}

        # Safely get each piece of data with .get() to avoid errors
        formatted_stats = {
            "username": user_profile.get('userName'),
            "name": user_profile.get('displayName'),
            "performance_tier": user_profile.get('performanceTier', 'Not Found'),
            "followers": user_profile.get('followers', 0),
            "following": user_profile.get('following', 0),
            "profile_url": profile_url
        }

        print(f"[✓] Successfully parsed data from Kaggle for '{kaggle_username}'.")
        return formatted_stats

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_message = f"Kaggle user '{kaggle_username}' not found (404)."
        else:
            error_message = f"Kaggle profile request failed for user '{kaggle_username}': Status {e.response.status_code}"
        print(f"[!] {error_message}")
        return {"error": error_message}
    except Exception as e:
        error_message = f"An unexpected error occurred during Kaggle scrape: {e}"
        print(f"[!] {error_message}")
        return {"error": error_message}