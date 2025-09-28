# System Architecture Documentation

## Overview

The Multi-Agent Healthcare Support System is built using a microservices-inspired architecture with specialized AI agents, each responsible for specific healthcare domains. The system provides a unified interface while maintaining modular, scalable components.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ login.html  │  │dashboard.html│  │  style.css  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                           │                                     │
│                    ┌─────────────┐                              │
│                    │ script.js   │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                        HTTP/REST API
                               │
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                                │
│  │   app.py    │  ← Main FastAPI application                    │
│  └─────────────┘                                                │
│         │                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Agent Coordination Layer                        ││
│  │  ┌─────────────┐                                            ││
│  │  │coordinator.py│ ← Routes requests to specialized agents   ││
│  │  └─────────────┘                                            ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                Specialized Agents                           ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        ││
│  │  │report_       │ │symptom_      │ │drug_         │        ││
│  │  │analyzer.py   │ │checker.py    │ │interaction.py│        ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘        ││
│  │                                                             ││
│  │  ┌──────────────┐                                          ││
│  │  │chatbot.py    │                                          ││
│  │  └──────────────┘                                          ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  Utility Services                           ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        ││
│  │  │llama_api.py  │ │   ocr.py     │ │email_service.py│      ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Data & Scheduling Layer                        ││
│  │  ┌──────────────┐ ┌──────────────┐                         ││
│  │  │database.py   │ │scheduler.py  │                         ││
│  │  └──────────────┘ └──────────────┘                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                               │
                    ┌─────────────────────┐
                    │   External Services  │
                    ├─────────────────────┤
                    │ ┌─────────────────┐ │
                    │ │ GroqCloud       │ │
                    │ │ (LLaMA API)     │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ SMTP Server     │ │
                    │ │ (Email)         │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ Tesseract OCR   │ │
                    │ │ (Local)         │ │
                    │ └─────────────────┘ │
                    └─────────────────────┘
                               │
                    ┌─────────────────────┐
                    │   Data Storage      │
                    ├─────────────────────┤
                    │ ┌─────────────────┐ │
                    │ │ SQLite Database │ │
                    │ │ - Users         │ │
                    │ │ - Reminders     │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ Environment     │ │
                    │ │ Variables       │ │
                    │ │ (.env file)     │ │
                    │ └─────────────────┘ │
                    └─────────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technologies**: HTML5, CSS3, JavaScript, Bootstrap 5

**Components**:
- `login.html`: Authentication interface with login/register forms
- `dashboard.html`: Main application interface with chat and reminders
- `style.css`: Custom styling with healthcare-themed design
- `script.js`: Client-side logic for API communication and UI interactions

**Key Features**:
- Responsive design for desktop and mobile
- Real-time chat interface similar to ChatGPT
- Drag-and-drop file upload functionality
- Tab-based navigation between features

### 2. API Gateway (FastAPI)

**File**: `app.py`

**Responsibilities**:
- HTTP request routing and validation
- Authentication and authorization
- File upload handling
- Error handling and response formatting
- CORS configuration for cross-origin requests

**Endpoints**:
```
POST /register          - User registration
POST /login            - User authentication
POST /chat             - AI chat interactions
POST /upload-report    - Medical report upload and analysis
POST /add-reminder     - Create medication reminder
GET  /get-reminders    - Retrieve user reminders
DELETE /delete-reminder - Remove reminder
GET  /health           - System health check
POST /test-email       - Email configuration test
```

### 3. Agent Coordination Layer

**File**: `agents/coordinator.py`

**Purpose**: Intelligent request routing to specialized agents based on content analysis

**Routing Logic**:
- **Report Analysis**: Keywords like "report", "test result", "lab result"
- **Symptom Checking**: Keywords like "symptom", "pain", "fever", "headache"
- **Drug Interactions**: Keywords like "drug", "medication", "interaction"
- **General Healthcare**: Default fallback for other health questions

### 4. Specialized Agents

#### 4.1 Report Analyzer Agent
**File**: `agents/report_analyzer.py`
- Processes OCR-extracted text from medical reports
- Provides structured analysis with key findings
- Includes medical disclaimers and recommendations

