#!/usr/bin/env python3
"""
Resume Tailoring Tool

A command-line utility that customizes a LaTeX resume based on job descriptions
using AI analysis to improve ATS compatibility and interview chances.
"""

import os
import sys
import argparse
import json
import logging
import datetime
import subprocess
import tempfile
import anthropic
import re
import time
import threading
import itertools
from pathlib import Path


class Spinner:
    """A simple terminal spinner for long-running processes."""
    
    def __init__(self, message="Working", delay=0.1):
        """Initialize the spinner.
        
        Args:
            message: The message to display next to the spinner.
            delay: Time between spinner updates in seconds.
        """
        self.message = message
        self.delay = delay
        self.spinner_cycle = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.spinner_thread = None
    
    def spin(self):
        """The spinner animation function that runs in a thread."""
        while self.running:
            sys.stdout.write(f"\r{next(self.spinner_cycle)} {self.message}")
            sys.stdout.flush()
            time.sleep(self.delay)
    
    def start(self, message=None):
        """Start the spinner animation.
        
        Args:
            message: Optional new message to display.
        """
        if message:
            self.message = message
            
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self, message=None):
        """Stop the spinner and clear the line.
        
        Args:
            message: Optional completion message to display.
        """
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
        
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10))
        
        # Print completion message if provided
        if message:
            sys.stdout.write(f"\r{message}")
        else:
            sys.stdout.write('\r')
        
        sys.stdout.flush()


