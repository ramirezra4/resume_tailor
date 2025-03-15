#!/usr/bin/env python3
"""
Resume Tailor Web App

A web interface for the resume tailoring tool that customizes LaTeX resumes
based on job descriptions using AI analysis.
"""

import os
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from resume_tailor import ResumeTailor

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'tex', 'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize ResumeTailor
tailor = ResumeTailor(
    api_key=os.environ.get('ANTHROPIC_API_KEY'),
    output_dir=os.environ.get('OUTPUT_DIR', './resume_output'),
    verbose=False  # Disable terminal spinner for web app
)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/tailor', methods=['GET', 'POST'])
def tailor_resume():
    """Handle resume tailoring requests."""
    if request.method == 'POST':
        # Check if resume file was uploaded
        if 'resume_file' not in request.files:
            flash('No resume file selected')
            return redirect(request.url)
            
        resume_file = request.files['resume_file']
        
        # If user submits without selecting a file
        if resume_file.filename == '':
            flash('No resume file selected')
            return redirect(request.url)
            
        # Get job description
        job_description = request.form.get('job_description', '').strip()
        job_title = request.form.get('job_title', '').strip()
        company = request.form.get('company', '').strip()
        
        if not job_description:
            flash('Job description is required')
            return redirect(request.url)
            
        if resume_file and allowed_file(resume_file.filename):
            # Save the uploaded resume file
            filename = secure_filename(resume_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(file_path)
            
            try:
                # Tailor the resume
                new_file_path = tailor.tailor_resume(
                    file_path,
                    job_description,
                    job_title=job_title,
                    company=company
                )
                
                # Get the latest application ID
                application_id = tailor.applications[-1]['id']
                
                # Redirect to the result page
                return redirect(url_for('result', application_id=application_id))
                
            except Exception as e:
                flash(f'Error tailoring resume: {str(e)}')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a .tex file')
            return redirect(request.url)
            
    return render_template('tailor.html')

@app.route('/applications')
def list_applications():
    """List all applications."""
    applications = tailor.applications
    return render_template('applications.html', applications=applications)

@app.route('/result/<int:application_id>')
def result(application_id):
    """Show the result of a tailored resume."""
    # Find the application by ID
    application = None
    for app in tailor.applications:
        if app['id'] == application_id:
            application = app
            break
            
    if not application:
        flash('Application not found')
        return redirect(url_for('home'))
        
    return render_template('result.html', application=application)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a file from the resume output directory."""
    directory = os.path.dirname(filename)
    filename = os.path.basename(filename)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/update/<int:application_id>', methods=['POST'])
def update_application(application_id):
    """Update application status."""
    applied = 'applied' in request.form
    company = request.form.get('company', '').strip()
    job_link = request.form.get('job_link', '').strip()
    notes = request.form.get('notes', '').strip()
    
    success = tailor.update_application_status(
        application_id,
        applied=applied,
        company=company,
        job_link=job_link,
        notes=notes
    )
    
    if success:
        flash('Application updated successfully')
    else:
        flash('Failed to update application')
        
    return redirect(url_for('list_applications'))

if __name__ == '__main__':
    app.run(debug=True)