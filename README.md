# Resume Tailoring Tool - Usage Guide

This tool automatically tailors your LaTeX resume for specific job descriptions using AI analysis, making your resume more ATS-friendly and increasing your chances of getting interviews.

## Installation

1. Clone this repository or download the script.

2. Install required dependencies:
   ```bash
   pip install anthropic argparse
   ```

3. Ensure you have a LaTeX compiler installed (pdflatex):
   - On Ubuntu/Debian: `sudo apt-get install texlive-latex-base`
   - On macOS with Homebrew: `brew install --cask mactex`
   - On Windows: Install MiKTeX or TeX Live

4. Set up your Anthropic API key (get one at https://console.anthropic.com/):
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Basic Usage

### Tailoring a Resume with a Job Description

```bash
python resume_tailor.py path/to/your_resume.tex --job-description "Full job description text goes here"
```

### Using a Job Description from a File

```bash
python resume_tailor.py path/to/your_resume.tex --job-file path/to/job_description.txt
```

### Adding Job Title and Company Information

```bash
python resume_tailor.py path/to/your_resume.tex --job-description "..." --job-title "Software Engineer" --company "Acme Inc."
```

## Application Tracking

The tool maintains a log of all generated resumes and application statuses in `./resume_logs/applications.json`.

### Updating Application Status

After applying for a job, update the application status using the resume ID:

```bash
python resume_tailor.py --update 1 --applied --job-link "https://example.com/job" --notes "Applied via company website"
```

## Output

The tool creates:

1. A new LaTeX file with the tailored resume in the same directory as the original
2. Log files in the `./resume_logs` directory
3. An entry in the applications tracking system

## Advanced Options

### Custom Log Directory

```bash
python resume_tailor.py path/to/your_resume.tex --job-description "..." --log-dir "/path/to/custom/log/directory"
```

### Using a Different API Key

```bash
python resume_tailor.py path/to/your_resume.tex --job-description "..." --api-key "your_alternative_api_key"
```

## Error Handling

If the tailored resume fails to compile correctly with LaTeX, the tool will raise an error and not save the file. Check the logs for details about the compilation errors.

## Batch Processing (Future Feature)

Support for batch processing multiple job descriptions is planned for a future update. This will allow you to:

1. Provide a directory of job description files
2. Supply a CSV with job details
3. Process them all at once to generate multiple tailored resumes
