#!/usr/bin/env python3
"""
Resume Tailor Web App

A web interface for the resume tailoring tool that customizes LaTeX resumes
based on job descriptions using AI analysis.
"""

import os
import json
import datetime
import tempfile
import subprocess
import re
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
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

def customize_resume_with_approved(original_latex, approved_changes, original_analysis):
    """Customize resume with only the user-approved changes.
    
    Args:
        original_latex: Original LaTeX content of resume
        approved_changes: Dictionary of user-approved changes
        original_analysis: Original full analysis from Claude
        
    Returns:
        str: Modified LaTeX content
    """
    # Create a custom prompt that only includes approved changes
    prompt = f"""
    You are an expert LaTeX resume editor. Your task is to modify a LaTeX resume based on the following APPROVED changes.
    
    # Original Resume (LaTeX format):
    ```latex
    {original_latex}
    ```
    
    # APPROVED CHANGES TO INCORPORATE:
    
    """
    
    if approved_changes.get('key_skills'):
        prompt += "## Key Skills to Emphasize:\n"
        for skill in approved_changes['key_skills']:
            prompt += f"- {skill}\n"
        prompt += "\n"
    
    if approved_changes.get('missing_skills'):
        prompt += "## Missing Skills to Add (only if the candidate genuinely has these skills):\n"
        for skill in approved_changes['missing_skills']:
            prompt += f"- {skill}\n"
        prompt += "\n"
    
    if approved_changes.get('title_suggestions'):
        prompt += "## Job Title Modifications:\n"
        for original, suggested in approved_changes['title_suggestions'].items():
            prompt += f"- Change '{original}' to '{suggested}'\n"
        prompt += "\n"
    
    if approved_changes.get('experience_suggestions'):
        prompt += "## Experience Description Modifications:\n"
        for section, content in approved_changes['experience_suggestions'].items():
            prompt += f"- For section '{section}':\n  {content}\n"
        prompt += "\n"
    
    if approved_changes.get('content_additions'):
        prompt += "## Content to Add:\n"
        for section, content in approved_changes['content_additions'].items():
            prompt += f"- In section '{section}':\n  {content}\n"
        prompt += "\n"
    
    prompt += """
    Please modify the LaTeX resume to incorporate ONLY these approved suggestions. Focus on:
    1. Making the changes as requested
    2. Ensuring the modifications are subtle and natural
    3. Keeping the resume formatting intact and professional
    4. Making sure the resume remains a single page
    
    Return ONLY the complete modified LaTeX code with no additional comments or explanations. The code should be valid LaTeX that will compile correctly.
    """
    
    # Use the Claude API to customize the resume
    response = tailor.client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4000,
        temperature=0.2,
        system="You are an expert LaTeX editor. Return only valid LaTeX code with no additional text.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract LaTeX content
    response_text = response.content[0].text
    
    # Strip any markdown code blocks if present
    latex_content = response_text
    if "```latex" in latex_content:
        latex_content = re.search(r'```latex\n([\s\S]*?)\n```', latex_content).group(1)
    elif "```" in latex_content:
        latex_content = re.search(r'```\n([\s\S]*?)\n```', latex_content).group(1)
    
    return latex_content

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
                # Read the original resume
                original_content = tailor.read_latex_resume(file_path)
                
                # Analyze the job description instead of directly tailoring
                analysis = tailor.analyze_job_description(job_description, original_content)
                
                # Store analysis in session for review
                session['analysis'] = analysis
                session['resume_file_path'] = file_path
                session['job_description'] = job_description
                session['job_title'] = job_title
                session['company'] = company
                
                # Redirect to review page
                return redirect(url_for('review_changes'))
                
            except Exception as e:
                flash(f'Error analyzing resume: {str(e)}')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a .tex file')
            return redirect(request.url)
            
    return render_template('tailor.html')

