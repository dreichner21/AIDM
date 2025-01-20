"""
ws_client.py

A sample WebSocket (SocketIO) client to demonstrate real-time interaction
with the AI DM server. Uses `python-socketio` to connect and communicate.
"""

import requests
import socketio
import sys

def choose_server_url():
    """
    Prompt the user for a server URL or fall back to a default value.
    """
    default_url = "https://74bb-108-85-196-134.ngrok-free.app"
    user_input = input(f"Enter the server URL (Press Enter for {default_url}): ").strip()
    return user_input if user_input else default_url

def list_campaigns(server_url):
    """
    Optional helper to list campaigns if your server supports a GET /campaigns route
    that returns a list. Adjust as needed if you have a different mechanism.
    """
    try:
        print("\nFetching campaigns from server...")
        resp = requests.get(f"{server_url}/campaigns")
        if resp.status_code == 200:
            campaigns = resp.json()
            if isinstance(campaigns, list):
                return campaigns
            # If your server doesn't provide a list route, handle accordingly
            return []
        else:
            print("Failed to fetch campaigns. Status code:", resp.status_code)
    except Exception as e:
        print("Error fetching campaigns:", e)
    return []

def pick_campaign(server_url):
    """
    Prompt the user to choose from a list of campaigns or manually enter one.
    """
    campaigns = list_campaigns(server_url)
    if not campaigns:
        print("No campaigns found or listing not supported.")
        choice = input("Enter a campaign_id manually: ").strip()
        return int(choice)

    print("\nAvailable Campaigns:")
    for i, c in enumerate(campaigns, start=1):
        print(f"{i}. [ID={c['campaign_id']}] {c['title']}")
    choice = input("\nEnter number or 'm' to manually enter an ID: ").strip()
    if choice.lower() == 'm':
        return int(input("Enter campaign_id: ").strip())
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(campaigns):
                return campaigns[idx-1]['campaign_id']
        except:
            pass
    return 1

def list_sessions_in_campaign(server_url, campaign_id):
    """
    Retrieve all sessions for a campaign. If it fails, return empty list.
    """
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}/sessions")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("Error fetching sessions:", e)
        return []

def pick_session(server_url, campaign_id):
    """
    Prompt the user to pick an existing session or start a new one.
    """
    sessions = list_sessions_in_campaign(server_url, campaign_id)
    if not sessions:
        print("\nNo existing sessions found for this campaign.")
        return start_new_session(server_url, campaign_id)

    print("\nExisting sessions:")
    for i, s in enumerate(sessions, start=1):
        print(f"{i}. Session {s['session_id']} (Created: {s['created_at']})")

    choice = input("\nEnter session number to load, or press Enter for new: ").strip()
    if not choice:
        return start_new_session(server_url, campaign_id)
    try:
        idx = int(choice)
        if 1 <= idx <= len(sessions):
            return sessions[idx-1]['session_id']
    except:
        pass
    return start_new_session(server_url, campaign_id)

def start_new_session(server_url, campaign_id):
    """
    Create a new session on the server for a campaign.
    """
    print("\nStarting a new session...")
    try:
        resp = requests.post(f"{server_url}/sessions/start", json={"campaign_id": campaign_id})
        resp.raise_for_status()
        return resp.json()["session_id"]
    except Exception as e:
        print("Error starting session:", e)
        return None

def list_players_in_campaign(server_url, campaign_id):
    """
    Retrieve all players in a campaign. Returns empty list on error.
    """
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}/players")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("Error fetching players:", e)
        return []

def pick_player(server_url, campaign_id):
    """
    Prompt user to pick an existing player or create a new one.
    """
    players = list_players_in_campaign(server_url, campaign_id)
    if not players:
        print("\nNo players found for this campaign.")
        return create_player(server_url, campaign_id)

    print("\nExisting Players:")
    for i, p in enumerate(players, start=1):
        print(f"{i}. [ID={p['player_id']}] {p['character_name']} (User: {p['name']})")

    choice = input("\nEnter player number or press Enter to create new: ").strip()
    if not choice:
        return create_player(server_url, campaign_id)
    try:
        idx = int(choice)
        if 1 <= idx <= len(players):
            return players[idx-1]['player_id']
    except:
        pass
    return create_player(server_url, campaign_id)

def create_player(server_url, campaign_id):
    """
    Prompt user for player info and create a new record on the server.
    """
    print("\nCreate a new player.")
    name = input("Real user name: ").strip()
    character_name = input("Character name: ").strip()
    race = input("Race (e.g. Dwarf): ").strip()
    char_class = input("Class (e.g. Fighter): ").strip()
    level_input = input("Level (default 1): ").strip()
    level = int(level_input) if level_input.isdigit() else 1

    data = {
        "name": name,
        "character_name": character_name,
        "race": race,
        "char_class": char_class,
        "level": level
    }
    try:
        resp = requests.post(f"{server_url}/campaigns/{campaign_id}/players", json=data)
        resp.raise_for_status()
        return resp.json()["player_id"]
    except Exception as e:
        print("Error creating player:", e)
        return None

# Create a SocketIO client instance
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server via SocketIO.")

@sio.event
def disconnect():
    print("Disconnected from the server.")

@sio.on('new_message')
def on_new_message(data):
    """
    Handler for 'new_message' events broadcast by the server.
    Prints out the message.
    """
    message = data.get('message', '')
    print(f"\n--- NEW MESSAGE ---\n{message}\n-------------------\n")

def main():
    print("Welcome to the D&D AI DM WebSocket Client!\n")
    server_url = choose_server_url()

    # 1. Choose a campaign
    campaign_id = pick_campaign(server_url)
    print(f"Selected campaign_id={campaign_id}")

    # 2. Choose a session or create new
    session_id = pick_session(server_url, campaign_id)
    if not session_id:
        print("No valid session. Exiting.")
        return
    print(f"Using session_id={session_id}")

    # 3. Choose or create a player
    player_id = pick_player(server_url, campaign_id)
    print(f"Playing as player_id={player_id}")

    # 4. Retrieve campaign details to find the world_id
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}")
        resp.raise_for_status()
        campaign_obj = resp.json()
        world_id = campaign_obj.get('world_id', 1)
    except Exception as e:
        print(f"Could not fetch campaign details, defaulting to world_id=1: {e}")
        world_id = 1

    # 5. Connect to the server
    print(f"\nConnecting to {server_url} via WebSocket...")
    sio.connect(server_url, transports=['websocket'])

    # 6. Join the session room
    sio.emit('join_session', {'session_id': session_id})

    print(f"\nAll set! You are player_id={player_id} in session_id={session_id}, campaign_id={campaign_id}, world_id={world_id}.")
    print("Type 'quit' or Ctrl+C to exit.\n")

    # 7. Main chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() == 'quit':
                break

            sio.emit('send_message', {
                'session_id': session_id,
                'campaign_id': campaign_id,
                'world_id': world_id,
                'player_id': player_id,
                'message': user_input
            })
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    print("Closing connection...")
    sio.disconnect()

if __name__ == "__main__":
    main()
