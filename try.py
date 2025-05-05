from flask import Flask, request, jsonify, render_template
import os
import ast
import json
from werkzeug.utils import secure_filename
# from resume_text.main import resume_extractor
from LinkedIn.main import linkedin_extractor
from dataCompare.main import compare_data

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def upload_form():
    return render_template('upload_resume.html')

@app.route('/parse_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get dummy resume data for testing
        resume_data = {
            "name": "PATEL PRITKUMAR NARESHBHAI",
            "linkedin_id": "prit44421",
            "contact_info": {
                "email": "2023ucs0106@iitjammu.ac.in",
                "phone": "+91-9313265834",
                "linkedin": "https://www.linkedin.com/in/prit44421/",
                "location": "Indian Institute Of Technology, Jammu"
            },
            "summary": "",
            "experience": [],
            "education": [
                {
                "school": "Indian Institute of Technology, Jammu",
                "degree": "B.tech (CSE)",
                "field_of_study": "Computer Science Engineering",
                "dates": "2027",
                "grades": "8.63 (Current)"
                },
                {
                "school": "Ascent School of Science",
                "degree": "12th Standard",
                "field_of_study": "",
                "dates": "2023",
                "grades": "80.46%"
                },
                {
                "school": "Bright Tulips International School",
                "degree": "10th Standard",
                "field_of_study": "",
                "dates": "2020",
                "grades": "68.83%"
                }
            ],
            "skills": [
                "Python",
                "C/C++",
                "Git",
                "Jupyter Notebook",
                "Google Colab",
                "Onshape",
                "Pandas",
                "Numpy",
                "scikit-learn",
                "Tensorflow",
                "Pytorch",
                "Keras",
                "HTML",
                "CSS",
                "MongoDB",
                "JavaScript",
                "React",
                "SQL",
                "Node.JS",
                "Express.JS",
                "YOLOv5",
                "EasyOCR",
                "Pyzbar",
                "Groq API",
                "OpenCV",
                "Selenium",
                "Tesseract OCR",
                "NLP",
                "API",
                "Web Crawling",
                "Flask"
            ],
            "certifications": [],
            "projects": [
                {
                "title": "Flipkart Grid 6.0",
                "description": "Developed an Image-Based Product Information Extraction and Fruit Freshness Prediction System\n– Tools & technologies used: YOLOv5, EasyOCR, Pyzbar, Groq API, TensorFlow, Keras, OpenCV\n– Built a system to predict fruit freshness using computer vision and deep learning, achieving 89% accuracy.\n– Developed a system to count products and extract information using OCR and used an LLM to refine and structure\ntext from images.",
                "technologies": [
                    "YOLOv5",
                    "EasyOCR",
                    "Pyzbar",
                    "Groq API",
                    "TensorFlow",
                    "Keras",
                    "OpenCV"
                ]
                },
                {
                "title": "Document Identity Aggregator",
                "description": "Creating a system to aggregate and verify CV data using web crawling, OCR, and NLP to detect inconsistencies.\n– Tools & technologies used: Selenium, Tesseract OCR, NLP, API‘s, Web Crawling\n– Developing a system to aggregate and cross-verify candidate CV data from multiple online sources to detect\ninconsistencies and validate authenticity.",
                "technologies": [
                    "Selenium",
                    "Tesseract OCR",
                    "NLP",
                    "API",
                    "Web Crawling"
                ]
                },
                {
                "title": "YouTube to Spotify Playlist Converter",
                "description": "Developed a webapp to effortlessly transfer playlists between YouTube and Spotify..\n– Tools & technologies used: Python, Flask, HTML, CSS, Spotify API, YouTube API\n– Built a web app that converts YouTube playlists to Spotify and vice versa, streamlining music migration across\nplatforms.\n– Implemented API authentication and token management to handle user accounts securely.",
                "technologies": [
                    "Python",
                    "Flask",
                    "HTML",
                    "CSS",
                    "Spotify API",
                    "YouTube API"
                ]
                }
            ],
            "languages": [],
            "achievements": [
                "Solved 300+ coding problems on LeetCode and Codeforces.",
                "Awarded \"Developer of the Month\" at IIT Jammu.",
                "Won a Silver Medal in NanoNavigator at IIT Roorkee."
            ]
            }
        
        # Call extractors and store results
        # if 'linkedin_id' in resume_data:
        #     linkedin_data = linkedin_extractor("direct", resume_data['linkedin_id'])
        # else:
        #     linkedin_data = linkedin_extractor("search",
        #                                     resume_data.get('name', 'Test User'),
        #                                     resume_data.get('school', 'Test University'))
        # Store all data in a combined JSON file
        with open(r"C:\prit\coding\projects\MiniProject\forgery_detection\LinkedIn\services\outputs\profile_json\prit44421_profile.json", 'r') as f:
            linkedin_data = json.load(f)
        print(linkedin_data)
        output_data = {
            'resume': resume_data,
            'linkedin': linkedin_data,
            # 'orcid': orcid_data
        }
        
        # Save to file
        output_path = os.path.join('data', 'profile_data.json')
        os.makedirs('data', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        

        print("Calling data compare funtion")
        # Call data comparison using LLM
        comparison_result = compare_data(resume_data,linkedin_data)
        if 'linkedin_id' in resume_data:
            report_path = fr"C:\prit\coding\projects\MiniProject\forgery_detection\dataCompare\data\reports\{resume_data['linkedin_id']}.json"
        else:
            report_path = fr"C:\prit\coding\projects\MiniProject\forgery_detection\dataCompare\data\reports\{resume_data['name']}.json"
        # Save comparison report
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(str(comparison_result))
        print("Saved data compare")
        # Read the markdown report
        # report_path = os.path.join('dataCompare', 'data', 'reports', 'prit44421.md')
        # report_path = fr"C:\prit\coding\projects\MiniProject\forgery_detection\dataCompare\data\reports\{}"
        with open(report_path, 'r') as f:
            report_content = f.read()
        print(type(report_content))
        # Convert string representation of dictionary to actual dictionary
        report_content = ast.literal_eval(report_content)
        print(type(report_content))

        # Render results template with data
        return render_template('upload_resume.html',
                           result={
                               'report_content': report_content
                           })
        
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
