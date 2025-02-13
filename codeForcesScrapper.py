import requests
import json

def get_codeforces_data(username):
    """Fetches Codeforces user rating and number of solved problems from API."""
    # Fetch user info
    user_info_url = f"https://codeforces.com/api/user.info?handles={username}"
    user_info_response = requests.get(user_info_url)
    
    if user_info_response.status_code != 200:
        return {"error": "Failed to fetch user info from API"}
    
    user_info_data = user_info_response.json()
    if user_info_data["status"] != "OK":
        return {"error": "Invalid API response for user info"}
    
    user_info = user_info_data["result"][0]
    
    # Fetch user submissions
    submissions_url = f"https://codeforces.com/api/user.status?handle={username}"
    submissions_response = requests.get(submissions_url)
    
    if submissions_response.status_code != 200:
        return {"error": "Failed to fetch submissions from API"}
    
    submissions_data = submissions_response.json()
    if submissions_data["status"] != "OK":
        return {"error": "Invalid API response for submissions"}
    
    # Count unique solved problems
    solved_problems = set()
    for submission in submissions_data["result"]:
        if submission["verdict"] == "OK":
            problem = submission["problem"]
            # Check if 'contestId' and 'index' exist in the problem object
            if "contestId" in problem and "index" in problem:
                problem_id = f"{problem['contestId']}{problem['index']}"  # Unique problem identifier
                solved_problems.add(problem_id)
    
    # Prepare final data
    user_data = {
        "handle": user_info["handle"],
        "rating": user_info.get("rating", "N/A"),
        "problems_solved": len(solved_problems)
    }
    return user_data

def save_to_json(data):
    """Saves the data as a JSON file."""
    filename = f"{data['handle']}_codeforces.json"
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"\nData saved in {filename}")

if __name__ == "__main__":
    username = input("Enter Codeforces username: ")
    user_data = get_codeforces_data(username)
    print("\nFinal data:")
    print(json.dumps(user_data, indent=4))
    save_to_json(user_data)