# Job Search Automation System

A multi-agent system built with Phidata that automates the job search process, from finding relevant positions to scheduling interviews.

## Features

- **Automated Job Collection**: Scrapes job postings from multiple platforms (LinkedIn, Glassdoor, Indeed)
- **Intelligent Information Extraction**: Parses and structures job posting data
- **Email Automation**: Handles application emails, follow-ups, and interview scheduling
- **Calendar Integration**: Manages interview scheduling with Google Calendar
- **Status Tracking**: Monitors application statuses and responses
- **Customizable Preferences**: Configure job search criteria, email templates, and more

## System Architecture

The system uses four specialized agents:

1. **Job Collector Agent**: Finds and collects relevant job postings
2. **Information Extractor Agent**: Processes and structures job data
3. **Email Agent**: Handles all email communications
4. **Scheduler Agent**: Manages calendar and scheduling

## Prerequisites

- Python 3.8+
- PostgreSQL (optional, can use CSV storage)
- Google Account (for Gmail and Calendar integration)
- API keys for job platforms (LinkedIn, Glassdoor, Indeed)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Javid912/AI-job-search-assistant.git
cd job-search-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
OPENAI_API_KEY=your_openai_key
GMAIL_CREDENTIALS=path_to_credentials.json
CALENDAR_CREDENTIALS=path_to_credentials.json
SENDER_EMAIL=your_email@example.com
SENDER_NAME=Your Name
EMAIL_SIGNATURE=Your Signature
RESUME_PATH=path/to/resume.pdf
COVER_LETTER_TEMPLATE=path/to/cover_letter.txt
PORTFOLIO_URL=https://your-portfolio.com
DATABASE_URL=postgresql://user:password@localhost:5432/job_search
```

5. Configure job search preferences in `config.py`

## Usage

### Basic Usage

Run the job search automation:
```bash
python main.py
```

### Update Search Preferences

Update job search preferences via command line:
```bash
python main.py --update-preferences \
    --keywords "software engineer" "python developer" \
    --locations "San Francisco" "Remote" \
    --job-types "full-time" "contract" \
    --experience-levels "mid" "senior" \
    --posted-within-days 30
```

### Email Templates

Customize email templates in the `email_templates` directory:
- `application_template.txt`: Initial job application
- `follow_up_template.txt`: Follow-up emails
- `interview_confirmation.txt`: Interview confirmations
- `thank_you_template.txt`: Post-interview thank you emails

## Configuration

The system is highly configurable through `config.py`:

- Job search preferences
- Email settings
- Calendar preferences
- API credentials
- Storage options
- Logging configuration
- LLM settings

## Monitoring

The system provides detailed logging of all operations in `job_search.log`. Monitor:

- Job search results
- Application statuses
- Email communications
- Interview scheduling
- System errors

## Development

### Project Structure

```
job-search-assistant/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── job_collector.py
│   │   ├── information_extractor.py
│   │   ├── email_agent.py
│   │   └── scheduler.py
│   └── workflows/
│       └── job_search.py
├── email_templates/
│   ├── application_template.txt
│   ├── follow_up_template.txt
│   ├── interview_confirmation.txt
│   └── thank_you_template.txt
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

### Adding New Features

1. Create new agent in `src/agents/`
2. Update workflow in `src/workflows/job_search.py`
3. Add configuration in `config.py`
4. Update email templates if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Phidata](https://docs.phidata.com/)
- Inspired by the need for efficient job search automation
