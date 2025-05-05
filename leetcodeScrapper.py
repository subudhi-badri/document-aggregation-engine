import requests
import json

def get_leetcode_data(username):
    """Fetches LeetCode user stats including problem-solving and contest performance."""

    graphql_url = "https://leetcode.com/graphql"
    
    # GraphQL query for fetching user profile and problem-solving stats
    profile_query = {
        "operationName": "getUserProfile",
        "query": """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }""",
        "variables": {"username": username}
    }

    # GraphQL query for contest performance
    contest_query = {
        "operationName": "getUserContestRanking",
        "query": """
        query getUserContestRanking($username: String!) {
            userContestRanking(username: $username) {
                rating
                globalRanking
                attendedContestsCount
            }
            userContestRankingHistory(username: $username) {
                rating
            }
        }""",
        "variables": {"username": username}
    }

    headers = {"Content-Type": "application/json"}

    # Fetch profile & problem-solving stats
    profile_response = requests.post(graphql_url, json=profile_query, headers=headers)
    if profile_response.status_code != 200:
        return {"error": "Failed to fetch user profile"}
    
    profile_data = profile_response.json()
    if not profile_data.get("data") or not profile_data["data"].get("matchedUser"):
        return {"error": "User not found"}
    
    user_info = profile_data["data"]["matchedUser"]
    submission_stats = user_info["submitStats"]["acSubmissionNum"]

    # Extract problem counts
    problem_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    total_solved = 0
    for entry in submission_stats:
        difficulty = entry["difficulty"]
        if difficulty in problem_counts:
            problem_counts[difficulty] = entry["count"]
        total_solved += entry["count"]

    # Fetch contest performance data
    contest_response = requests.post(graphql_url, json=contest_query, headers=headers)
    contest_performance = {"highest_rank": "N/A", "best_contest_rating": "N/A", "latest_rating": "N/A", "total_contests": 0}

    if contest_response.status_code == 200:
        contest_data = contest_response.json()
        ranking = contest_data["data"]["userContestRanking"]
        history = contest_data["data"]["userContestRankingHistory"]

        if ranking:
            contest_performance["latest_rating"] = ranking.get("rating", "N/A")
            contest_performance["highest_rank"] = ranking.get("globalRanking", "N/A")
            contest_performance["total_contests"] = ranking.get("attendedContestsCount", 0)

        if history:
            ratings = [entry["rating"] for entry in history if entry["rating"]]
            if ratings:
                contest_performance["best_contest_rating"] = max(ratings)

    # Prepare final JSON output
    user_data = {
        "handle": user_info["username"],
        "total_solved": total_solved,
        "easy_solved": problem_counts["Easy"],
        "medium_solved": problem_counts["Medium"],
        "hard_solved": problem_counts["Hard"],
        "contest_performance": contest_performance
    }

    return user_data

def save_to_json(data):
    """Saves the extracted data to a JSON file."""
    filename = f"{data['handle']}_leetcode.json"
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"\nData saved in {filename}")

if __name__ == "__main__":
    username = input("Enter LeetCode username: ")
    user_data = get_leetcode_data(username)
    print("\nFinal JSON Output:")
    print(json.dumps(user_data, indent=4))
    save_to_json(user_data)
