# Resume Tailor

Resume Tailor is a command-line tool that automatically customizes your LaTeX resume for specific job descriptions using AI analysis, making your resume more ATS-friendly and increasing your chances of getting interviews.

## Features

- **AI-Powered Analysis**: Uses Claude's API to extract key skills and requirements from job descriptions
- **Smart Customization**: Tailors your resume content to better match job requirements
- **LaTeX Validation**: Ensures the modified resume compiles correctly
- **Application Tracking**: Maintains a detailed log of all generated resumes and application statuses

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ramirezra4/resume_tailor.git
   cd resume_tailor
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have a LaTeX compiler installed (pdflatex):
   - On Ubuntu/Debian: `sudo apt-get install texlive-latex-base`
   - On macOS with Homebrew: `brew install --cask mactex`
   - On Windows: Install MiKTeX or TeX Live

4. Set up your Anthropic API key (get one at https://console.anthropic.com/):
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

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

### Quiet Mode (No Progress Animation)

```bash
python resume_tailor.py path/to/your_resume.tex --job-file job.txt --quiet
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Uses the [Anthropic Claude API](https://anthropic.com/) for AI analysis
- Inspired by the need to optimize job application process
