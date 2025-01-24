# AI-DM: AI Dungeon Master

Welcome to the AI-DM (AI Dungeon Master) system! This project is designed to help run tabletop RPG adventures (like Dungeons & Dragons) with the assistance of a powerful large language model as the DM.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Running the Server](#running-the-server)
  - [Using the GUI Wizard](#using-the-gui-wizard)
  - [Admin Interface](#admin-interface)
- [REST API Reference](#rest-api-reference)
- [Socket.IO Real-Time Interface](#socketio-real-time-interface)
- [Directory Structure](#directory-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

AI-DM is a Flask-based web application that uses Google's Generative AI (Gemini 1.5 Pro, or any other LLM you configure) to generate dynamic responses in a tabletop RPG scenario. It manages worlds, campaigns, players, sessions, and NPCs in an SQLite database.

## Features

- **RESTful Endpoints** to create and fetch Worlds, Campaigns, Players, Sessions, and more
- **Real-Time Chat** via Socket.IO, providing chunked/streamed responses from the AI
- **Flask-Admin** interface for quick data administration
- **PySide6 GUI** that guides you through selecting a server, campaign, session, and player, then enters a live chat
- **SQLite Database** (using SQLAlchemy ORM)

## Architecture

```
                     +-------------------------+
                     |      PySide6 GUI        |
                     | (Desktop Application)   |
                     +-----------↑↓-----------+
                      Socket.IO/WebSockets
                     +-----------↑↓-----------+
                     |    Flask/WS Server      |
                     | (REST API & Real-Time   |    
                     |        Chat)            |
                     +-----↑---------------↑---+
                           |               |
             HTTP/JSON     |               |   LLM API Integration
                           |               |
         +-----------------↓-+         +---↓----------------+
         |  SQLite Database |         | External LLM Service|
         | (SQLAlchemy ORM) |         | (e.g., Google GenAI,|
         +------------------+         |    Gemini, etc.)    |
                                      +---------------------+

   Host Machine                  Friend's Machine 
+-------------------+          +-----------------------+
|  Flask Server     |          |      GUI Client       |
|  - DB: local SQLite◄---ngrok---► Connects via API/   |
|  - Port 5000      |          | Socket.IO to your IP  |
+-------------------+          +-----------------------+
 
```
### Diagram Explanation
- **PySide6 GUI:** The desktop client communicates with the server using Socket.IO/WebSockets in both directions (sending user inputs and receiving updates).
- **Flask/WS Server:** Serves both the REST API for standard HTTP/JSON interactions and manages the real-time chat via WebSockets. It also forwards requests to and receives responses from the external LLM.
- **SQLite Database:** The Flask server interacts with the database (using SQLAlchemy ORM) to store and retrieve campaign, session, and game state data.
- **External LLM Service:** The generative AI service (such as Google GenAI or Gemini) receives prompts and sends back generated responses to the Flask server.
- **Host Machine:** Runs the Flask server on port 5000 with a local SQLite database. This is where all server-side processing occurs and game data is stored.
- **ngrok:** Creates a secure tunnel between the host and friend machines, allowing remote access to the local Flask server without complex port forwarding or networking configuration.
- **Friend's Machine:** Runs only the GUI client application, connecting to the host's server through the ngrok tunnel using API calls and Socket.IO for real-time communication.

## Getting Started

### Installation

1. **Clone** this repository:
   ```bash
   git clone https://github.com/dreichner21/AI-DM.git
   cd AI-DM
   ```

2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

#### GOOGLE_GENAI_API_KEY

Place your real Google Generative AI key in a `.env` file at the project root:

```
GOOGLE_GENAI_API_KEY=YOUR_ACTUAL_KEY
```

The code defaults to `AIzaSyBvsMef-geqcJJDof6hZitpLWSUxhiR1Ds` if you do not set the env var. Adjust as necessary.

### Environment Setup

1. Create a `.env` file in the project root
2. Add your Google Gemini API key:
   ```
   GOOGLE_GENAI_API_KEY=your_api_key_here
   ```
3. Never commit the `.env` file to version control

### Database Setup

By default, the app uses `sqlite:///dnd_ai_dm.db` inside `ai_dm/instance/`. This is automatically created upon first run. No additional steps needed.

### Running the Server

Inside the repository (with virtualenv activated), run:

```bash
cd ai_dm
python server.py
```

Or simply:

```bash
python -m ai_dm.server
```

It will:
1. Create missing tables in the SQLite database
2. Start a Flask + SocketIO server on http://localhost:5000

### Using the GUI Wizard

Open a separate terminal or keep the same terminal, then run:

```bash
python scripts/app.py
```

A Qt window will appear:
1. Enter the Server URL (if you're running locally, http://localhost:5000)
2. Select or create a Campaign
3. Select or create a Session
4. Select or create a Player
5. Enter the real-time Chat page and interact with the AI DM!

### Admin Interface

Flask-Admin is enabled at `<server-url>/admin`.
For example: http://localhost:5000/admin

Here, you can directly manage Worlds, Campaigns, Players, Sessions, and NPCs in a simple CRUD interface.

## REST API Reference

All endpoints are prefixed by the server root (e.g. http://localhost:5000).

### POST /worlds
Create a World. JSON body fields: `{ "name": "...", "description": "..." }`

### GET /worlds/<world_id>
Fetch a world's info. Returns JSON with fields for name, description, etc.

### POST /campaigns
Create a Campaign. JSON body: `{"title": "...", "description": "...", "world_id": X }`

### GET /campaigns
List all campaigns.

### GET /campaigns/<campaign_id>
Fetch campaign details.

### POST /campaigns/<campaign_id>/players
Add a Player to a campaign. JSON:
```json
{
  "name": "...",
  "character_name": "...",
  "race": "...",
  "char_class": "...",
  "level": 1
}
```

### GET /campaigns/<campaign_id>/players
List all players in a campaign.

### POST /sessions/start
Create a session for a campaign. Body: `{"campaign_id": X}`

### POST /sessions/<session_id>/interact
Send user input for a single turn (non-streaming). JSON:
```json
{
  "user_input": "...",
  "campaign_id": X,
  "world_id": Y,
  "player_id": Z
}
```
Returns complete AI response in one piece.

### POST /sessions/<session_id>/end
Ends the session, requests a recap from the AI, and stores it in session_obj.state_snapshot.

### GET /sessions/<session_id>/recap
Retrieve the recap of a completed session.

## Socket.IO Real-Time Interface

Namespace: default (`/`)

### Events from Client to Server

#### join_session
Payload: `{"session_id": <int>}`
Joins the user to a room named by the session ID.

#### send_message
Payload: `{"session_id": X, "campaign_id": Y, "world_id": Z, "player_id": W, "message": "User's message"}`
Server streams AI response chunk-by-chunk in real time.

### Events from Server to Client

#### new_message
Fired to the room when a new user or system message arrives.

#### dm_response_start
Signals the start of the AI's streaming answer.

#### dm_chunk
Each chunk of text from the AI while streaming. Accumulate to form the full response.

#### dm_response_end
Signifies the end of the AI's streaming response.

#### error
If an error occurs, the server emits this event with a message.

## Directory Structure

```
AI-DM/
├── ai_dm/
│   ├── instance/
│   │   └── dnd_ai_dm.db       # SQLite DB (auto-created)
│   ├── database.py            # Flask-SQLAlchemy db = SQLAlchemy()
│   ├── llm.py                 # Interactions with Google's Generative AI
│   ├── models_orm.py          # SQLAlchemy model definitions
│   └── server.py              # Main Flask + SocketIO server with REST endpoints
├── assets/
│   ├── fonts/
│   │   ├── MedievalSharp-Regular.ttf
│   │   └── UnifrakturMaguntia-Regular.ttf
│   └── background.jpg
├── scripts/
│   ├── app.py                 # PySide6 Wizard GUI
│   ├── cli_client.py          # CLI test client 
│   ├── install_fonts.py       # Installs custom fonts to user's OS
│   └── ws_client.py           # WebSocket/SocketIO test client
├── README.md                  # Project docs
└── requirements.txt           # Python dependencies
```

## Contributing

Feel free to open pull requests or issues. For major changes, discuss them first to ensure they fit the project's direction.

## License

This project is under MIT License.
