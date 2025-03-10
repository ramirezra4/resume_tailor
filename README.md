# Resume Tailor

A command-line utility that customizes your LaTeX resume for specific job descriptions using Claude AI to improve ATS compatibility and increase your chances of getting interviews.

## Features

- **AI-Powered Analysis**: Uses Claude to analyze job descriptions and identify key skills and requirements
- **Resume Customization**: Intelligently modifies your resume to highlight relevant experience
- **ATS Optimization**: Ensures your resume includes keywords from the job description
- **LaTeX Validation**: Automatically verifies that the generated LaTeX compiles correctly
- **PDF Generation**: Creates both LaTeX and PDF versions of your tailored resume
- **Application Tracking**: Maintains a log of all your customized resumes and application statuses
- **Terminal UI**: Includes loading animations and formatted output for a better user experience

## Installation

### Prerequisites

1. Python 3.6 or higher
2. LaTeX distribution with pdflatex:
   - **Linux**: `sudo apt-get install texlive-latex-base`
   - **macOS**: `brew install --cask mactex`
   - **Windows**: Install MiKTeX or TeX Live

### Setup

1. Clone this repository or download the script:
   ```bash
   git clone https://github.com/yourusername/resume-tailor.git
   cd resume-tailor
   ```

2. Install required dependencies:
   ```bash
   pip install anthropic
   ```

3. Set up your Anthropic API key (get one at https://console.anthropic.com/):
   ```bash
   # For bash/zsh (Linux/macOS)
   echo 'export ANTHROPIC_API_KEY=your_api_key_here' >> ~/.bashrc
   source ~/.bashrc
   
   # For Windows Command Prompt
   setx ANTHROPIC_API_KEY your_api_key_here
   
   # For Windows PowerShell
   [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your_api_key_here", "User")
   ```

## Usage

### Creating a Tailored Resume

Basic usage with a job description:

```bash
python resume_tailor.py your_resume.tex --job-description "Full job description goes here"
```

Using a file containing the job description:

```bash
python resume_tailor.py your_resume.tex --job-file path/to/job_description.txt
```

Adding job details for better tracking:

```bash
python resume_tailor.py your_resume.tex --job-file job.txt --job-title "Senior Developer" --company "Tech Corp"
```

### Viewing Your Tailored Resumes

List all your previously generated resumes:

```bash
python resume_tailor.py --list
```

This shows details like:
- Resume ID and job title
- Creation date
- Application status
- File locations
- Company and job link (if provided)

### Updating Application Status

After applying for a job, update the status:

```bash
python resume_tailor.py --update 1 --applied --job-link "https://example.com/job" --notes "Applied via company website"
```

## Output Organization

The tool creates an organized directory structure:

```
resume_output/               # Main output directory
├── applications.json        # Application tracking database
├── resumes/                 # All tailored resumes
│   ├── your_resume_tailored_JobTitle_20250310.tex  # LaTeX file
│   └── your_resume_tailored_JobTitle_20250310.pdf  # PDF version
└── logs/                    # Log files
    └── resume_tailor_20250310.log
```

## Advanced Options

### Custom Output Directory

```bash
python resume_tailor.py your_resume.tex --job-file job.txt --output-dir "/path/to/custom/output"
```

### Quiet Mode (No Progress Animations)

```bash
python resume_tailor.py your_resume.tex --job-file job.txt --quiet
```

### Using a Different API Key

```bash
python resume_tailor.py your_resume.tex --job-file job.txt --api-key "your_alternative_api_key"
```

## Example Workflow

1. **Create a tailored resume**:
   ```bash
   python resume_tailor.py my_resume.tex --job-file software_engineer_job.txt --job-title "Software Engineer" --company "Tech Corp"
   ```

2. **Review the tailored resume**:
   The tool will save both LaTeX and PDF versions in the `resume_output/resumes/` directory.

3. **Apply for the job**:
   After applying, update the application status:
   ```bash
   python resume_tailor.py --update 1 --applied --job-link "https://techcorp.com/careers/12345"
   ```

4. **Track your applications**:
   ```bash
   python resume_tailor.py --list
   ```

## Future Features

- Batch processing of multiple job descriptions
- Resume similarity scoring to see how well your resume matches a job
- Cover letter generation
- Integration with job application tracking services

## Troubleshooting

- **LaTeX Compilation Errors**: Check the log file in `resume_output/logs/` for detailed error messages
- **API Key Issues**: Make sure your Anthropic API key is correctly set as an environment variable
- **Missing Dependencies**: Ensure you have all required Python packages and LaTeX installed

## License

[MIT License](LICENSE)