@app.route('/review', methods=['GET', 'POST'])
def review_changes():
    """Review and approve suggested changes."""
    # Check if we have analysis data in the session
    if 'analysis' not in session:
        flash('No resume analysis found. Please start over.')
        return redirect(url_for('tailor_resume'))
    
    # Get data from session
    analysis = session['analysis']
    resume_file_path = session['resume_file_path']
    job_description = session['job_description']
    job_title = session['job_title']
    company = session['company']
    
    # For POST requests, process approved changes
    if request.method == 'POST':
        # Get user-approved changes
        approved_changes = {
            'key_skills': [skill for skill in analysis.get('key_skills', []) 
                           if f"skill_{analysis['key_skills'].index(skill)}" in request.form],
            'missing_skills': [skill for skill in analysis.get('missing_skills', []) 
                              if f"missing_{analysis['missing_skills'].index(skill)}" in request.form],
            # Title suggestions removed - not allowing job title changes
            'title_suggestions': {},  # Empty - no title changes allowed
            'experience_suggestions': {k: v for k, v in analysis.get('experience_suggestions', {}).items() 
                                      if f"exp_{k.replace(' ', '_')}" in request.form},
            'content_additions': {k: v for k, v in analysis.get('content_additions', {}).items() 
                                 if f"add_{k.replace(' ', '_')}" in request.form}
        }
        
        # Create a custom prompt for resume customization with only approved changes
        original_content = tailor.read_latex_resume(resume_file_path)
        
        try:
            # Use the customize_resume_with_approved method we'll add to ResumeTailor
            tailored_content = customize_resume_with_approved(original_content, approved_changes, analysis)
            
            # Validate the LaTeX
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, "resume_temp.tex")
                
                # Write content to temporary file
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(tailored_content)
                
                # Try to compile
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, temp_file],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    flash("LaTeX compilation failed. Please try again with different selections.")
                    return redirect(url_for('review_changes'))
            
            # Save the tailored resume
            new_filename = f"tailored_{os.path.basename(resume_file_path)}"
            output_path = os.path.join(tailor.resumes_dir, new_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(tailored_content)
            
            # Create PDF
            pdf_basename = os.path.splitext(new_filename)[0]
            pdf_output = os.path.join(tailor.resumes_dir, f"{pdf_basename}.pdf")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_tex = os.path.join(temp_dir, f"{pdf_basename}.tex")
                with open(temp_tex, "w", encoding="utf-8") as f:
                    f.write(tailored_content)
                
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, temp_tex],
                    capture_output=True,
                    check=False
                )
                
                temp_pdf = os.path.join(temp_dir, f"{pdf_basename}.pdf")
                if os.path.exists(temp_pdf):
                    import shutil
                    shutil.copy2(temp_pdf, pdf_output)
            
            # Add to applications log
            job_entry = {
                "id": len(tailor.applications) + 1,
                "date_created": datetime.datetime.now().isoformat(),
                "original_resume": str(resume_file_path),
                "tailored_resume": str(output_path),
                "pdf_resume": pdf_output if os.path.exists(pdf_output) else None,
                "job_title": job_title or "Untitled Position",
                "applied": False,
                "application_date": None,
                "company": company,
                "job_link": None,
                "notes": "Created with user-approved changes"
            }
            
            tailor.applications.append(job_entry)
            tailor._save_applications_log()
            
            # Clear session data
            for key in ['analysis', 'resume_file_path', 'job_description', 'job_title', 'company']:
                if key in session:
                    session.pop(key)
            
            # Redirect to the result page
            return redirect(url_for('result', application_id=job_entry['id']))
            
        except Exception as e:
            flash(f'Error tailoring resume with approved changes: {str(e)}')
            return redirect(url_for('review_changes'))
    
    # Render the review template for GET requests
    return render_template('review.html', 
                          analysis=analysis, 
                          resume_file_path=resume_file_path,
                          job_title=job_title,
                          company=company)

@app.route('/applications')
def list_applications():
    """List all applications with optional filtering and searching."""
    applications = tailor.applications.copy()
    
    # Filter by application status
    filter_param = request.args.get('filter', 'all')
    if filter_param == 'applied':
        applications = [app for app in applications if app.get('applied', False)]
    elif filter_param == 'not_applied':
        applications = [app for app in applications if not app.get('applied', False)]
    
    # Search functionality
    search_query = request.args.get('search', '').lower()
    if search_query:
        filtered_apps = []
        for app in applications:
            job_title = app.get('job_title', '').lower()
            company = app.get('company', '').lower()
            
            if search_query in job_title or search_query in company:
                filtered_apps.append(app)
        applications = filtered_apps
    
    # Sort by newest first (assuming date_created is an ISO format string)
    applications.sort(key=lambda x: x.get('date_created', ''), reverse=True)
    
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
        
    # Redirect back to the result page instead of the applications list
    return redirect(url_for('result', application_id=application_id))

@app.route('/quick_update/<int:application_id>', methods=['POST'])
def quick_update_application(application_id):
    """Quick update for application status (applied/not applied)."""
    # Get the applied status from the form
    applied_value = request.form.get('applied', '').lower()
    applied = applied_value == 'true' or applied_value == 'on' or applied_value == '1'
    
    # Find the application to preserve other fields
    application = None
    for app in tailor.applications:
        if app['id'] == application_id:
            application = app
            break
            
    if not application:
        flash('Application not found')
        return redirect(url_for('list_applications'))
    
    # Update the status, preserving other fields
    success = tailor.update_application_status(
        application_id,
        applied=applied,
        company=application.get('company'),
        job_link=application.get('job_link'),
        notes=application.get('notes')
    )
    
    if success:
        status_text = "applied" if applied else "not applied"
        flash(f'Application marked as {status_text}')
    else:
        flash('Failed to update application')
        
    # Redirect back to the applications list
    return redirect(url_for('list_applications'))

@app.route('/bulk_actions', methods=['POST'])
def bulk_actions():
    """Handle bulk actions on multiple applications."""
    action = request.form.get('action', '')
    selected_ids_str = request.form.get('selected_ids', '')
    
    if not selected_ids_str:
        flash('No applications selected')
        return redirect(url_for('list_applications'))
        
    selected_ids = [int(id_str) for id_str in selected_ids_str.split(',') if id_str.strip()]
    
    if action == 'apply' or action == 'unapply':
        applied = (action == 'apply')
        updated_count = 0
        
        for app_id in selected_ids:
            # Find the application to preserve other fields
            application = None
            for app in tailor.applications:
                if app['id'] == app_id:
                    application = app
                    break
                    
            if application:
                success = tailor.update_application_status(
                    app_id,
                    applied=applied,
                    company=application.get('company'),
                    job_link=application.get('job_link'),
                    notes=application.get('notes')
                )
                if success:
                    updated_count += 1
        
        status_text = "applied" if applied else "not applied"
        flash(f'Updated {updated_count} applications to {status_text}')
    
    elif action == 'delete':
        # This is a bit trickier as the ResumeTailor class doesn't have a built-in delete method
        # We'll need to modify the applications list directly
        original_count = len(tailor.applications)
        tailor.applications = [app for app in tailor.applications if app['id'] not in selected_ids]
        deleted_count = original_count - len(tailor.applications)
        
        # Save the updated applications log
        tailor._save_applications_log()
        
        flash(f'Deleted {deleted_count} applications')
    
    return redirect(url_for('list_applications'))

if __name__ == '__main__':
    app.run(debug=True)