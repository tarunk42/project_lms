# AI-Powered Learning Management System

A modern, AI-driven Learning Management System that automatically generates comprehensive educational courses on any topic using OpenAI's GPT models. Features a persistent static domain for easy access from anywhere.

![LMS System Demo](https://img.shields.io/badge/Demo-Live-brightgreen)
![Version](https://img.shields.io/badge/Version-1.1.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Deployment](https://img.shields.io/badge/Deployment-ngrok-orange)

## 🚀 Overview

This project is an innovative Learning Management System that leverages AI to automatically generate complete educational courses. Simply input a topic, select a difficulty level, add an optional learning goal, and the system will create a structured curriculum with comprehensive study materials.

**Key Features:**
- 🧠 AI-generated curriculum structure with logical progression
- 📚 Comprehensive learning materials with examples and practice exercises
- 🔍 Detailed course outlines with modules and lessons
- 📝 Rich content formatting (code, math equations, diagrams)
- 🌐 Modern web interface for course creation and viewing
- 🌍 Persistent static domain for consistent access from anywhere
- 🔒 Secure HTTPS connections via ngrok tunneling
- 📊 Support for various learning styles and content types
- ⚡ One-command deployment with automated configuration

## 📋 Table of Contents

- [Project Architecture](#project-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Directory Structure](#directory-structure)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [License](#license)

## 🏗️ Project Architecture

The system follows a microservices architecture with specialized AI agents:

![Architecture Diagram](https://via.placeholder.com/800x400?text=LMS+System+Architecture)

### Core Components:

1. **Orchestrator** - Coordinates the entire workflow and manages communication between agents
2. **AI Agents** - Specialized agents for curriculum planning, review, syllabus detailing, and content generation
3. **FastAPI Backend** - RESTful API server for handling client requests
4. **Content Storage** - File-based system for storing course materials
5. **Web Interface** - Modern UI for interacting with the system
6. **ngrok Tunnel** - Secure tunneling for accessing the API from anywhere
7. **Automation Scripts** - Easy startup and shutdown of all services

### AI Agent Workflow:

```
User Request → Curriculum Planning → Review & Revision → Syllabus Detailing → Content Generation → Course Delivery
```

### System Architecture:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Web UI     │────▶│   FastAPI Server  │────▶│   AI Agents      │
│ (localhost  │     │   (localhost:8000 │     │   (OpenAI GPT-4) │
│  :5500)     │◀────│   or ngrok domain)│◀────│                  │
└─────────────┘     └──────────────────┘     └──────────────────┘
      │                      │                        │
      │                      │                        │
      ▼                      ▼                        ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Browser    │     │   Content Store   │     │  Orchestrator    │
│  Interface  │     │   (File System)   │     │  (Workflow Mgmt) │
└─────────────┘     └──────────────────┘     └──────────────────┘
```

## 📥 Installation

### Prerequisites

- Python 3.10+
- OpenAI API Key
- ngrok account (free tier is sufficient)
- Node.js 16+ (for local development server)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/project_lms.git
   cd project_lms
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv lmsenv
   source lmsenv/bin/activate  # On Windows: lmsenv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```bash
   # Create a .env file in the project root with your API keys
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   echo "NGROK_AUTH_TOKEN=your_ngrok_auth_token_here" >> .env
   ```

5. Configure your static ngrok domain:
   - Sign up for a free ngrok account at https://ngrok.com/
   - Get your authtoken from the ngrok dashboard
   - Reserve a free static domain from the ngrok dashboard
   - Update the domain in `start_lms.sh` (replace "lively-intimate-treefrog.ngrok-free.app" with your domain)

6. Make the automation scripts executable:
   ```bash
   chmod +x start_lms.sh stop_lms.sh
   ```

7. Start the entire system with one command:
   ```bash
   ./start_lms.sh
   ```
   This will:
   - Start the FastAPI server on port 8000
   - Create a secure ngrok tunnel with your static domain
   - Configure the web interface to use the correct API URL
   - Start the web interface on port 5500
   - Perform health checks on all services

8. To stop all services:
   ```bash
   ./stop_lms.sh
   ```

## 🔧 Usage

### Creating a New Course

1. Open the web interface at `http://localhost:5500` or via your static domain `https://lively-intimate-treefrog.ngrok-free.app`
2. Enter the topic you want to learn about (e.g., "Quantum Mechanics", "Python Programming")
3. Select the difficulty level (Beginner, Intermediate, Advanced)
4. Optionally add a learning goal
5. Click "Generate Complete Course"
6. Wait for the system to generate your curriculum and materials (typically 3-5 minutes)
7. Explore your custom-generated course!

### Accessing Your LMS From Anywhere

With your configured static ngrok domain, your LMS system is accessible from anywhere:

- **Local access**: `http://localhost:5500` - When working on your own machine
- **Public access**: `https://lively-intimate-treefrog.ngrok-free.app` - For sharing with others or accessing remotely

The static domain setup ensures:
- Consistent URL that doesn't change between restarts
- Secure HTTPS connection
- Access from any device with internet connectivity

### Exploring Existing Courses

1. Open the web interface
2. Select a course from the "Load Existing Course" dropdown
3. Browse through the modules and lessons
4. Click on a lesson to expand its content

### Command Line Usage

Generate a curriculum directly from the command line:

```bash
python main.py --topic "Python Programming" --level "beginner" --goal "Build a web scraper"
```

## 🔌 API Reference

The system exposes several RESTful endpoints, available both locally and through your ngrok static domain:

### Endpoints

All endpoints are available at:
- Local: `http://localhost:8000`
- Remote: `https://your-ngrok-domain.ngrok-free.app`

### Course Generation

- `POST /curriculum/plan` - Generate a new curriculum structure
  ```json
  {
    "topic": "Python Programming",
    "level": "beginner",
    "goal": "Build a web scraper"
  }
  ```

- `POST /materials/build/{course_id}` - Generate all course materials
  
### Course Management

- `GET /courses/list` - List all available courses
- `GET /courses/load/{course_id}` - Load a specific course with all materials

### Course Content

- `GET /materials/subtopic/{course_id}/{module_number}/{subtopic_number}` - Get a specific lesson

See the [API documentation](https://example.com/api-docs) for more details.

## 📂 Directory Structure

```
project_lms/
├── app.py                # FastAPI application
├── lms.py                # Core LMS functionality
├── main.py               # Command-line interface
├── requirements.txt      # Python dependencies
├── README.md             # This documentation
├── start_lms.sh          # Automation script to start all services
├── stop_lms.sh           # Automation script to stop all services
├── .env                  # Environment variables (API keys, configuration)
├── content/              # Generated course materials
├── logs/                 # Log files for API server, ngrok, and web server
├── src/
│   ├── config.py         # Configuration settings
│   ├── orchestrator.py   # Workflow coordination
│   ├── custom_agents/    # AI agent definitions
│   ├── models/           # Data models
│   ├── tools/            # Utility tools
│   └── utils/            # Helper functions
├── notebooks/            # Jupyter notebooks for experimentation
└── web_test/            # Web interface
    ├── index.html        # Main page
    ├── script.js         # Frontend logic
    ├── styles.css        # Styling
    └── config.js         # Dynamic API configuration
```

## 🛠️ Technologies

- **Backend**:
  - FastAPI - Modern, fast web framework
  - Pydantic - Data validation and settings management
  - OpenAI Agents SDK - AI agent coordination
  - Nest Asyncio - Asyncio support
  - uvicorn - ASGI server

- **Frontend**:
  - HTML/CSS/JavaScript - Basic web interface
  - Marked.js - Markdown rendering
  - Prism.js - Syntax highlighting
  - MathJax - Mathematical equation rendering

- **Deployment & Access**:
  - ngrok - Secure tunneling with static domain
  - HTTPS encryption - Secure communication
  - Bash scripts - Automated deployment

- **Data Storage**:
  - File-based storage system
  - JSON metadata

## 🚀 Advanced Features

### Custom Material Generation

The system adapts content generation based on subject matter:

- **Code-focused topics**: Includes runnable code examples and exercises
- **Math-heavy subjects**: LaTeX equation rendering and step-by-step derivations
- **Historical content**: Primary source analysis and chronological organization
- **Theoretical topics**: Conceptual illustrations and detailed explanations

### Course Review and Refinement

The system includes an AI reviewer that evaluates curriculum quality and suggests improvements:

- Structure verification
- Content balance analysis
- Learning progression assessment
- Terminology appropriateness

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## Deployment Options

### Local Deployment
The default setup uses ngrok for tunneling, which is perfect for development and small-scale deployments. The automated scripts make this process simple.

### Production Deployment
For production environments, consider:
- Deploying the API on a cloud provider like AWS, Azure, or Google Cloud
- Setting up a proper domain name with DNS records
- Using a reverse proxy like Nginx
- Implementing proper authentication

## �📬 Contact

For questions or feedback, please open an issue on GitHub or contact the maintainer at [your-email@example.com](mailto:your-email@example.com).

---


