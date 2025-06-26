# ==============================================================================
#  scrapers/github_scraper.py - Fetches data directly from the GitHub API
# ==============================================================================

import httpx  # A modern and easy-to-use HTTP client library
import backoff # Import the new library

# The decorator can now catch the httpx.RequestError
@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
def _make_github_api_request(url):
    """A private helper function for making the actual API call, wrapped in backoff."""
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        if response.status_code in (403, 429):
            print(f"[!] GitHub API rate limit hit: {response.status_code}. Response: {response.text}")
            raise httpx.RequestError(f"GitHub API rate limit hit: {response.status_code}")
        response.raise_for_status() # This will raise an exception on failure
        return response.json()

def scrape(github_username: str):
    """
    The main public function. It orchestrates the API calls and handles
    the final formatting and user-facing errors.
    """
    if not github_username:
        return {"error": "No GitHub username was provided."}

    user_api_url = f"https://api.github.com/users/{github_username}"
    repos_api_url = f"https://api.github.com/users/{github_username}/repos?sort=pushed&per_page=5"

    try:
        print(f"[*] Fetching GitHub profile for: {github_username}")
        user_data = _make_github_api_request(user_api_url)

        print(f"[*] Fetching top 5 repos for: {github_username}")
        repos_data = _make_github_api_request(repos_api_url)

        # --- Format the final output ---
        final_output = {
            "profile": {
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "location": user_data.get("location"),
                "public_repos": user_data.get("public_repos"),
                "followers": user_data.get("followers"),
                "following": user_data.get("following"),
                "profile_url": user_data.get("html_url")
            },
            "top_repositories": [
                {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                    "forks": repo.get("forks_count"),
                    "url": repo.get("html_url")
                }
                for repo in repos_data
            ]
        }

        print(f"[✓] Successfully received structured JSON from GitHub API for '{github_username}'.")
        return final_output

    except httpx.HTTPStatusError as e:
        # This catches specific "user not found" errors after retries have failed
        error_message = f"GitHub API request failed: User '{github_username}' not found (Status {e.response.status_code})."
        print(f"[!] {error_message}")
        return {"error": error_message}
    except Exception as e:
        # This catches other errors, like the final network error after all backoff attempts
        error_message = f"An unexpected error occurred during GitHub scrape after retries: {e}"
        print(f"[!] {error_message}")
        return {"error": error_message}