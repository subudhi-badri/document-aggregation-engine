import os
import json
import pytesseract
from PIL import Image
import docx
from io import BytesIO
from pdf2image import convert_from_path
import google.generativeai as genai

# === CONFIG ===
GENAI_API_KEY = "kjbjkbjk"  # Replace with yours
POPPLER_PATH = r"C:\prit\coding\projects\MiniProject\forgery_detection\resume_text\poppler-24.08.0\Library\bin"  # Change to your Poppler bin path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe" 

genai.configure(api_key=GENAI_API_KEY)
print(GENAI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction='''Extract structured resume info in the following JSON format and write "" empty string instead of null:

{
    "name": "string",
    "linkedin_id": "string",
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
)

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

def json_generator(resume_id, resume_text):
    prompt = f"""
You are a resume parser. Return ONLY a valid JSON.

---- RESUME CONTENT ----
{resume_text}
---- END ----
"""
    try:
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        with open(f"resume_text/output/{resume_id}_raw_ai.txt", "w", encoding="utf-8") as f:
            f.write(ai_text)
            print(f"[✓] AI response saved to output/{resume_id}_raw_ai.txt but ye kese hua ")
        ai_text = ai_text[ai_text.find("{"): ai_text.rfind("}") + 1]
        return json.loads(ai_text)
    except Exception as e:
        print("[!] AI processing error:", e)
        return None

def resume_extractor(file_path):
    if not os.path.exists(file_path):
        print("[!] File not found.")
        return

    resume_id = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        resume_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        resume_text = extract_text_from_docx(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        resume_text = extract_text_from_image(Image.open(file_path))
    else:
        print("[!] Unsupported file type.")
        return

    os.makedirs("resume_text/output", exist_ok=True)
    with open(f"resume_text/output/{resume_id}_raw_text.txt", "w", encoding="utf-8") as f:
        f.write(resume_text)

    final_json = json_generator(resume_id, resume_text)
    if final_json:
        with open(f"resume_text/output/{resume_id}.json", "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=4, ensure_ascii=False)
        print(f"[✓] Extracted JSON saved to output/{resume_id}.json")
        return final_json
    else:
        print("[!] Failed to extract JSON")
        return None

# # === USAGE ===
# if __name__ == "__main__":
#     resume_extractor(r"C:\prit\coding\projects\MiniProject\forgery_detection\resume_text\PritPatelResume.pdf")  # replace with your file