# ==============================================================================
#  resume_text/main.py - OFFLINE VERSION WITH OLLAMA
# ==============================================================================

import os
import json
import pytesseract
from PIL import Image
import docx
from io import BytesIO
from pdf2image import convert_from_path
import google.generativeai as genai  # Import the new library
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Direct Google AI Client Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Ensure these paths are correct for your system
POPPLER_PATH = r"C:\Users\ASUS\Desktop\restart\document_aggregation\poppler-24.08.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\ASUS\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# This is the detailed instruction for the AI model
system_instruction_prompt = '''You are an expert resume parser. Your sole function is to extract structured information from the provided resume text and return it ONLY as a valid JSON object. Adhere strictly to the following format. Pay special attention to finding the LinkedIn profile URL for the "linkedin_id" field AND the GitHub username for the "github_id" field. For any fields where information is not found, use an empty string "" or an empty list []. Do not use null.
{
    "name": "string",
    "linkedin_id": "string",
    "github_id": "string",
    "leetcode_id": "string",
    "kaggle_id": "string",
    "contact_info": {"email": "string", "phone": "string", "location": "string"},
    "summary": "string",
    "experience": [{"title": "string", "company": "string", "dates": "string", "description": "string", "location": "string"}],
    "education": [{"school": "string", "degree": "string", "field_of_study": "string", "dates": "string", "grades": "string"}],
    "skills": ["string"],
    "certifications": [{"name": "string", "issuing_authority": "string", "dates": "string"}],
    "projects": [{"title": "string", "description": "string", "technologies": ["string"]}],
    "languages": ["string"],
    "achievements": ["string"]
}
'''

# --- HELPER FUNCTIONS FOR TEXT EXTRACTION (These do not need to be changed) ---

def extract_text_from_image(image):
    return pytesseract.image_to_string(image).strip()

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
    except Exception as e:
        print("[!] 300 DPI failed, retrying without dpi...")
        try:
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        except Exception as e2:
            print("[!] PDF to image failed:", e2)
            return ""
    return text.join([extract_text_from_image(img) for img in images])

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                img_data = rel.target_part.blob
                img = Image.open(BytesIO(img_data))
                text += "\n" + extract_text_from_image(img)
            except Exception as e:
                print("[!] DOCX image OCR failed:", e)
    return text.strip()

# --- GOOGLE GEMINI JSON GENERATOR FUNCTION ---
def generate_json_with_google(resume_text):
    """
    Takes raw resume text and uses the direct Google Gemini API 
    to parse it into structured JSON.
    """
    generation_config = {
        "response_mime_type": "application/json",
    }
    model = genai.GenerativeModel(
        "gemini-1.5-flash-latest",
        generation_config=generation_config
    )
    user_prompt = f"{system_instruction_prompt}\n\n--- RESUME CONTENT TO PARSE ---\n{resume_text}"
    try:
        print("[*] Calling direct Google Gemini API to parse resume...")
        response = model.generate_content(user_prompt)
        ai_response_str = response.text
        print("[*] --- Raw AI Response Received from Google ---")
        print(ai_response_str)
        print("[*] --- End of Raw AI Response ---")
        if not ai_response_str:
            print("[!] Google AI returned an empty response.")
            return None
        return json.loads(ai_response_str)
    except Exception as e:
        with open("resume_text/error.log", "a", encoding="utf-8") as logf:
            logf.write(f"[!] Error processing Google Gemini API response: {e}\n")
        print(f"[!] An error occurred while processing the Google Gemini API response: {e}")
        return None

# --- MAIN FUNCTION ---
def resume_extractor(file_path):
    if not os.path.exists(file_path):
        print("[!] File not found.")
        return {"error": "File not found."}
    resume_id = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        resume_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        resume_text = extract_text_from_docx(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        resume_text = extract_text_from_image(Image.open(file_path))
    else:
        print(f"[!] Unsupported file type: {ext}")
        return {"error": f"Unsupported file type: {ext}"}
    if not resume_text:
        print("[!] Text extraction failed. Document might be empty or unreadable.")
        return {"error": "Text extraction failed. Document might be empty or unreadable."}
    os.makedirs("resume_text/output", exist_ok=True)
    with open(f"resume_text/output/{resume_id}_raw_text.txt", "w", encoding="utf-8") as f:
        f.write(resume_text)
    # Call the new Google-based function
    final_json = generate_json_with_google(resume_text)
    if final_json:
        with open(f"resume_text/output/{resume_id}.json", "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=4, ensure_ascii=False)
        print(f"[✓] Extracted JSON saved to output/{resume_id}.json")
        return final_json
    else:
        print("[!] Failed to extract JSON using Google Gemini API.")
        return None