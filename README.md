# Multi-Agent Healthcare Support System

A comprehensive healthcare support system built with FastAPI, CrewAI, and LLaMA integration via GroqCloud.

## Features

- **Multi-Agent System**: Report analysis, symptom checking, drug interaction detection, and general healthcare Q&A
- **OCR Integration**: Process medical reports from JPG/PNG images using Tesseract
- **Smart Reminders**: Email-based medication reminders with scheduling
- **Chat Interface**: ChatGPT-like dashboard for seamless user interaction
- **Secure Login**: Simple authentication with SQLite storage

## Tech Stack

- **Backend**: FastAPI (Python)
- **Multi-Agent**: CrewAI
- **LLM**: LLaMA via GroqCloud
- **OCR**: Tesseract
- **Database**: SQLite
- **Scheduler**: APScheduler
- **Email**: FastAPI-Mail
- **Frontend**: HTML, CSS, JavaScript with Bootstrap

## Quick Start

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access Dashboard**
   - Open `frontend/login.html` in your browser
   - Register/Login and start using the healthcare assistant

## Project Structure

```
multi-agent-healthcare/
├── backend/
│   ├── app.py
│   ├── agents/
│   ├── utils/
│   ├── database.py
│   ├── scheduler.py
│   └── requirements.txt
├── frontend/
│   ├── login.html
│   ├── dashboard.html
│   ├── style.css
│   └── script.js
└── docs/
```

## Environment Variables

Required environment variables in `.env`:
- `GROQ_API_KEY`: Your GroqCloud API key
- `EMAIL_USER`: SMTP email username
- `EMAIL_PASS`: SMTP email password
- `EMAIL_HOST`: SMTP server host
- `EMAIL_PORT`: SMTP server port

## Security Notes

- Reports and chat queries are NOT stored in the database
- Only login credentials and reminders are persisted
- All sensitive data is handled via environment variables