import json

from dataCompare.apiCaller import llm_caller
def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse JSON in file {file_path}.")
        return None


def compare_strings(string1, string2):
    # Compare two strings and return a similarity score
    result=llm_caller(f"string 1 : {string1} , string 2 : {string2}")
    print(f"string 1 : {string1} , string 2 : {string2}, result : {result}")
    return result == "1"

def compare_data(resume_data, other_data):
    # print("Comparing data...")
    comparison_result = {
        "name": {"matched": [], "unmatched": []},
        "headline": {"matched": [], "unmatched": []},
        "location": {"matched": [], "unmatched": []},
        "education": {"matched": [], "unmatched": []},
        "experience": {"matched": [], "unmatched": []},
        "skills": {"matched": [], "unmatched": []},
        "certifications": {"matched": [], "unmatched": []},
        "volunteer_experience": {"matched": [], "unmatched": []},
        "interests": {"matched": [], "unmatched": []}
    }

    def match_and_store(field, value1, value2):
        """Helper function to match and store results."""
        is_match = compare_strings(value1.lower(), value2.lower())
        if is_match:
            comparison_result[field]["matched"].append({"resume": value1, "other": value2})
        else:
            comparison_result[field]["unmatched"].append({"resume": value1, "other": value2})

    # Compare simple string fields
    simple_fields = ["name", "headline", "location"]
    for field in simple_fields:
        val1 = resume_data.get(field, "")
        val2 = other_data.get(field, "")
        if val1 and val2:
            match_and_store(field, val1, val2)
    # print("Compared Simple fields")
    # Compare education
    for edu_entry1 in resume_data.get("education", []):
        match_found = False
        for edu_entry2 in other_data.get("education", []):
            school1 = edu_entry1.get("school", "").lower()
            school2 = edu_entry2.get("school", "").lower()
            degree1 = edu_entry1.get("degree", "").lower()
            degree2 = edu_entry2.get("degree", "").lower()
            
            if compare_strings(school1, school2) and compare_strings(degree1, degree2):
                comparison_result["education"]["matched"].append({"resume": edu_entry1, "other": edu_entry2})
                match_found = True
                break
        
        if not match_found:
            comparison_result["education"]["unmatched"].append({"resume": edu_entry1})

    # Compare volunteer experience
    for vol_entry1 in resume_data.get("volunteer_experience", []):
        match_found = False
        for vol_entry2 in other_data.get("volunteer_experience", []):
            title1 = vol_entry1.get("title", "").lower()
            title2 = vol_entry2.get("title", "").lower()
            org1 = vol_entry1.get("organization", "").lower()
            org2 = vol_entry2.get("organization", "").lower()
            print(f"Comparing {title1 + ' ' + org1} with {title2 + ' ' + org2}")
            if compare_strings(title1 + " " + org1, title2 + " " + org2):
                comparison_result["volunteer_experience"]["matched"].append({"resume": vol_entry1, "other": vol_entry2})
                match_found = True
                break
        
        if not match_found:
            comparison_result["volunteer_experience"]["unmatched"].append({"resume": vol_entry1})

    # Compare experience
    for exp_entry1 in resume_data.get("experience", []):
        match_found = False
        for exp_entry2 in other_data.get("experience", []):
            title1 = exp_entry1.get("title", "").lower()
            title2 = exp_entry2.get("title", "").lower()
            company1 = exp_entry1.get("company", "").lower()
            company2 = exp_entry2.get("company", "").lower()
            print(f"Comparing {title1+" "+company1} with {title2+' '+company2}")
            if compare_strings(title1+" "+company1, title2+" "+company2):
                
                comparison_result["experience"]["matched"].append({"resume": exp_entry1, "other": exp_entry2})
                match_found = True
                break
        
        if not match_found:
            comparison_result["experience"]["unmatched"].append({"resume": exp_entry1})



    # Compare skills
    skills1 = set(resume_data.get("skills", []))
    skills2 = set(other_data.get("skills", []))
    matched_skills = skills1.intersection(skills2)
    unmatched_skills = skills1-skills2
    comparison_result["skills"]["matched"].extend(list(matched_skills))
    comparison_result["skills"]["unmatched"].extend(list(unmatched_skills))

    # Compare certifications
    for cert1 in resume_data.get("certifications", []):
        match_found = False
        for cert2 in other_data.get("certifications", []):
            if compare_strings(cert1.get("name", ""), cert2.get("name", "")):
                comparison_result["certifications"]["matched"].append({"resume": cert1, "other": cert2})
                match_found = True
                break
        if not match_found:
            comparison_result["certifications"]["unmatched"].append({"resume": cert1})

    # Compare interests
    interests1 = set(interest.lower() for interest in resume_data.get("interests", []))
    interests2 = set(interest.lower() for interest in other_data.get("interests", []))
    matched_interests = interests1.intersection(interests2)
    unmatched_interests = interests1-interests2
    comparison_result["interests"]["matched"].extend(list(matched_interests))
    comparison_result["interests"]["unmatched"].extend(unmatched_interests)
    print("comparison_result")
    print(comparison_result)
    print("exiting compare_data")
    print()
    return comparison_result


def generate_match_report(resume_data, other_data,person_id):
    comparison_result = compare_data(resume_data, other_data)
    
    report = []
    
    def format_entry(entry):
        if isinstance(entry, dict):
            return " | ".join(f"{k}: {v}" for k, v in entry.items() if v)
        elif isinstance(entry, str):
            return entry
        return "N/A"

    
    report.append("**Resume Matching Report**")
    report.append("=" * 40)

    for section, results in comparison_result.items():
        report.append(f"\n**{section.capitalize()}**")
        
        if results["matched"]:
            report.append("\nMatched:")
            for match in results["matched"]:
                if isinstance(match, dict):
                    report.append(f"  - {format_entry(match['resume'])} \n    ↔ Matched with ↔ \n  {format_entry(match['other'])}")
                else:
                    report.append(f"  - {match}")
        
        if results["unmatched"]:
            report.append("\nUnmatched:")
            for unmatched in results["unmatched"]:
                print(unmatched)
                if isinstance(unmatched, dict):
                    report.append(f"  - {format_entry(unmatched)}")
                else:
                    report.append(f"  - {unmatched}")
    with open(f"dataCompare/data/reports/{person_id}.md", "w+", encoding='utf-8') as file:
        file.write("\n".join(report))
    return "\n".join(report)




# def main():
#     person_id = "prit44421"
#     linkedin_data_file_path = rf'dataCompare\data\jsonFiles\{person_id}_profile.json'
#     other_data = load_json_file(linkedin_data_file_path)
#     resume_data_file_path = rf'dataCompare\data\jsonFiles\{person_id}_resume.json'
#     resume_data = load_json_file(resume_data_file_path)
#     print(generate_match_report(resume_data, other_data,person_id))

# main()

