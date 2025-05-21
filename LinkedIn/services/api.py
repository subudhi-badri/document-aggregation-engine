import google.generativeai as genai
from LinkedIn.commander import GENAI_API_KEY
import json

def beautifier(linkedin_id):
  filename = fr"C:\prit\coding\projects\MiniProject\forgery_detection\LinkedIn\services\outputs\profile_json\{linkedin_id}_profile.json"
  with open(filename, "r", encoding='utf-8') as file:
      response = file.read()
      # Extract the JSON part from the response
      json_data = response.split('''"text": "''')[1]
      json_data = json_data.split('''"role": "model"''')[0]
      json_data=json_data[0:-47]
      json_data = json_data.replace("\\","")
      data = json.loads(json_data)  # Load the valid JSON
  print(f"Saved JSON to {linkedin_id}_profile.json")

  # Save the modified data back to the JSON file
  with open(filename, "w", encoding='utf-8') as file:
      json.dump(data, file, ensure_ascii=False, indent=4)



genai.configure(api_key=GENAI_API_KEY)
model=genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  system_instruction='''## System Prompt: LinkedIn HTML Data Extraction

    You are a highly accurate LinkedIn data extractor. You will receive raw HTML content scraped from a LinkedIn profile page as input. Your task is to extract structured data from this HTML and return it in a well-formatted JSON string.

    **Input:** Raw HTML content of a LinkedIn profile page (string).

    **Output:** A JSON string representing the extracted LinkedIn profile data.  The JSON should adhere to the following structure, with values set to `null` or an empty string if the corresponding data is not found in the HTML.  Maintain consistency with the specified field names and types. Prioritize accuracy and completeness, handling variations in LinkedIn's HTML structure robustly and gracefully managing missing elements MOST IMPORTANT DO NOT GIVE ANY NEW LINE CHARECTOR OR ANY OTHER SPECIAL CHARACTOR AS A PLAIN TEXT.

    ```json
    {
      {"name":"string","headline":"string","about":"string","location":"string","profile_url":"string","experience":[{"title":"string","company":"string","dates":"string","description":"string","location":"string"}],"education":[{"school":"string","degree":"string","field_of_study":"string","dates":"string"}],"skills":["string"],"certifications":[{"name":"string","issuing_authority":"string","dates":"string"}],"volunteer_experience":[{"role":"string","organization":"string","dates":"string","description":"string","cause":"string"}],"interests":["string"],"profile_image_url":"string"}

    }'''
  )




def json_generator(linkedin_id,html_content):
    print(f"Extracting JSON file for {linkedin_id}")
    response = model.generate_content(html_content)
    print(response)
    filename = fr"C:\prit\coding\projects\MiniProject\forgery_detection\LinkedIn\services\outputs\profile_json\{linkedin_id}_profile.json"
    with open(filename, "w", encoding='utf-8') as file:
      file.write(str(response))
      print(f"Successfully saved JSON to {filename}")
    beautifier(linkedin_id)



