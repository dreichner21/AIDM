# AI-DM (AI Dungeon Master)

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://palletsprojects.com/p/flask/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

AI-DM (AI Dungeon Master) is a Flask-based web application designed to provide an AI-assisted experience for running tabletop RPG sessions (e.g., Dungeons & Dragons). It leverages Google's PaLM API (via the `google-generativeai` Python package) to generate dynamic, context-aware storytelling and DM (Dungeon Master) responses.

The application supports creating and managing:
- **Worlds** and the overall setting.
- **Campaigns** linked to those worlds.
- **Players** and their characters.
- **Sessions** (game logs, real-time interaction using Socket.IO).
- **Maps** and **Segments** (story milestones, triggers, etc.).

Whether you're a developer looking to extend or customize the AI logic or a player/DM wanting to experiment with AI-driven storytelling, AI-DM provides an interactive platform to bring your RPG sessions to life.

---

## Table of Contents
1. [Project Title and Description](#ai-dm-ai-dungeon-master)
2. [Installation Instructions](#installation-instructions)
3. [Usage Instructions](#usage-instructions)
4. [Accessing the GUI](#accessing-the-gui)
    - [Using Ngrok to Play With Friends](#using-ngrok-to-play-with-friends)
5. [Features](#features)
6. [API Documentation](#api-documentation)
    - [Worlds](#worlds)
    - [Campaigns](#campaigns)
    - [Players](#players)
    - [Sessions](#sessions)
    - [Maps](#maps)
    - [Segments](#segments)
    - [Real-time Socket.IO Events](#real-time-socketio-events)
7. [Technologies Used](#technologies-used)
8. [Project Structure](#project-structure)
9. [Contributing Guidelines](#contributing-guidelines)
10. [Testing Instructions](#testing-instructions)
11. [Known Issues and Limitations](#known-issues-and-limitations)
12. [License](#license)
13. [Acknowledgments](#acknowledgments)
14. [Contact Information](#contact-information)
15. [Additional Sections](#additional-sections)

---

## Installation Instructions

### Prerequisites
- **Python 3.9+**
- **pip** (or another Python package manager)
- A **Google PaLM (Generative AI)** API key (set as an environment variable `GOOGLE_GENAI_API_KEY`)
- (Optional) **Node.js** if you want to customize front-end or manage Socket.IO client setups from Node.

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/AIDM.git
   cd AIDM
   ```

2. **Create and Activate a Virtual Environment (Recommended)**
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
   - **Google PaLM API Key**: Ensure you have a `.env` file in the project root (or your environment) with:
     ```bash
     GOOGLE_GENAI_API_KEY=YOUR_API_KEY_HERE
     FLASK_SECRET_KEY=some_random_secret
     ```
   - Replace `YOUR_API_KEY_HERE` with your actual Google Generative AI (PaLM) key.

5. **Initialize the Database**
   When you first run the Flask application, it will automatically create a local SQLite database in the `instance/` folder. If it does not, you can manually create it using:
   ```bash
   flask db upgrade
   ```
   (This project uses Flask-Migrate for database migrations.)

6. **Run the Application**
   ```bash
   python -m aidm_server.main
   ```
   By default, the server runs on [http://localhost:5000](http://localhost:5000).

---

## Usage Instructions

Once the application is running:

- **API Endpoints** are available at `http://localhost:5000/api/...`.
- **Flask Admin Panel** is accessible at `http://localhost:5000/admin`. Use this to manage database entries visually.
- **Real-time Socket.IO** connections use the same domain/port (e.g., `ws://localhost:5000/socket.io/`).

Below is a quick example flow of how you might set up your game world:

1. **Create a World** (via HTTP):
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"name": "Faerun", "description": "A high-fantasy realm filled with magic."}' \
   http://localhost:5000/api/worlds
   ```

2. **Create a Campaign**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"title": "Dragons of the North", "description": "A quest to stop ancient dragons.", "world_id": 1}' \
   http://localhost:5000/api/campaigns
   ```

3. **Add Players**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"name": "Alice", "character_name": "Seraphina", "race": "Elf", "char_class": "Ranger", "level": 3}' \
   http://localhost:5000/api/players/campaigns/1/players
   ```

4. **Start a Session**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"campaign_id": 1}' \
   http://localhost:5000/api/sessions/start
   ```
   This returns a `session_id` that can be used for real-time interactions with Socket.IO or further session logs.

Use the [API Documentation](#api-documentation) below for more details on available endpoints and request/response formats.

---

## Accessing the GUI

An official front-end GUI is available at [aidm-client.vercel.app](https://aidm-client.vercel.app). Follow these steps to connect:

1. **Start the AI-DM Server**
   Make sure your Flask server is running locally on `http://localhost:5000` (or your custom host/port).

2. **Open the Web Client**
   Go to [aidm-client.vercel.app](https://aidm-client.vercel.app) in your browser.

3. **Enter Server URL**
   On the first page, you will be prompted for a **Server URL**. By default, if you're running locally, you can use:
   ```
   http://localhost:5000
   ```

4. **Play!**
   Once connected, you can create/join campaigns, start sessions, and interact via the web client's interface.

### Using Ngrok to Play With Friends

If you want to play together with friends over the internet (without hosting on a public server), you can use **ngrok** to securely tunnel your local server:

1. **Download ngrok**
   - Visit [https://ngrok.com/download](https://ngrok.com/download) and download the appropriate version for your OS.

2. **Expose Your Local Server**
   - Run:
     ```bash
     ngrok http 5000
     ```
   - This will create a secure URL (e.g., `https://1234-56-789-xxx.ngrok.io`) that points to your local machine's port 5000.

3. **Share the Ngrok URL**
   - Copy the **Forwarding** URL from the ngrok terminal.
   - Give this URL to your friends.

4. **Set the Server URL in the GUI**
   - In the [aidm-client.vercel.app](https://aidm-client.vercel.app) interface, everyone should **enter the ngrok URL** as the **Server URL** instead of `http://localhost:5000`.
     For example:
     ```
     https://1234-56-789-xxx.ngrok.io
     ```

5. **Play Together**
   - Now, all players will be connected to the same AI-DM server through the ngrok tunnel, allowing real-time interaction from anywhere.

---

## Features

- **Flask REST API** for worlds, campaigns, players, sessions, maps, and story segments.
- **Real-Time Interaction** using Socket.IO for live chat between players and an AI-driven DM.
- **Automated Storytelling** leveraging Google PaLM (Generative AI) for narrative, NPC dialogues, and dynamic events.
- **Session Logging** to capture player actions and DM responses for recaps or analysis.
- **Flask-Admin Interface** to manage data (worlds, campaigns, sessions, etc.) via a browser-based admin panel.
- **Modular Blueprint Architecture** for clean separation of features and routes.

---

## API Documentation

Below is a brief overview of the main API endpoints. All endpoints are prefixed with `/api`.

### Worlds

- **POST** `/worlds`
  Create a new world.
  **Request Body**:
  ```json
  {
    "name": "Faerun",
    "description": "A high-fantasy realm filled with magic."
  }
  ```

- **GET** `/worlds/<world_id>`
  Get details of a specific world by its ID.

### Campaigns

- **POST** `/campaigns`
  Create a new campaign.
  **Request Body**:
  ```json
  {
    "title": "Dragons of the North",
    "description": "A quest to stop ancient dragons.",
    "world_id": 1
  }
  ```

- **GET** `/campaigns`
  List all campaigns.

- **GET** `/campaigns/<campaign_id>`
  Retrieve details for a specific campaign.

### Players

- **POST** `/players/campaigns/<campaign_id>/players`
  Create (add) a new player in a specific campaign.
  **Request Body**:
  ```json
  {
    "name": "Alice",
    "character_name": "Seraphina",
    "race": "Elf",
    "char_class": "Ranger",
    "level": 3
  }
  ```

- **GET** `/players/campaigns/<campaign_id>/players`
  List all players in a campaign.

- **GET** `/players/<player_id>`
  Retrieve details for a specific player by ID.

### Sessions

- **POST** `/sessions/start`
  Start a new session for a campaign.
  **Request Body**:
  ```json
  {
    "campaign_id": 1
  }
  ```

- **POST** `/sessions/<session_id>/end`
  End a session and generate a GPT-based recap.

- **GET** `/sessions/campaigns/<campaign_id>/sessions`
  List all sessions for a campaign.

### Maps

- **POST** `/maps`
  Create a new map (optionally linked to a world or campaign).

- **GET** `/maps`
  List maps, optionally filtered by `world_id` or `campaign_id`.

- **GET** `/maps/<map_id>`
  Retrieve a specific map.

- **PUT/PATCH** `/maps/<map_id>`
  Update a map's details or data.

### Segments

- **POST** `/segments`
  Create a campaign segment (e.g., a key storyline milestone).

- **GET** `/segments`
  List segments, optionally filtered by `campaign_id`.

- **GET** `/segments/<segment_id>`
  Retrieve a specific segment.

- **PUT/PATCH** `/segments/<segment_id>`
  Update segment details (like trigger conditions).

- **DELETE** `/segments/<segment_id>`
  Delete a segment.

### Real-time Socket.IO Events

The application also supports real-time events using **Socket.IO**. Examples include:

- **`join_session`**: Join a particular session (room) with a given `session_id` and `player_id`.
- **`leave_session`**: Leave a session.
- **`send_message`**: Broadcast a player's chat or action to the session, triggering an AI (DM) response.
- **`player_joined`, `player_left`**: Emitted by the server to inform all connected clients about player changes.
- **`dm_chunk`**, **`dm_response_start`**, **`dm_response_end`**: Emitted by the server to send AI-generated story text in chunks.

---

## Technologies Used

- **Python 3.9+**
- **Flask** (web framework)
- **Flask-SocketIO** (real-time communication)
- **SQLAlchemy** / **Flask-Migrate** (database ORM and migrations)
- **SQLite** (default local database)
- **google-generativeai** (integration with Google's PaLM API for text generation)
- **Flask-Admin** (admin panel)
- **dotenv** (environment variable management)
- **eventlet** / **websocket-client** (for Socket.IO)
- Various Python libraries (see `requirements.txt`)

---

## Project Structure

```
AIDM/
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation (this file)
└── aidm_server/
    ├── blueprints/         # Flask blueprints for different features
    │   ├── campaigns.py
    │   ├── worlds.py
    │   ├── players.py
    │   ├── sessions.py
    │   ├── segments.py
    │   ├── maps.py
    │   ├── admin.py
    │   └── socketio_events.py
    ├── __init__.py
    ├── database.py         # Database setup and initialization
    ├── llm.py              # LLM interaction logic (Google PaLM)
    ├── main.py             # Application entry point
    └── models.py           # SQLAlchemy ORM models
```

- **`blueprints/`**: Each file under this directory defines a specific set of related routes (e.g., `sessions.py`, `maps.py`) for better modularity.
- **`llm.py`**: Contains logic to query the Google PaLM model with context built from the game data.
- **`main.py`**: The central Flask application runner. Sets up Socket.IO, registers blueprints, etc.
- **`database.py`** and **`models.py`**: Database configurations and entity models.

---

## Contributing Guidelines

We welcome contributions! To contribute:

1. **Fork the Repository** on GitHub.

2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Commit Your Changes** with descriptive messages:
   ```bash
   git commit -m "Add new feature for DM dialogue"
   ```

4. **Push to Your Fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

5. **Create a Pull Request** describing your changes, enhancements, or bug fixes.

**Code Style**:
- Follow PEP 8 for Python code style where possible.
- Write clear docstrings and comments, especially around AI logic.

---

## Testing Instructions

Currently, there are **no dedicated test suites** included in this repository. We recommend:

- **Pytest** or **unittest** for Python testing.
- Creating a `tests/` directory and adding test modules (e.g., `test_campaigns.py`, `test_sessions.py`).

Sample test command (if you have a `tests/` folder with `pytest`):
```bash
pytest tests
```

We encourage contributors to add tests alongside new features.

---

## Known Issues and Limitations

1. **AI Accuracy**: Responses from the Google PaLM model can vary and are sometimes not perfectly aligned with D&D rules.
2. **Session Persistence**: Long-term session logs may grow large; a more robust archiving system may be needed for big campaigns.
3. **Trigger Logic**: Segment trigger conditions are placeholders and need custom rules to be truly dynamic.
4. **Testing**: Lack of automated tests means potential bugs might go unnoticed in certain workflows.

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## Acknowledgments

- **Google PaLM / Generative AI** team for providing the underlying language model.
- **Flask** maintainers for the powerful yet lightweight Python framework.
- **Socket.IO** community for real-time web communications.
- All open-source contributors whose work made this project possible.

---

## Contact Information

For questions, feature requests, or bug reports:
- **Open a GitHub Issue** on the repository.
- **Email**: dannyreichner@outlook.com

---

## Additional Sections

- **Deployment Instructions**:
  - You can host this on any platform that supports Python and Socket.IO (e.g., Heroku, DigitalOcean, AWS).
  - Ensure environment variables (particularly `GOOGLE_GENAI_API_KEY` and `FLASK_SECRET_KEY`) are set.
- **FAQ**: Coming soon!
- **Roadmap**:
  1. Enhance segment trigger logic.
  2. Integrate more advanced AI features (NPC personalities, quest generation).
  3. Add user-friendly front-end for interactive map and session control.

---

<p align="center">
  <b>Thank you for using AI-DM! Enjoy your AI-driven RPG adventures.</b>
</p>