#### 4.2 Symptom Checker Agent
**File**: `agents/symptom_checker.py`
- Evaluates user-reported symptoms
- Provides emergency detection and alerts
- Offers triage recommendations and care guidance

#### 4.3 Drug Interaction Agent
**File**: `agents/drug_interaction.py`
- Identifies potential medication conflicts
- Maintains basic drug interaction database
- Provides safety warnings and recommendations

#### 4.4 Healthcare Chatbot Agent
**File**: `agents/chatbot.py`
- Handles general health information queries
- Categorizes topics (nutrition, exercise, mental health, etc.)
- Provides educational content and resources

### 5. Utility Services

#### 5.1 LLaMA API Service
**File**: `utils/llama_api.py`
- Interfaces with GroqCloud for LLaMA model access
- Provides specialized prompts for different healthcare tasks
- Handles API errors and fallback responses

#### 5.2 OCR Service
**File**: `utils/ocr.py`
- Processes uploaded medical report images
- Extracts text using Tesseract OCR
- Validates and cleans extracted text

#### 5.3 Email Service
**File**: `utils/email_service.py`
- Sends medication reminder emails
- Configurable SMTP settings
- HTML email formatting with healthcare branding

### 6. Data Layer

#### 6.1 Database Service
**File**: `database.py`
- SQLite database management
- User authentication and management
- Reminder storage and retrieval
- Secure password hashing with bcrypt

#### 6.2 Scheduler Service
**File**: `scheduler.py`
- Background task scheduling with APScheduler
- Automated reminder checking and email sending
- Configurable reminder frequencies

## Data Flow Patterns

### 1. Chat Interaction Flow
```
User Message → Frontend → FastAPI → Coordinator → Specialized Agent → LLaMA API → Response Formatting → Frontend Display
```

### 2. File Upload Flow
```
Image Upload → Frontend → FastAPI → OCR Processing → Text Validation → Report Analysis → AI Processing → Formatted Response
```

### 3. Reminder Flow
```
User Input → Frontend → FastAPI → Database Storage → Scheduler Registration → Background Processing → Email Notification
```

## Security Architecture

### Authentication
- Simple username/password authentication
- Bcrypt password hashing (cost factor: 12)
- Session-based user management
- No JWT tokens for simplicity

### Data Protection
- Medical data is NOT stored in database
- Only user credentials and reminders are persisted
- Environment variables for sensitive configuration
- Input validation and sanitization

### API Security
- CORS middleware configuration
- Request rate limiting (future enhancement)
- Input validation with Pydantic models
- Error handling without information disclosure

## Scalability Considerations

### Horizontal Scaling
- Stateless API design enables load balancing
- Database connection pooling for concurrent requests
- Asynchronous processing for file uploads
- Microservices-ready architecture

### Performance Optimization
- Efficient database queries with proper indexing
- Caching strategies for repeated AI requests
- Lazy loading of heavy components
- Optimized frontend asset delivery

### Monitoring and Logging
- Health check endpoints for system monitoring
- Structured logging for debugging
- Error tracking and alerting
- Performance metrics collection

## Deployment Architecture

### Development Environment
```
Local Machine → Python Virtual Environment → SQLite Database → Local SMTP Server
```

### Production Environment (Recommended)
```
Load Balancer → FastAPI Containers → PostgreSQL Database → External SMTP Service
```

### Container Strategy
```dockerfile
# Example Dockerfile structure
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration Management

### Environment Variables
```bash
# Core API Configuration
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key

# Database Configuration
DATABASE_URL=sqlite:///./healthcare.db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

### Configuration Files
- `.env`: Environment-specific variables
- `requirements.txt`: Python dependencies
- Database schema: Defined in `database.py`

## Error Handling Strategy

### Frontend Error Handling
- User-friendly error messages
- Loading states and progress indicators
- Graceful degradation for offline scenarios
- Retry mechanisms for failed requests

### Backend Error Handling
- Structured exception handling
- Appropriate HTTP status codes
- Detailed logging for debugging
- Fallback responses when AI services fail

### Data Validation
- Pydantic models for request validation
- File type and size validation
- Input sanitization and cleaning
- Database constraint enforcement

This architecture provides a solid foundation for a scalable, maintainable healthcare support system while maintaining simplicity and focusing on core functionality.