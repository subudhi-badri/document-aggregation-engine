from pdf2image import convert_from_path

pdf_path = r"C:\prit\coding\projects\MiniProject\forgery_detection\resume_text\PritPatelResume.pdf"
poppler_path =  r"C:\prit\coding\projects\MiniProject\forgery_detection\resume_text\poppler-24.08.0\Library\bin"

try:
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    print(f"✅ Converted {len(images)} pages to image.")
except Exception as e:
    print("[❌] Conversion failed:",e)