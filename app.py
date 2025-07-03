# app.py
from flask import Flask, request, render_template, jsonify, redirect, url_for, send_file, flash
from flask_cors import CORS  # 1. Import the CORS library
from logging_config import setup_logging

setup_logging()

import os
import uuid
from datetime import datetime, timezone # Import timezone for the fix
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from weasyprint import HTML, CSS
from io import BytesIO
from bson.objectid import ObjectId # This might be needed if your IDs are not strings

# --- Correctly import your services ---
from tasks import process_verification_job, init_celery
from resume_text.main import resume_extractor

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = os.urandom(24) # Or any other secret key
init_celery(app) # Link celery to the Flask app

# 2. Initialize CORS on your app.
# This tells your app to accept requests from any origin for /api/* endpoints.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Create Folders ---
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data_output/comparison_reports', exist_ok=True)

# --- DB Connection (Update with your actual connection string if needed) ---
client = MongoClient("mongodb://localhost:27017/")
db = client['document_aggregation']
jobs_collection = db['jobs']


@app.route('/')
def upload_form():
    """Renders the main file upload page."""
    return render_template('upload_resume.html')


@app.route('/parse_resume', methods=['POST'])
def batch_create_jobs_route():
    """
    Handles batch uploads of resumes. It loops through each file,
    creates a separate job for it, and dispatches it to Celery.
    """
    # Use request.files.getlist() to get all files from the input
    uploaded_files = request.files.getlist("resumes")

    if not uploaded_files or uploaded_files[0].filename == '':
        flash("No files were selected for upload.", "error")
        return redirect(url_for('upload_form'))

    successful_uploads = 0
    failed_uploads = 0

    # --- Loop through each uploaded file ---
    for file in uploaded_files:
        if file and file.filename:
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # --- Run the synchronous part (resume parsing) ---
                app.logger.info(f"Starting initial parsing for: {filename}")
                resume_data = resume_extractor(filepath)
                if not resume_data:
                    app.logger.error(f"Failed to parse resume: {filename}. Skipping.")
                    failed_uploads += 1
                    continue # Move to the next file

                # --- Create a unique job for this single file ---
                job_id = str(uuid.uuid4())
                job_document = {
                    "_id": job_id,
                    "created_at": datetime.now(timezone.utc),
                    "resume_file": filename,
                    "status": "PENDING",
                    "data": {
                        "resume": resume_data,
                        "sources": {
                            "linkedin": {"status": "PENDING"},
                            "github": {"status": "PENDING"},
                            "leetcode": {"status": "PENDING"},
                            "kaggle": {"status": "PENDING"}
                        }
                    },
                    "final_report": None
                }
                jobs_collection.insert_one(job_document)
                
                # --- Dispatch this single job to Celery ---
                process_verification_job.delay(job_id)
                successful_uploads += 1
                app.logger.info(f"Successfully queued job {job_id} for {filename}.")

            except Exception as e:
                app.logger.error(f"An unexpected error occurred while processing file {file.filename}: {e}")
                failed_uploads += 1

    # After the loop, flash a summary message and redirect to the history page
    flash(f"Successfully queued {successful_uploads} jobs. {failed_uploads} files failed during initial processing.", "success")
    return redirect(url_for('history_page'))


@app.route('/results/<job_id>')
def results_page(job_id):
    """Renders the page that will poll for results."""
    return render_template('results.html', job_id=job_id)


@app.route('/status/<job_id>')
def job_status(job_id):
    """API endpoint for the frontend to get the latest job status."""
    job = jobs_collection.find_one({"_id": job_id})
    # Convert MongoDB's ObjectId to a string for JSON serialization if needed
    if job and '_id' in job:
        job['_id'] = str(job['_id'])
    return jsonify(job)


@app.route('/history')
def history_page():
    """Renders the main shell for the history page. Data is loaded via API."""
    # We get the sort_by parameter here just to pass it to the template,
    # so the dropdown can show the correct initial value.
    sort_by = request.args.get('sort', 'date_desc')
    return render_template('history.html', sort_by=sort_by)


