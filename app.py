from flask import Flask, request, jsonify, render_template
import os
import ast
import json
from werkzeug.utils import secure_filename
from resume_text.main import resume_extractor
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
        resume_data = resume_extractor(filepath)
        print(resume_data)
        
        
        # Call extractors and store results
        if 'linkedin_id' in resume_data:
            # If LinkedIn ID is present, use direct extraction
            linkedin_id = resume_data['linkedin_id'].split('/')[-2]
            linkedin_data = linkedin_extractor("direct", linkedin_id)
        else:
            linkedin_data = linkedin_extractor("search",
                                            resume_data.get('name', 'Test User'),
                                            resume_data.get('school', 'Test University'))
        # Store all data in a combined JSON file
        output_data = {
            'resume': resume_data,
            'linkedin': linkedin_data,
            # 'orcid': orcid_data
        }
        
        # Save to file
        output_path = os.path.join('data', f'{filename}_extracted.json')
        os.makedirs('data', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        

        print("Calling data compare funtion")
        # Call data comparison using LLM
        print("resume_data",type(resume_data))
        print("linkedin data",type(linkedin_data))
        print("resume data",resume_data)
        print("linkedin data",linkedin_data)
        if isinstance(resume_data, tuple):
            resume_data = resume_data[0]
        if isinstance(linkedin_data, tuple):
            linkedin_data = linkedin_data[0]
        print("resume data",type(resume_data))
        print("linkedin data",type(linkedin_data))
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
