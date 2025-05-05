import requests
import json
import pandas as pd
import os
import mongoUploader










# Makes a request to Orcid and returns the response
def get_orcid_data(orcid_id):
    """
    Fetches data from ORCID API for a given ORCID ID
    """
    base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None










# parsing the raw_data that is given by the get_orcid_data 
# and 
def parse_orcid_data(raw_data):
    """
    Parses relevant information from ORCID API response with null checks.
    """
    if not raw_data:
        print("Error: No data received from the API.")
        return None

    parsed_data = {
        "personal-info":                    {},
        "works":                            [],
        "education":                        [],
        "employment":                       []
    }

    try:
        # Extract personal information
        personal_info =                     raw_data.get("person", {}) or {}
        name_info =                         personal_info.get("name", {}) or {}
        
        # Safely extract name components
        given_names =                       (name_info.get("given-names", {}) or {}).get("value", "")
        family_name =                       (name_info.get("family-name", {}) or {}).get("value", "")
        credit_name =                       (name_info.get("credit-name", {}) or {}).get("value", "")
        name =                              credit_name or f"{given_names} {family_name}".strip()

        parsed_data["personal-info"] = {
            "name":                         name,
            "orcid":                        (raw_data.get("orcid-identifier", {}) or {}).get("path", ""),
            "creation-date":                (raw_data.get("history", {}) or {}).get("creation-date", {}).get("value", "")
        }

        # Extract works (handle None/empty responses)
        activities_summary =                raw_data.get("activities-summary", {}) or {}
        works =                             activities_summary.get("works", {}) or {}
        works_group =                       works.get("group", []) or []
        for work in works_group:
            work_summary = (work.get("work-summary", [{}]) or [{}])[0] or {}
            parsed_data["works"].append({
                "title":                    (work_summary.get("title", {}) or {}).get("title", {}).get("value", ""),
                "doi":                      (work_summary.get("external-ids", {}) or {}).get("external-id", [{}])[0].get("external-id-value", ""),
                "type":                     work_summary.get("type", ""),
                "publication-date":         work_summary.get("publication-date", {}),
                "journal":                  (work_summary.get("journal-title", {}) or {}).get("value", "")
            })

        # Extract education
        educations =                        (activities_summary.get("educations", {}) or {}).get("affiliation-group", []) or []
        for edu in educations:
            education_summary =             (edu.get("summaries", [{}]) or [{}])[0].get("education-summary", {}) or {}
            parsed_data["education"].append({
                "organization":             (education_summary.get("organization", {}) or {}).get("name", ""),
                "department":               education_summary.get("department-name", ""),
                "role":                     education_summary.get("role-title", ""),
                "start-date":               education_summary.get("start-date", {}),
                "end-date":                 education_summary.get("end-date", {})
            })

        # Extract employment
        employments =                       (activities_summary.get("employments", {}) or {}).get("affiliation-group", []) or []
        for emp in employments:
            employment_summary =            (emp.get("summaries", [{}]) or [{}])[0].get("employment-summary", {}) or {}
            parsed_data["employment"].append({
                "organization":             (employment_summary.get("organization", {}) or {}).get("name", ""),
                "department":               employment_summary.get("department-name", ""),
                "role":                     employment_summary.get("role-title", ""),
                "start-date":               employment_summary.get("start-date", {}),
                "end-date":                 employment_summary.get("end-date", {})
            })

    except Exception as e:
        print(f"Error parsing data: {e}")
        return None

    return parsed_data










# Saves the data in a json file
def save_to_json(data, orcid_id, output_folder):
    output_file = os.path.join(output_folder, f"orcid_{orcid_id}.json")

    # Ensure the "Fetched ORCIDs" folder exists
    dir_name = os.path.dirname(output_file)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Save the parsed data as a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"Saved JSON to: {output_file}")










