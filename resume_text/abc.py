import google.generativeai as genai
import json
import os

# Configure API Key
genai.configure(api_key="replace_with_your_api_key")

def beautifier(resume_id):
    filename = r"C:\Users\nares\Downloads\Resume (1).pdf"
    with open(filename, "r", encoding='utf-8') as file:
        response = file.read()
        # Extract the JSON part from the response
        json_data = response.split('''"text": "''')[1]
        json_data = json_data.split('''"role": "model"''')[0]
        json_data = json_data[0:-47]
        json_data = json_data.replace("\\", "")
        data = json.loads(json_data)  # Load the valid JSON
    print(f"Saved JSON to {resume_id}_resume.json")

    # Save the modified data back to the JSON file
    with open(filename, "w", encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction='''## System Prompt: Resume Text Data Extraction

You are a highly accurate Resume data extractor. You will receive raw text content from a resume as input. Your task is to extract structured data from this text and return it in a well-formatted JSON string.

**Input:** Raw text content of a resume (string).

**Output:** A JSON string representing the extracted resume data. The JSON should adhere to the following structure, with values set to `null` or an empty string if the corresponding data is not found. Maintain consistency with the specified field names and types. Prioritize accuracy and completeness, handling variations in resume structures robustly.

```json
{
    "name": "string",
    "contact": {"email": "string", "phone": "string", "location": "string", "linkedin": "string"},
    "summary": "string",
    "experience": [{"title": "string", "company": "string", "dates": "string", "description": "string", "location": "string"}],
    "education": [{"school": "string", "degree": "string", "field_of_study": "string", "dates": "string"}],
    "skills": ["string"],
    "certifications": [{"name": "string", "issuing_authority": "string", "dates": "string"}],
    "projects": [{"name": "string", "description": "string", "technologies": ["string"]}],
    "languages": ["string"]
}
```'''
)

def json_generator(resume_id, resume_file_path):
    print(f"Extracting JSON file for {resume_id}")
    
    # Ensure output directory exists
    os.makedirs("services/outputs/resume_json", exist_ok=True)
    
    # Read the resume text from file
    with open(resume_file_path, "r", encoding='utf-8') as file:
        resume_text = file.read()
    
    response = model.generate_content(resume_text)
    filename = f"services/outputs/resume_json/{resume_id}_resume.json"
    
    with open(filename, "w", encoding='utf-8') as file:
        file.write(str(response))
    
    # beautifier(resume_id)

if __name__ == "__main__":
    resume_id = input("Enter Resume ID: ")
    resume_file_path = r"C:\Users\nares\Downloads\Resume (1).pdf"
    json_generator(resume_id, resume_file_path)