@app.route('/report/<job_id>/pdf')
def download_pdf_report(job_id):
    """
    Fetches job data, renders it into a PDF-specific HTML template,
    and returns it as a downloadable file.
    """
    try:
        job = jobs_collection.find_one({"_id": str(job_id)})
        if not job or not job.get('final_report'):
            return jsonify({"error": "Report not found or not yet complete."}), 404

        # Render the dedicated PDF template with the job data
        # We need to pass the base_url for WeasyPrint to find our CSS file
        rendered_html = render_template('report_pdf.html', job=job)
        
        # Create a PDF in memory
        pdf_bytes = HTML(string=rendered_html, base_url=request.base_url).write_pdf()
        
        # Create a friendly filename
        resume_name = job.get('resume_file', 'report').split('.')[0]
        pdf_filename = f"Verification_Report_{resume_name}.pdf"

        # Return the PDF as a downloadable attachment
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        app.logger.error(f"Error generating PDF for job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while generating the PDF report."}), 500


# This is the new route for handling deletion
@app.route('/job/delete/<job_id>', methods=['POST'])
def delete_job_route(job_id):
    """Deletes a specific job document from the MongoDB collection."""
    if not job_id:
        flash("Invalid job ID provided.", "error")
        return redirect(url_for('history_page'))
    try:
        # Ensure job_id is a string
        job_id = str(job_id)
        delete_result = jobs_collection.delete_one({'_id': job_id})
        if delete_result.deleted_count == 1:
            flash("Job report successfully deleted.", "success")
        else:
            flash("Job report not found.", "warning")
    except Exception as e:
        app.logger.error(f"Error deleting job {job_id}: {e}", exc_info=True)
        flash("An error occurred while trying to delete the job report.", "error")
    return redirect(url_for('history_page'))


@app.route('/api/history')
def api_history():
    """API endpoint that returns a clean, serialized list of all jobs."""
    sort_by = request.args.get('sort', 'date_desc')

    try:
        jobs_from_db = list(jobs_collection.find({}, {"final_report": 0}))

        # Safe Sorting in Python
        if sort_by == 'score_desc':
            jobs_from_db.sort(key=lambda j: j.get('consistency_score', -1), reverse=True)
        elif sort_by == 'score_asc':
            jobs_from_db.sort(key=lambda j: j.get('consistency_score', 999), reverse=False)
        elif sort_by == 'date_asc':
            jobs_from_db.sort(key=lambda j: j.get('created_at', datetime.min), reverse=False)
        else: # Default 'date_desc'
            jobs_from_db.sort(key=lambda j: j.get('created_at', datetime.min), reverse=True)

        # Bulletproof Serialization
        serialized_jobs = []
        for job in jobs_from_db:
            clean_job = {
                '_id': str(job.get('_id')),
                'resume_file': job.get('resume_file'),
                'status': job.get('status'),
                'consistency_score': job.get('consistency_score'),
                'created_at': job.get('created_at').isoformat() if job.get('created_at') else None
            }
            serialized_jobs.append(clean_job)

        return jsonify(jobs=serialized_jobs)
        
    except Exception as e:
        app.logger.error(f"API error fetching job history: {e}", exc_info=True)
        return jsonify(error="Could not fetch job history."), 500


@app.route('/compare')
def compare_page():
    """
    Renders a side-by-side comparison page for selected candidates.
    """
    # Get the list of job_ids from the URL query parameters
    # e.g., /compare?job_ids=id1&job_ids=id2
    job_ids = request.args.getlist('job_ids')

    if not job_ids or len(job_ids) < 2:
        flash("Please select at least two completed reports to compare.", "warning")
        return redirect(url_for('history_page'))

    try:
        # Fetch the full documents for the selected jobs
        # We need the final_report, so we don't exclude it here.
        jobs_to_compare = list(jobs_collection.find({"_id": {"$in": job_ids}}))

        # Check if all requested jobs were found and are complete
        if len(jobs_to_compare) != len(job_ids) or any(not j.get('final_report') for j in jobs_to_compare):
             flash("One or more selected reports were not found or are incomplete.", "error")
             return redirect(url_for('history_page'))

        return render_template('compare.html', jobs=jobs_to_compare)

    except Exception as e:
        app.logger.error(f"Error fetching jobs for comparison: {e}", exc_info=True)
        flash("An error occurred while preparing the comparison.", "error")
        return redirect(url_for('history_page'))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) # Important: use_reloader=False when running Celery