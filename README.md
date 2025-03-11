# Resume Tailor

A tool that ethically customizes your LaTeX resume for specific job descriptions using Claude AI to improve ATS compatibility while maintaining accuracy and honesty in your application.

## Features

- **AI-Powered Analysis**: Uses Claude to analyze job descriptions and identify key skills and requirements
- **Resume Customization**: Intelligently modifies your resume to highlight relevant experience
- **Human-in-the-Loop Review**: Review and approve each suggested change before applying it
- **ATS Optimization**: Ensures your resume includes relevant keywords from the job description
- **Ethical Guidelines**: Prevents misrepresentation by focusing on truthful highlighting of skills
- **Token Usage Tracking**: Monitors API usage and estimates costs for each resume customization
- **LaTeX Validation**: Automatically verifies that the generated LaTeX compiles correctly
- **PDF Generation**: Creates both LaTeX and PDF versions of your tailored resume
- **Application Tracking**: Maintains a log of all your customized resumes and application statuses
- **Terminal UI**: Includes loading animations and formatted output for a better user experience
- **Web Interface**: User-friendly browser UI for managing the entire resume customization process

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
    ├── resume_tailor_20250310.log                  # Application logs
    └── token_usage.csv                             # Token usage tracking
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

## Web Application

The Resume Tailor now includes a web interface that makes it even easier to manage your resume tailoring process.

### Running the Web App

1. Install the additional requirements:
   ```bash
   pip install flask python-dotenv
   ```

2. Set up your environment variables by copying the example file:
   ```bash
   cp .env.example .env
   ```
   
3. Edit the `.env` file to add your Anthropic API key and a secure secret key

4. Run the web server:
   ```bash
   python app.py
   ```

5. Open your browser to `http://localhost:5000`

### Web Features

- **User-friendly Interface**: No need to remember command-line arguments
- **Resume Upload**: Simply upload your LaTeX resume file through the browser
- **Job Description Input**: Paste job descriptions directly into the web form
- **Interactive Review**: Review and selectively approve AI-suggested changes before applying them
- **Status Tracking**: Easily view and update application statuses
- **File Management**: Download tailored resumes and PDFs directly from the app

## AI Prompt Architecture

The Resume Tailor uses a carefully designed multi-stage prompt system:

### 1. Job Analysis Prompt
- **Purpose**: Extracts key information from job descriptions without fabrication
- **Structure**: 
  - Instructs Claude to analyze the job for required skills, responsibilities, and qualifications
  - Requests output in structured JSON format for consistent parsing
  - Explicitly prevents fabrication by requiring evidence from the job description
  - Focuses on identifying missing skills rather than encouraging embellishment

### 2. User Review Interface
- **Purpose**: Gives users full control over which AI suggestions to incorporate
- **Design Philosophy**: 
  - Presents suggested modifications categorized by type (skills, experience, content)
  - Uses checkboxes for explicit approval of each change
  - Includes warnings against selecting skills you don't actually possess
  - Prevents job title modifications that could be seen as misrepresentation

### 3. Customization Prompt
- **Purpose**: Applies only approved changes to the resume
- **Structure**:
  - Dynamically built based on user-selected changes
  - Provides original LaTeX content alongside approved modifications
  - Includes specific instructions for maintaining proper LaTeX syntax
  - Focuses on truthful highlighting rather than fabrication

This architecture balances AI assistance with ethical considerations and user control to create resumes that are both effective and honest.

## Future Features

- Batch processing of multiple job descriptions
- Resume similarity scoring to see how well your resume matches a job
- Cover letter generation
- Integration with job application tracking services
- OAuth authentication for multi-user support
- Expanded ethics controls and transparency features
- Alternative resume formats beyond LaTeX
- Additional personalization options with more granular control

## Token Usage Tracking

Resume Tailor includes built-in token usage tracking to help you monitor API usage and estimate costs:

### CLI Token Usage

When using the command-line interface, token usage information is displayed after each resume tailoring operation:

```
📊 Total tokens used: 12,345 (estimated cost: $0.2345)
```

### Token Usage Logs

Detailed token usage is logged to a CSV file in the `resume_output/logs/` directory:

```
resume_output/logs/token_usage.csv
```

This file includes:
- Timestamp of each operation
- Operation type (analysis, customization)
- Job title
- Prompt tokens used
- Completion tokens used
- Total tokens
- Estimated cost in USD

This data can be imported into spreadsheet applications for further analysis and tracking of your API usage over time.

### Web Interface Token Display

The web interface displays token usage statistics for each resume on the result page, including:
- Analysis tokens
- Customization tokens
- Total tokens used
- Estimated cost

## Troubleshooting

- **LaTeX Compilation Errors**: Check the log file in `resume_output/logs/` for detailed error messages
- **API Key Issues**: Make sure your Anthropic API key is correctly set as an environment variable
- **Missing Dependencies**: Ensure you have all required Python packages and LaTeX installed
- **Token Usage Issues**: If token tracking seems incorrect, check the token_usage.csv log file for detailed information

## License

[MIT License](LICENSE)
