# AI-DM (AI Dungeon Master)

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://palletsprojects.com/p/flask/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

AI-DM (AI Dungeon Master) is a Flask-based web application designed to provide an AI-assisted experience for running tabletop RPG sessions (e.g., Dungeons & Dragons). It leverages Google's PaLM API (via the `google-generativeai` Python package) to generate dynamic, context-aware storytelling and DM (Dungeon Master) responses.

The application supports creating and managing:
- **Worlds** and the overall setting
- **Campaigns** linked to those worlds
- **Players** and their characters
- **Sessions** (game logs, real-time interaction using Socket.IO)
- **Maps** and **Segments** (story milestones, triggers, etc.)

Whether you're a developer looking to extend or customize the AI logic or a player/DM wanting to experiment with AI-driven storytelling, AI-DM provides an interactive platform to bring your RPG sessions to life.

## Table of Contents

1. [Installation Instructions](#installation-instructions)
2. [Usage Instructions](#usage-instructions)
3. [Accessing the GUI](#accessing-the-gui)
4. [Features](#features)
5. [API Documentation](#api-documentation)
6. [Technologies Used](#technologies-used)
7. [Project Structure](#project-structure)
8. [Contributing Guidelines](#contributing-guidelines)
9. [Testing Instructions](#testing-instructions)
10. [Known Issues and Limitations](#known-issues-and-limitations)
11. [License](#license)
12. [Acknowledgments](#acknowledgments)
13. [Contact Information](#contact-information)
14. [Additional Information](#additional-information)

## Installation Instructions

### Prerequisites

- **Python 3.9+**
- **pip** (or another Python package manager)
- A **Google PaLM (Generative AI)** API key (set as an environment variable `GOOGLE_GENAI_API_KEY`)
- (Optional) **Node.js** if you want to customize front-end or manage Socket.IO client setups from Node

### Steps

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/AIDM.git
cd AIDM
```

2. **Create and Activate a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or
venv\Scripts\activate      # Windows
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**

Create a `.env` file in the project root:

```bash
GOOGLE_GENAI_API_KEY=YOUR_API_KEY_HERE
FLASK_SECRET_KEY=some_random_secret
```

5. **Initialize the Database**

```bash
flask db upgrade
```

6. **Run the Application**

```bash
python -m aidm_server.main
```

The server runs on [http://localhost:5000](http://localhost:5000) by default.

## Usage Instructions

Once running, you can access:

- **API Endpoints**: `http://localhost:5000/api/...`
- **Flask Admin Panel**: `http://localhost:5000/admin`
- **Socket.IO**: `ws://localhost:5000/socket.io/`

### Quick Start Example

1. **Create a World**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"name": "Faerun", "description": "A high-fantasy realm filled with magic."}' \
http://localhost:5000/api/worlds
```

2. **Create a Campaign**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"title": "Dragons of the North", "description": "A quest to stop ancient dragons.", "world_id": 1}' \
http://localhost:5000/api/campaigns
```

3. **Add Players**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"name": "Alice", "character_name": "Seraphina", "race": "Elf", "char_class": "Ranger", "level": 3}' \
http://localhost:5000/api/players/campaigns/1/players
```

4. **Start a Session**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"campaign_id": 1}' \
http://localhost:5000/api/sessions/start
```

## Accessing the GUI

The official front-end GUI is available at [aidm-client.vercel.app](https://aidm-client.vercel.app).

### Using Ngrok to Play With Friends

1. **Download ngrok** from [https://ngrok.com/download](https://ngrok.com/download)

2. **Expose Your Local Server**

```bash
ngrok http 5000
```

3. **Share the Ngrok URL** with your friends and use it as the Server URL in the GUI

## Features

- **Flask REST API** for worlds, campaigns, players, sessions, maps, and story segments
- **Real-Time Interaction** using Socket.IO for live chat
- **Automated Storytelling** leveraging Google PaLM
- **Session Logging** for recaps and analysis
- **Flask-Admin Interface** for database management
- **Modular Blueprint Architecture**

## API Documentation

### Worlds

- **POST `/worlds`**
  ```json
  {
    "name": "Faerun",
    "description": "A high-fantasy realm filled with magic."
  }
  ```

- **GET `/worlds/<world_id>`**

### Campaigns

- **POST `/campaigns`**
  ```json
  {
    "title": "Dragons of the North",
    "description": "A quest to stop ancient dragons.",
    "world_id": 1
  }
  ```

- **GET `/campaigns`**
- **GET `/campaigns/<campaign_id>`**

### Players

- **POST `/players/campaigns/<campaign_id>/players`**
- **GET `/players/campaigns/<campaign_id>/players`**
- **GET `/players/<player_id>`**

### Sessions

- **POST `/sessions/start`**
- **POST `/sessions/<session_id>/end`**
- **GET `/sessions/campaigns/<campaign_id>/sessions`**

### Socket.IO Events

- `join_session`
- `leave_session`
- `send_message`
- `player_joined`
- `player_left`
- `dm_chunk`
- `dm_response_start`
- `dm_response_end`

## Technologies Used

- Python 3.9+
- Flask
- Flask-SocketIO
- SQLAlchemy
- Flask-Migrate
- SQLite
- Google PaLM API
- Flask-Admin
- Eventlet

## Project Structure

```
AIDM/
├── requirements.txt
├── README.md
└── aidm_server/
    ├── blueprints/
    │   ├── campaigns.py
    │   ├── worlds.py
    │   ├── players.py
    │   ├── sessions.py
    │   ├── segments.py
    │   ├── maps.py
    │   ├── admin.py
    │   └── socketio_events.py
    ├── __init__.py
    ├── database.py
    ├── llm.py
    ├── main.py
    └── models.py
```

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to your fork
5. Create a Pull Request

Follow PEP 8 and include clear documentation.

## Testing Instructions

Currently, no dedicated test suites are included. We recommend:

- Using Pytest or unittest
- Creating a `tests/` directory
- Adding test modules for each component

## Known Issues and Limitations

1. AI responses can vary in accuracy
2. Session logs may grow large
3. Segment trigger conditions need enhancement
4. Lack of automated tests

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google PaLM team
- Flask maintainers
- Socket.IO community
- Open-source contributors

## Contact Information

- Open a GitHub Issue
- Email: your_email@example.com

## Additional Information

### Deployment

- Supports any Python/Socket.IO compatible platform
- Remember to set environment variables

### Roadmap

1. Enhance segment trigger logic
2. Integrate advanced AI features
3. Add user-friendly front-end

---

<p align="center"><b>Thank you for using AI-DM! Enjoy your AI-driven RPG adventures.</b></p>