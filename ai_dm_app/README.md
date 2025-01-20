# D&D AI Dungeon Master

An AI-powered Dungeon Master for Dungeons & Dragons campaigns, built with Python, Flask, and OpenAI's GPT.

## Features

- Create and manage D&D worlds, campaigns, and characters
- AI-powered DM responses and storytelling
- Session management with automatic recaps
- Persistent game state tracking
- RESTful API for easy integration

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the server:
   ```bash
   python app.py
   ```

2. The API will be available at `http://localhost:5000`

## API Endpoints

### Worlds
- `POST /worlds` - Create a new world
- `GET /worlds/<world_id>` - Get world details

### Campaigns
- `POST /campaigns` - Create a new campaign
- `GET /campaigns/<campaign_id>` - Get campaign details

### Players
- `POST /campaigns/<campaign_id>/players` - Add a player to a campaign
- `GET /campaigns/<campaign_id>/players` - Get all players in a campaign

### Sessions
- `POST /sessions/start` - Start a new game session
- `POST /sessions/<session_id>/interact` - Send player action and get DM response
- `POST /sessions/<session_id>/end` - End a session and get recap
- `GET /sessions/<session_id>/recap` - Get session recap

## Example Usage

1. Create a new world:
```bash
curl -X POST http://localhost:5000/worlds \
  -H "Content-Type: application/json" \
  -d '{"name": "Forgotten Realms", "description": "A high fantasy world of magic and adventure"}'
```

2. Create a campaign:
```bash
curl -X POST http://localhost:5000/campaigns \
  -H "Content-Type: application/json" \
  -d '{"title": "Lost Mine of Phandelver", "world_id": 1, "description": "A D&D 5E starter campaign"}'
```

3. Add a player:
```bash
curl -X POST http://localhost:5000/campaigns/1/players \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "name": "John",
    "character_name": "Thorin",
    "race": "Dwarf",
    "char_class": "Fighter",
    "level": 1
  }'
```

4. Start a session and interact:
```bash
# Start session
curl -X POST http://localhost:5000/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": 1}'

# Player interaction
curl -X POST http://localhost:5000/sessions/1/interact \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "campaign_id": 1,
    "world_id": 1,
    "user_input": "I want to investigate the tavern"
  }'
```

## License

MIT License 