# The following function is used to search for ORCID IDs and other fields
# according the queries and then store them in a file locally
def search_orcid_api(query, fields, output_file="orcid_search_results.csv"):
    """
    Perform an advanced search using the ORCID API and save results in CSV format.
    """
    base_url = "https://pub.orcid.org/v3.0/csv-search/"
    headers = {
        "Accept": "text/csv"
    }
    params = {
        "q": query,
        "fl": fields
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()

        # Save the CSV response to a file
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Search results saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")










# The following function generates a query string for the ORCID API search
def generate_query(name=None, institute=None, place=None, keyword=None, exact_phrase=None):
    """
    Inputs:
        name:                           Searches for a specific name.
        institute:                      Searches for affiliations with one or more institutes.
        place:                          Searches for current institution affiliations in a specific place.
        keyword:                        Searches for a keyword in the record.
        exact_phrase:                   Searches for an exact phrase.
    """
    query_parts = []

    # Add name to query
    if name:
        query_parts.append(f'given-and-family-names:"{name}"')

    # Add institute to query
    if institute:
        if isinstance(institute, list):
            # Handle multiple institute names
            institute_query = " OR ".join([f'affiliation-org-name:"{inst}"' for inst in institute])
            query_parts.append(f"({institute_query})")
        else:
            query_parts.append(f'affiliation-org-name:"{institute}"')

    # Add place to query
    if place:
        query_parts.append(f'current-institution-affiliation-name:"{place}"')

    # Add keyword to query
    if keyword:
        query_parts.append(f'keyword:"{keyword}"')

    # Add exact phrase to query
    if exact_phrase:
        query_parts.append(f'"{exact_phrase}"')

    # Combine all parts with AND
    query = " AND ".join(query_parts)
    return query










# The following function generates a string which contains fields to be extracted from the search results
# separated by a comma
def generate_fields(orcid=False,                given_names=False, 
                    family_name=False,          current_institution=False, 
                    past_institution=False,     email=False, 
                    credit_name=False,          other_names=False):
    """
    Generates a comma-separated string of fields for the ORCID API based on user input.
    """
    fields = []

    if orcid:
        fields.append("orcid")
    if given_names:
        fields.append("given-names")
    if family_name:
        fields.append("family-name")
    if current_institution:
        fields.append("current-institution-affiliation-name")
    if past_institution:
        fields.append("past-institution-affiliation-name")
    if email:
        fields.append("email")
    if credit_name:
        fields.append("credit-name")
    if other_names:
        fields.append("other-names")

    return ",".join(fields)










def process_orcid_id(orc_id):
    output_folder = "Fetched ORCIDs"
    os.makedirs(output_folder, exist_ok=True)
    orcid_data = get_orcid_data(orc_id)  # Fetch data from ORCID
    parsed_data = parse_orcid_data(orcid_data)  # Parse the data

    save_to_json(parsed_data, orc_id, output_folder)  # Save to JSON file
    print(f"Saved data for ORCID: {orc_id} -> orcid_{orc_id}.json in Fetched ORCIDs")










def process_orcid_entries(csv_filename, num_entries):
    # Read CSV file
    df = pd.read_csv(csv_filename)

    # Ensure the ORCID column exists
    if "orcid" not in df.columns:
        print("Error: ORCID column not found in CSV.")
        return

    # Drop empty ORCID values and limit entries
    selected_orcids = df["orcid"].dropna().tolist()
    actual_entries = min(num_entries, len(selected_orcids))

    if actual_entries == 0:
        print("No valid ORCID IDs found in the CSV file.")
        return

    print(f"Processing {actual_entries} ORCID IDs...")

    # Create directory to store results
    output_folder = "Fetched ORCIDs"
    os.makedirs(output_folder, exist_ok=True)

    for orc_id in selected_orcids[:actual_entries]:
        orcid_data = get_orcid_data(orc_id)  # Fetch data from ORCID
        parsed_data = parse_orcid_data(orcid_data)  # Parse the data

        save_to_json(parsed_data, orc_id, output_folder)  # Save to JSON file
        print(f"Saved data for ORCID: {orc_id} -> orcid_{orc_id}.json in Fetched ORCIDs")










def last_function(_name, _institute):
    # Step 1: Generate the query
    if(_institute):
        query = generate_query(name = _name,
                            institute=_institute)
    else:
        query = generate_query(name = _name)

    fields = generate_fields(orcid=True, given_names=True, email=True)

    output_csv = "orcid_search_results.csv"
    output_dir = "Fetched ORCIDs"

    # Step 2: Search ORCID API and save results to CSV
    search_orcid_api(query, fields, output_csv)

    # Step 3: Process ORCID entries, parse data, and save as JSON
    num_entries = 5  # Define how many ORCID IDs to process
    process_orcid_entries(output_csv, num_entries)











def orcid_extractor(name=None, orcId=None, institute=None):
    if(orcId):
        process_orcid_id(orc_id=orcId)
        return
    
    if(name == None):
        print("Error: Name is required to fetch ORCID data.")
        return
    
    if(institute):
        last_function(name, institute)
        return
    
    last_function(name)