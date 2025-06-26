# scrapers/leetcode_scraper.py
import httpx
import backoff

LEETCODE_API_URL = "https://leetcode.com/graphql"

@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3)
def _make_leetcode_api_request(payload):
    """A private helper for making the LeetCode GraphQL POST request with backoff."""
    with httpx.Client(timeout=15.0) as client:
        response = client.post(LEETCODE_API_URL, json=payload)
        if response.status_code == 429:
            print(f"[!] LeetCode API rate limit hit: {response.status_code}. Response: {response.text}")
            raise httpx.RequestError(f"LeetCode API rate limit hit: {response.status_code}")
        response.raise_for_status()
        return response.json()

def scrape(leetcode_username: str):
    """
    Fetches a user's public profile and stats from LeetCode's unofficial
    GraphQL API.

    Args:
        leetcode_username (str): The LeetCode username.

    Returns:
        dict: A dictionary of the user's stats or an error dictionary.
    """
    if not leetcode_username:
        return {"error": "No LeetCode username provided."}

    # This is the GraphQL query to get user stats
    graphql_query = {
        "query": """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    username
                    profile {
                        realName
                        ranking
                    }
                    submitStats: submitStatsGlobal {
                        acSubmissionNum {
                            difficulty
                            count
                            submissions
                        }
                    }
                }
            }
        """,
        "variables": {
            "username": leetcode_username
        }
    }

    try:
        print(f"[*] Fetching LeetCode stats for: {leetcode_username}")
        data = _make_leetcode_api_request(graphql_query)

        if not data.get("data") or not data["data"].get("matchedUser"):
            error_message = f"LeetCode user '{leetcode_username}' not found."
            print(f"[!] {error_message}")
            return {"error": error_message}
        
        user_data = data["data"]["matchedUser"]
        stats = user_data["submitStats"]["acSubmissionNum"]
        
        # Format the data into a clean, simple dictionary
        formatted_stats = {
            "username": user_data["username"],
            "ranking": user_data["profile"]["ranking"],
            "total_solved": next((s['count'] for s in stats if s['difficulty'] == 'All'), 0),
            "easy_solved": next((s['count'] for s in stats if s['difficulty'] == 'Easy'), 0),
            "medium_solved": next((s['count'] for s in stats if s['difficulty'] == 'Medium'), 0),
            "hard_solved": next((s['count'] for s in stats if s['difficulty'] == 'Hard'), 0),
            "profile_url": f"https://leetcode.com/{leetcode_username}"
        }
        
        print(f"[✓] Successfully received structured JSON from LeetCode for '{leetcode_username}'.")
        return formatted_stats

    except httpx.HTTPStatusError as e:
        error_message = f"LeetCode API request failed for user '{leetcode_username}': Status {e.response.status_code}"
        print(f"[!] {error_message}")
        return {"error": error_message}
    except Exception as e:
        error_message = f"An unexpected error occurred during LeetCode scrape: {e}"
        print(f"[!] {error_message}")
        return {"error": error_message}