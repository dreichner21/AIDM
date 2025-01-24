---

# AI-DM: AI Dungeon Master

Welcome to **AI-DM (AI Dungeon Master)**, a Flask-based web application designed to assist in running tabletop RPG adventures (like *Dungeons & Dragons*) using a Large Language Model (LLM) as the automated “DM.” This codebase integrates with Google’s *Gemini* (or any API-compatible LLM service) to generate dynamic game narration, handle rules logic, and facilitate real-time storytelling.

---

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Directory Structure](#directory-structure)
5. [Detailed File Walkthrough](#detailed-file-walkthrough)
6. [Getting Started](#getting-started)
   - [Installation](#installation)
   - [Environment Variables](#environment-variables)
   - [Running the Server](#running-the-server)
   - [Using the GUI Wizard](#using-the-gui-wizard)
   - [Admin Interface](#admin-interface)
7. [REST API Reference](#rest-api-reference)
8. [Socket.IO Real-Time Interface](#socketio-real-time-interface)
9. [Contributing](#contributing)
10. [License](#license)

---

## Overview

**AI-DM** is a system that aims to replicate the role of a *Dungeon Master* in a tabletop RPG using advanced generative AI models. It provides:

- An **interactive chat** interface to guide players through an RPG scenario.
- **Automated dice roll requests** and outcomes for combat or skill checks.
- **Persistence** of campaigns, worlds, players, and sessions in an SQLite database.
- **Real-time streaming** of the AI’s responses, allowing for a more natural back-and-forth conversation.

You can run the Flask-based server on your machine and optionally expose it to other players via tools like **ngrok**. Players can then connect from anywhere using the PySide6-based **GUI Wizard** or any custom UI you build on top of the **Socket.IO** endpoints.

---

## Key Features

1. **RESTful Endpoints** – Create and manage Worlds, Campaigns, Players, and Sessions via JSON-based APIs.
2. **Socket.IO Real-Time Chat** – Supports streaming chunked responses from the AI, giving a smooth conversational experience.
3. **AI Function Calling** – The code uses structured prompts (“function calling”) to enforce consistent DM responses, including roll requests.
4. **SQLite Database** – Quickly get started with an on-disk SQLite file that the app auto-creates in the `instance/` folder.
5. **Flask-Admin** – Includes an admin interface at `/admin` for editing database objects like worlds, campaigns, sessions, NPCs, etc.
6. **PySide6 Wizard** – A cross-platform desktop client (`scripts/app.py`) that simplifies connecting to the server, selecting campaigns/sessions, and chatting as a player.

---

## Architecture

```
                               app.py
                     +-------------------------+
                     |      PySide6 GUI        |
                     | (Desktop Application)   |
                     +-----------↑↓-----------+
                              server.py
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

1. **Client (Wizard GUI)** – A PySide6 application that guides you to connect to the server, pick a campaign/session/player, and then interact with the AI DM in real time.
2. **Flask + Socket.IO** – The server hosts both:
   - A standard RESTful API for managing game entities (worlds, campaigns, players, sessions).
   - A Socket.IO endpoint to handle live chat messages and stream AI responses.
3. **SQLite Database** – By default, everything (world, campaign, session, NPC, and player data) is stored locally in `ai_dm/instance/dnd_ai_dm.db`. 
4. **External LLM** – The server calls out to Google’s Generative AI endpoints (or any other configured provider) to generate DM responses based on your `.env` configuration.

---

## Directory Structure

```
AI-DM/
├── ai_dm
│   ├── database.py         # Database initialization (Flask-SQLAlchemy, migrations)
│   ├── llm.py              # Core LLM (Gemini) integration and DM function-calling logic
│   ├── models_orm.py       # SQLAlchemy ORM models (World, Campaign, Player, Session, etc.)
│   └── server.py           # Main Flask + SocketIO server with routes, streaming chat
├── assets
│   ├── fonts
│   │   ├── MedievalSharp-Regular.ttf
│   │   └── UnifrakturMaguntia-Regular.ttf
│   └── background.jpg      # Background image for the PySide6 GUI
├── scripts
│   ├── app.py              # PySide6 Wizard GUI for connecting and playing
│   └── install_fonts.py    # Installs custom fantasy fonts on first run
├── README.md               # This README
└── requirements.txt        # Required Python dependencies
```

---

## Detailed File Walkthrough

### `ai_dm/database.py`
- Configures **Flask-SQLAlchemy** and Alembic migrations.
- Initializes the SQLite database in `ai_dm/instance/dnd_ai_dm.db`.
- Provides a function `init_db(app)` used by `server.py` to attach the DB to the Flask app.

### `ai_dm/llm.py`
- **Core LLM integration** with Google’s Generative AI (Gemini).
- Contains advanced logic for:
  - Function-calling prompt: specifying how the DM should respond in JSON (with `roll_request`, `speaking_player`, etc.).
  - Validation of the DM’s JSON response, ensuring it references valid player IDs and includes proper formatting.
  - Handling streaming text (`query_dm_function_stream`) if you want chunked responses for a more immersive feel.
  - Building context from the database (world, campaign, recent player actions) to keep the AI’s replies consistent.

### `ai_dm/models_orm.py`
- **SQLAlchemy model definitions** for:
  - `World`, `Campaign`, `Player`, `Session`, `Npc`, `PlayerAction`, etc.
- Each class maps to a database table in SQLite.

### `ai_dm/server.py`
- The **main Flask + SocketIO server** file:
  - **REST endpoints** for managing worlds, campaigns, players, sessions, etc.
  - **Socket.IO event handlers** to handle real-time chat messages, roll requests, and streaming DM responses.
  - Uses `init_db(app)` to create or migrate the database.
  - Contains an admin setup using `flask_admin` with custom forms and validation.

### `scripts/app.py`
- A **PySide6** desktop application that:
  - Opens a multi-page “wizard” to:
    1. Specify the server URL.
    2. Select or create a campaign.
    3. Select or create a session.
    4. Select or create a player.
    5. Enter the real-time chat screen, bridging Socket.IO to the AI DM.
  - Installs fonts if needed (`install_fonts.py`) on first run.

### `scripts/install_fonts.py`
- Installs custom medieval-style fonts (e.g., *MedievalSharp*, *UnifrakturMaguntia*) into your system’s font directory.
- Called automatically on the first run of the PySide6 wizard.

### `assets/`
- Contains resources like fonts and a background image for the GUI.

---

## Getting Started

### Installation

1. **Clone** the repository:
   ```bash
   git clone https://github.com/dreichner21/AIDM.git
   cd AIDM
   ```

2. (Recommended) Create and activate a **virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # or on Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

> **Note**: On Windows, if you see errors installing or importing `pywin32` or other dependencies, try updating `pip` first:  
> `python -m pip install --upgrade pip`

### Environment Variables

**LLM API Key** – The core environment variable is:

- `GOOGLE_GENAI_API_KEY` – Put your actual Google Generative AI key in a `.env` file or export it system-wide.

Create a `.env` file at the project root with content like:

```
GOOGLE_GENAI_API_KEY=<YOUR_API_KEY>
FLASK_SECRET_KEY=<SOME_RANDOM_SECRET_KEY>
```

> **Never commit** your `.env` file to source control.

### Running the Server

1. **Navigate** into the `ai_dm/` folder (or stay in root; either is fine):
   ```bash
   cd ai_dm
   ```
2. **Run the Flask server** (which also starts Socket.IO):
   ```bash
   # From ai_dm folder:
   python server.py
   
   # OR from project root
   python -m ai_dm.server
   ```
3. By default, the server runs on `http://localhost:5000`. 

   - It automatically creates the local SQLite DB (if not already present).
   - The admin interface is at `http://localhost:5000/admin`.

### Using the GUI Wizard

In a **separate** terminal (with the same virtual environment active if you wish), run:

```bash
python scripts/app.py
```

This **Qt** window will guide you through:

1. **Server Page**: Enter the URL (`http://localhost:5000` if running locally).
2. **Campaign Page**: Load or create a new campaign.
3. **Session Page**: Load or create a session for your campaign.
4. **Player Page**: Load or create your player character.
5. **Chat Page**: Interact in real time with the AI DM. You can roll dice, see streaming responses, and play your campaign.

### Admin Interface

Visit `http://localhost:5000/admin` in your web browser to:

- **Browse** and **edit** data for worlds, campaigns, players, sessions, or NPCs.
- Use the CRUD forms to quickly fix campaign descriptions, player classes, or session logs.

> **Tip**: If you want to share your server with friends, consider using **ngrok**:
> ```bash
> ngrok http 5000
> ```
> And provide them the forwarded HTTPS address to paste into their “Server URL” field in `app.py`.

---

## REST API Reference

All endpoints default to JSON-based communication. Below are commonly used endpoints:

### **Worlds**
- **`POST /worlds`**  
  Create a new world:  
  ```json
  {
    "name": "Faerûn",
    "description": "A vast land of sword & sorcery..."
  }
  ```
- **`GET /worlds/<world_id>`**  
  Fetch details of a specific world.

### **Campaigns**
- **`POST /campaigns`**  
  Create a campaign in a given world:
  ```json
  {
    "title": "Dragon's Requiem",
    "description": "...",
    "world_id": 1
  }
  ```
- **`GET /campaigns`**  
  List all campaigns.

- **`GET /campaigns/<campaign_id>`**  
  Get details of a specific campaign.

### **Players**
- **`POST /campaigns/<campaign_id>/players`**  
  Add a new player to the campaign:
  ```json
  {
    "name": "Alice",
    "character_name": "Lyran",
    "race": "Elf",
    "char_class": "Wizard",
    "level": 1
  }
  ```
- **`GET /campaigns/<campaign_id>/players`**  
  List all players in a campaign.

### **Sessions**
- **`POST /sessions/start`**  
  Start a new session for a campaign:
  ```json
  {
    "campaign_id": 1
  }
  ```
  Returns `{"session_id": <ID>}`

- **`POST /sessions/<session_id>/interact`**  
  Send a single user input to the AI DM for a textual response (non-streaming):
  ```json
  {
    "user_input": "I try to pick the lock.",
    "campaign_id": 1,
    "world_id": 1,
    "player_id": 3
  }
  ```
  Returns DM’s textual response in one piece.

- **`POST /sessions/<session_id>/end`**  
  End the session, request a recap from the AI, and store it in the session’s data.

- **`GET /sessions/<session_id>/recap`**  
  Retrieve any stored session recap.

---

## Socket.IO Real-Time Interface

The **PySide6** wizard uses Socket.IO events for real-time chat with streaming AI responses:

### Client → Server Events

- **`join_session`**  
  ```json
  { "session_id": 123 }
  ```
  Joins a Socket.IO “room” for the session, so broadcast messages are properly routed.

- **`send_message`**  
  ```json
  {
    "session_id": 123,
    "campaign_id": 1,
    "world_id": 1,
    "player_id": 3,
    "message": "I open the ancient door..."
  }
  ```
  Sends a user (player) message to the DM. The server then streams back the AI’s response chunk-by-chunk.

### Server → Client Events

- **`new_message`**  
  Broadcasts to all clients in the session, carrying a message with optional speaker info.

- **`dm_response_start`** / **`dm_chunk`** / **`dm_response_end`**  
  Provide chunked (streaming) AI responses. Concatenate `dm_chunk` text segments until `dm_response_end` is received.

- **`roll_request`**  
  In some scenarios, the AI DM may request a dice roll. This event instructs the client to roll a d20 (with advantage/disadvantage, or ability checks, etc.).

- **`error`**  
  Emitted if something goes wrong (e.g., invalid session ID, missing fields).

---

## Contributing

1. **Fork** this repository.
2. **Create a feature branch** for your changes.
3. **Commit** thoroughly tested code.
4. **Open a Pull Request** describing your changes and link any relevant issues.

All contributions, large or small, are welcome.

---

## License

This project is available under the [MIT License](LICENSE). You are free to use, modify, and distribute it as permitted.

---

*Happy adventuring with your AI Dungeon Master!*
