# Project Setup and Requirements

## Setup API Keys and Cookies
- Setup API keys in `LinkedIn/commander.py` and in `resume_text/main.py` (set `GENAI_API_KEY`).
- Setup LinkedIn cookies in `LinkedIn/commander.py`.

## Download and Install Tesseract OCR
Download Tesseract OCR from the following link and install it:
[Tesseract OCR alternative download - SourceForge](https://sourceforge.net/projects/tesseract-ocr-alt/files/)

Make sure to note the installation path (default is usually `C:\Program Files\Tesseract-OCR\tesseract.exe`) and update the path in `resume_text/main.py` if needed:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```


Make sure the path to Poppler binaries is correctly set in `resume_text/main.py`:
```python
POPPLER_PATH = r"C:\prit\coding\projects\MiniProject\forgery_detection\resume_text\poppler-24.08.0\Library\bin"
```

## Python Dependencies
Install the required Python packages using pip. You can install the packages listed in `LinkedIn/requirements.txt` plus additional dependencies used in the project:

```bash
pip install -r LinkedIn/requirements.txt
pip install pytesseract pdf2image pillow python-docx
```

The main dependencies include:
- Flask==2.0.3
- google-generativeai==0.1.0
- selenium==4.1.0
- webdriver-manager==3.5.2
- pytesseract
- pdf2image
- pillow
- python-docx

## Running the Application
Run the Flask app using:

```bash
python app.py
```