class ResumeTailor:
    """Main class for tailoring resumes to job descriptions."""

    def __init__(self, api_key=None, output_dir=None, verbose=True):
        """Initialize the resume tailoring tool.

        Args:
            api_key: Anthropic API key. If None, will look for ANTHROPIC_API_KEY environment variable.
            output_dir: Directory to store outputs. If None, defaults to './resume_output'.
            verbose: Whether to show loading animations and status messages.
        """
        self.verbose = verbose
        
        # Setup loading spinner
        self.spinner = Spinner()
        
        # Setup output directory structure
        self.output_dir = output_dir or './resume_output'
        self.resumes_dir = os.path.join(self.output_dir, 'resumes')
        self.log_dir = os.path.join(self.output_dir, 'logs')
        
        # Create all necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.resumes_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._setup_logging()

        # Initialize Claude client
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            self.logger.error("No Anthropic API key provided. Set ANTHROPIC_API_KEY environment variable or pass via --api-key.")
            sys.exit(1)
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Log store for applications
        self.applications_log_file = os.path.join(self.output_dir, 'applications.json')
        self.applications = self._load_applications_log()

    def _setup_logging(self):
        """Configure logging for the application."""
        log_file = os.path.join(self.log_dir, f'resume_tailor_{datetime.datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler() if not self.verbose else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger('resume_tailor')
        self.logger.info("ResumeTailor initialized")

    def _load_applications_log(self):
        """Load the applications log file or create if it doesn't exist."""
        if os.path.exists(self.applications_log_file):
            try:
                with open(self.applications_log_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse applications log file. Creating new one.")
                return []
        else:
            return []

    def _save_applications_log(self):
        """Save the applications log to disk."""
        with open(self.applications_log_file, 'w') as f:
            json.dump(self.applications, f, indent=2)

    def read_latex_resume(self, file_path):
        """Read the original LaTeX resume file.
        
        Args:
            file_path: Path to the LaTeX resume file.
            
        Returns:
            str: Content of the LaTeX file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Successfully read LaTeX resume from {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading LaTeX file: {e}")
            raise

    def analyze_job_description(self, job_description, resume_content):
        """Use Claude to analyze the job description and extract key information.
        
        Args:
            job_description: Text of the job description.
            resume_content: Text of the original resume.
            
        Returns:
            dict: Analysis results including key skills, missing skills, and suggested modifications.
        """
        self.logger.info("Analyzing job description with Claude API")
        
        if self.verbose:
            self.spinner.start("Analyzing job description with Claude API (this may take a minute)...")
        
        prompt = f"""
        You are an expert resume tailoring assistant. Your task is to analyze a job description and a resume, then provide guidance on tailoring the resume to better match the job requirements.

        # Job Description:
        ```
        {job_description}
        ```

        # Current Resume (LaTeX format):
        ```latex
        {resume_content}
        ```

        Please provide a structured analysis in JSON format with the following information:
        1. "key_skills": Extract the key skills and requirements from the job description (array of strings)
        2. "missing_skills": Identify skills in the job description that don't appear in the resume (array of strings)
        3. "title_suggestions": Suggest how to modify job titles to better align with the target position (object with original titles as keys and suggested titles as values)
        4. "experience_suggestions": Suggest modifications to experience descriptions to highlight relevant skills (object with section identifiers as keys and suggested text as values)
        5. "content_additions": Suggest additional content to add to the resume (object with section names as keys and content to add as values)

        Your response should be valid JSON that can be parsed programmatically. Focus on making changes that will improve ATS compatibility while maintaining the truth of the resume.
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                temperature=0.2,
                system="You are an expert resume tailoring assistant that helps customize resumes for specific job descriptions. Provide only valid JSON in your response.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from the response
            response_text = response.content[0].text
            # Find JSON content (in case there's additional text)
            json_pattern = r'({[\s\S]*})'
            json_match = re.search(json_pattern, response_text)
            
            if json_match:
                json_str = json_match.group(1)
                analysis = json.loads(json_str)
                self.logger.info("Successfully analyzed job description")
                
                if self.verbose:
                    self.spinner.stop("✓ Job description analyzed successfully.")
                
                return analysis
            else:
                if self.verbose:
                    self.spinner.stop("✗ Failed to extract valid data from response.")
                
                self.logger.error("Failed to extract JSON from Claude response")
                raise ValueError("Could not extract valid JSON from the AI response")
                
        except Exception as e:
            if self.verbose:
                self.spinner.stop(f"✗ Error analyzing job description: {e}")
                
            self.logger.error(f"Error analyzing job description: {e}")
            raise

    def customize_resume(self, original_latex, analysis):
        """Customize the resume LaTeX based on the analysis.
        
        Args:
            original_latex: Original LaTeX content of the resume.
            analysis: Analysis output from analyze_job_description().
            
        Returns:
            str: Modified LaTeX content.
        """
        self.logger.info("Customizing resume based on analysis")
        
        if self.verbose:
            self.spinner.start("Customizing resume based on job requirements...")
        
        prompt = f"""
        You are an expert LaTeX resume editor. Your task is to modify a LaTeX resume based on analysis to better target a specific job.

        # Original Resume (LaTeX format):
        ```latex
        {original_latex}
        ```

        # Analysis to incorporate:
        ```json
        {json.dumps(analysis, indent=2)}
        ```

        Please modify the LaTeX resume to incorporate the suggestions from the analysis. Focus on:
        1. Adjusting job titles if suggested
        2. Enhancing experience descriptions to highlight relevant skills
        3. Adding any missing skills that the candidate genuinely has
        4. Making the resume more ATS-friendly for this specific job

        Return ONLY the complete modified LaTeX code with no additional comments or explanations. The code should be valid LaTeX that will compile correctly.
        """
        
        try:
            response = self.client.messages.create(
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
                
            self.logger.info("Successfully customized resume")
            
            if self.verbose:
                self.spinner.stop("✓ Resume customized successfully.")
                
            return latex_content
            
        except Exception as e:
            if self.verbose:
                self.spinner.stop(f"✗ Error customizing resume: {e}")
                
            self.logger.error(f"Error customizing resume: {e}")
            raise

    def validate_latex(self, latex_content):
        """Validate that the LaTeX content compiles correctly.
        
        Args:
            latex_content: LaTeX content to validate.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        self.logger.info("Validating LaTeX compilation")
        
        if self.verbose:
            self.spinner.start("Validating LaTeX compilation...")
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "resume_temp.tex")
            
            # Write content to temporary file
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(latex_content)
            
            # Try to compile
            try:
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, temp_file],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    self.logger.error(f"LaTeX compilation failed: {result.stderr}")
                    
                    if self.verbose:
                        self.spinner.stop("✗ LaTeX compilation failed.")
                    
                    return False
                
                self.logger.info("LaTeX compilation successful")
                
                if self.verbose:
                    self.spinner.stop("✓ LaTeX compilation successful.")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error during LaTeX validation: {e}")
                
                if self.verbose:
                    self.spinner.stop(f"✗ Error during LaTeX validation: {e}")
                
                return False

    def save_tailored_resume(self, latex_content, original_file, job_title=None):
        """Save the tailored resume to the output directory.
        
        Args:
            latex_content: Modified LaTeX content.
            original_file: Path to the original resume file.
            job_title: Optional job title for the filename.
            
        Returns:
            str: Path to the new file.
        """
        # Generate filename based on original file and date/job
        original_path = Path(original_file)
        base_name = original_path.stem
        
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        job_suffix = f"_{job_title.replace(' ', '_')}" if job_title else ""
        new_filename = f"{base_name}_tailored{job_suffix}_{date_str}.tex"
        
        # Save to the resumes subdirectory
        new_path = Path(self.resumes_dir) / new_filename
        
        # Save the file
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
            
        self.logger.info(f"Saved tailored resume to {new_path}")
        
        # Also save the compiled PDF if validation succeeded
        pdf_output = self._compile_resume_to_pdf(latex_content, new_path.stem)
        
        # Add to applications log
        job_entry = {
            "id": len(self.applications) + 1,
            "date_created": datetime.datetime.now().isoformat(),
            "original_resume": str(original_file),
            "tailored_resume": str(new_path),
            "pdf_resume": pdf_output,
            "job_title": job_title or "Untitled Position",
            "applied": False,
            "application_date": None,
            "company": None,
            "job_link": None,
            "notes": None
        }
        
        self.applications.append(job_entry)
        self._save_applications_log()
        
        return str(new_path)
        
    def _compile_resume_to_pdf(self, latex_content, base_name):
        """Compile the LaTeX content to PDF and save in the output directory.
        
        Args:
            latex_content: LaTeX content to compile.
            base_name: Base name for the output file.
            
        Returns:
            str: Path to the PDF file or None if compilation failed.
        """
        # Create path for the PDF
        pdf_path = os.path.join(self.resumes_dir, f"{base_name}.pdf")
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, f"{base_name}.tex")
            
            # Write content to temporary file
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(latex_content)
            
            # Try to compile
            try:
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, temp_file],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    self.logger.error(f"PDF compilation failed: {result.stderr}")
                    return None
                
                # Copy the PDF from temp directory to output directory
                temp_pdf = os.path.join(temp_dir, f"{base_name}.pdf")
                if os.path.exists(temp_pdf):
                    import shutil
                    shutil.copy2(temp_pdf, pdf_path)
                    self.logger.info(f"Saved PDF version to {pdf_path}")
                    return pdf_path
                else:
                    self.logger.error("PDF file not found after compilation")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Error during PDF compilation: {e}")
                return None

    def update_application_status(self, resume_id, applied=True, company=None, job_link=None, notes=None):
        """Update the application status in the log.
        
        Args:
            resume_id: ID of the resume in the applications log.
            applied: Whether the application has been submitted.
            company: Name of the company.
            job_link: Link to the job posting.
            notes: Additional notes about the application.
            
        Returns:
            bool: True if updated successfully.
        """
        for app in self.applications:
            if app["id"] == resume_id:
                if applied:
                    app["applied"] = True
                    app["application_date"] = datetime.datetime.now().isoformat()
                
                if company:
                    app["company"] = company
                
                if job_link:
                    app["job_link"] = job_link
                    
                if notes:
                    app["notes"] = notes
                
                self._save_applications_log()
                self.logger.info(f"Updated application status for resume ID {resume_id}")
                return True
                
        self.logger.warning(f"Could not find resume with ID {resume_id}")
        return False

    def tailor_resume(self, resume_file, job_description, job_title=None, company=None):
        """Main method to tailor a resume based on a job description.
        
        Args:
            resume_file: Path to the original LaTeX resume.
            job_description: Text of the job description.
            job_title: Optional job title for logging.
            company: Optional company name for logging.
            
        Returns:
            str: Path to the tailored resume file.
        """
        try:
            if self.verbose:
                print(f"📄 Starting resume tailoring process for: {job_title or 'Untitled Position'}")
                if company:
                    print(f"🏢 Company: {company}")
                print()
            
            # Read the original resume
            original_content = self.read_latex_resume(resume_file)
            
            # Analyze the job description
            analysis = self.analyze_job_description(job_description, original_content)
            
            # Customize the resume
            tailored_content = self.customize_resume(original_content, analysis)
            
            # Validate the LaTeX
            is_valid = self.validate_latex(tailored_content)
            if not is_valid:
                self.logger.error("Tailored resume failed to compile. Aborting.")
                
                if self.verbose:
                    print("\n❌ Error: Generated LaTeX content does not compile correctly.")
                
                raise ValueError("Generated LaTeX content does not compile correctly")
            
            # Save the tailored resume
            new_file_path = self.save_tailored_resume(tailored_content, resume_file, job_title)
            
            # Update log with company info if provided
            if company and len(self.applications) > 0:
                latest_id = self.applications[-1]["id"]
                self.update_application_status(latest_id, applied=False, company=company)
            
            self.logger.info(f"Resume successfully tailored and saved to {new_file_path}")
            
            if self.verbose:
                print(f"\n✅ Resume successfully tailored and saved to: {new_file_path}")
                
                # Print key insights from the analysis
                if analysis.get('key_skills'):
                    print(f"\n🔑 Key skills identified ({len(analysis['key_skills'])}): " + 
                          ", ".join(analysis['key_skills'][:5]) + 
                          (f" and {len(analysis['key_skills']) - 5} more..." if len(analysis['key_skills']) > 5 else ""))
                
                if analysis.get('missing_skills'):
                    print(f"⚠️ Missing skills addressed ({len(analysis['missing_skills'])}): " + 
                          ", ".join(analysis['missing_skills'][:3]) + 
                          (f" and {len(analysis['missing_skills']) - 3} more..." if len(analysis['missing_skills']) > 3 else ""))
                
                if analysis.get('title_suggestions') and len(analysis['title_suggestions']) > 0:
                    print(f"✏️ Job titles optimized: {len(analysis['title_suggestions'])}")
                
            return new_file_path
            
        except Exception as e:
            self.logger.error(f"Error tailoring resume: {e}")
            
            if self.verbose:
                print(f"\n❌ Error tailoring resume: {e}")
                
            raise


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Tailor your LaTeX resume to specific job descriptions")
    
    parser.add_argument("resume_file", help="Path to your original LaTeX resume file", nargs="?")
    parser.add_argument("--job-title", help="Job title for the position (used in filename and logs)")
    parser.add_argument("--company", help="Company name for logging purposes")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY environment variable)")
    parser.add_argument("--output-dir", help="Directory to store all outputs (default: ./resume_output)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress animations and detailed output")
    
    job_desc_group = parser.add_mutually_exclusive_group()
    job_desc_group.add_argument("--job-description", help="Job description text")
    job_desc_group.add_argument("--job-file", help="File containing the job description")
    
    # Status updating
    parser.add_argument("--update", type=int, help="Update application status for resume ID")
    parser.add_argument("--applied", action="store_true", help="Mark application as applied")
    parser.add_argument("--job-link", help="Link to the job posting")
    parser.add_argument("--notes", help="Additional notes about the application")
    
    # Utility options
    parser.add_argument("--list", action="store_true", help="List all previously created resumes")
    
    args = parser.parse_args()
    
    # Initialize the resume tailor with verbosity setting
    verbose = not args.quiet
    tailor = ResumeTailor(api_key=args.api_key, output_dir=args.output_dir, verbose=verbose)
    
    # List all applications
    if args.list:
        if not tailor.applications:
            print("No resume applications found in the log.")
            return
            
        print("\n=== Resume Applications ===\n")
        for app in tailor.applications:
            status = "✅ Applied" if app.get('applied') else "📝 Not Applied"
            created_date = datetime.datetime.fromisoformat(app.get('date_created')).strftime("%Y-%m-%d")
            
            print(f"ID: {app.get('id')} - {app.get('job_title')} - {status}")
            print(f"  Created: {created_date}")
            
            if app.get('company'):
                print(f"  Company: {app.get('company')}")
                
            if app.get('applied') and app.get('application_date'):
                applied_date = datetime.datetime.fromisoformat(app.get('application_date')).strftime("%Y-%m-%d")
                print(f"  Applied: {applied_date}")
                
            print(f"  Resume: {os.path.basename(app.get('tailored_resume'))}")
            
            if app.get('pdf_resume'):
                print(f"  PDF: {os.path.basename(app.get('pdf_resume'))}")
                
            if app.get('job_link'):
                print(f"  Link: {app.get('job_link')}")
                
            if app.get('notes'):
                print(f"  Notes: {app.get('notes')}")
                
            print()
        
        print(f"Total: {len(tailor.applications)} resume(s)")
        print(f"Output directory: {os.path.abspath(tailor.output_dir)}")
        return
    
    # If updating application status
    if args.update:
        if tailor.update_application_status(
            args.update, 
            applied=args.applied, 
            company=args.company, 
            job_link=args.job_link, 
            notes=args.notes
        ):
            print(f"Updated application status for resume ID {args.update}")
        else:
            print(f"Failed to update application status for resume ID {args.update}")
        return
    
    # Check if we're missing required arguments for tailoring
    if not args.resume_file:
        parser.error("resume_file is required unless using --list or --update")
    
    if not args.job_description and not args.job_file:
        parser.error("Either --job-description or --job-file is required")
    
    # Get job description
    job_description = None
    if args.job_description:
        job_description = args.job_description
    elif args.job_file:
        try:
            with open(args.job_file, 'r', encoding='utf-8') as f:
                job_description = f.read()
        except Exception as e:
            print(f"Error reading job description file: {e}")
            return
    
    # Tailor the resume
    try:
        new_file_path = tailor.tailor_resume(
            args.resume_file,
            job_description,
            job_title=args.job_title,
            company=args.company
        )
        
        if verbose:
            print(f"Application ID for future reference: {tailor.applications[-1]['id']}")
        
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
