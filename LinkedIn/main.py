from LinkedIn.services.full_scrapper import scrape_full_profile
from LinkedIn.services.search import search_with_name
import os
import json

def linkedin_extractor(method, identifier, school_or_company=None):
    """
    Get LinkedIn profile data either directly by ID or by searching with name
    
    Args:
        method (str): 'direct' to use LinkedIn ID directly, 'search' to search by name
        identifier (str): LinkedIn ID (for direct) or name (for search)
        school_or_company (str, optional): School/company name for search method
    
    Returns:
        dict: Profile data if successful, None if not found
        str: Error message if applicable
    """
    try:
        if method == 'direct':
            linkedin_id = identifier
        elif method == 'search':
            if not school_or_company:
                return None, "school_or_company is required for search method"
            linkedin_id = search_with_name(identifier, school_or_company)
            if not linkedin_id:
                return None, "LinkedIn profile not found"
        else:
            return None, "Invalid method - use 'direct' or 'search'"

        # Scrape the profile
        profile_infos = scrape_full_profile(linkedin_id)
        
        # Return the profile data directly
        output_file = fr"C:\prit\coding\projects\MiniProject\forgery_detection\LinkedIn\services\outputs\profile_json\{linkedin_id}_profile.json"
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                return json.load(f), None
        return None, "Profile data not found"
    
    except Exception as e:
        return None, f"Error occurred: {str(e)}"
