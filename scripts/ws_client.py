import requests
import socketio
import sys

def choose_server_url():
    default_url = "https://74bb-108-85-196-134.ngrok-free.app"
    user_input = input(f"Enter the server URL (Press Enter for {default_url}): ").strip()
    return user_input if user_input else default_url

def list_campaigns(server_url):
    print("\nFetching campaigns from server...")
    try:
        resp = requests.get(f"{server_url}/campaigns")
        if resp.status_code == 200:
            campaigns = resp.json()
            # If there's no direct list endpoint in your code, 
            # you might need to handle that differently or omit this step.
            # Alternatively, you can store campaigns if you coded an endpoint like /campaigns returning a list.
            if isinstance(campaigns, dict) and 'error' in campaigns:
                print("Error fetching campaigns:", campaigns['error'])
                return []
            elif isinstance(campaigns, list):
                return campaigns
            else:
                # Some servers might return a single object if you don't have a generic 'list campaigns' route
                return []
        else:
            print("Failed to fetch campaigns. Status code:", resp.status_code)
    except Exception as e:
        print("Error fetching campaigns:", e)
    return []

def pick_campaign(server_url):
    """Let the user pick a campaign from a list or type one in."""
    campaigns = list_campaigns(server_url)
    if not campaigns:
        print("No campaigns found or listing campaigns not supported by the server.")
        # Let user type a campaign_id manually anyway
        campaign_id = input("Enter a campaign_id manually (e.g. 1): ").strip()
        return int(campaign_id)
    
    print("\nAvailable Campaigns:")
    for i, c in enumerate(campaigns, start=1):
        print(f"{i}. [ID={c['campaign_id']}] {c['title']}")
    choice = input("\nEnter the number of a campaign or 'm' to manually enter an ID: ").strip()
    if choice.lower() == 'm':
        campaign_id = input("Enter campaign_id: ").strip()
        return int(campaign_id)
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(campaigns):
                return campaigns[idx-1]['campaign_id']
        except:
            pass
    # fallback
    return 1

def list_sessions_in_campaign(server_url, campaign_id):
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}/sessions")
        resp.raise_for_status()
        sessions = resp.json()
        if isinstance(sessions, dict) and 'error' in sessions:
            print("Error fetching sessions:", sessions['error'])
            return []
        return sessions
    except Exception as e:
        print("Error fetching sessions:", e)
        return []

def pick_session(server_url, campaign_id):
    sessions = list_sessions_in_campaign(server_url, campaign_id)
    if not sessions:
        print("\nNo existing sessions found for this campaign.")
        return start_new_session(server_url, campaign_id)
    
    print("\nExisting sessions:")
    for i, s in enumerate(sessions, start=1):
        print(f"{i}. Session {s['session_id']} (Created: {s['created_at']})")
    
    choice = input("\nEnter session number to load, or press Enter for new session: ").strip()
    if choice == "":
        return start_new_session(server_url, campaign_id)
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(sessions):
                return sessions[idx-1]['session_id']
        except:
            pass
    # fallback
    return start_new_session(server_url, campaign_id)

def start_new_session(server_url, campaign_id):
    print("\nStarting a new session...")
    try:
        resp = requests.post(f"{server_url}/sessions/start", json={"campaign_id": campaign_id})
        resp.raise_for_status()
        return resp.json()["session_id"]
    except Exception as e:
        print("Error starting session:", e)
        return None

def list_players_in_campaign(server_url, campaign_id):
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}/players")
        resp.raise_for_status()
        players = resp.json()
        if isinstance(players, dict) and 'error' in players:
            print("Error fetching players:", players['error'])
            return []
        return players
    except Exception as e:
        print("Error fetching players:", e)
        return []

def pick_player(server_url, campaign_id):
    """Let user pick or create a player record in the chosen campaign."""
    players = list_players_in_campaign(server_url, campaign_id)
    if not players:
        print("\nNo players found for this campaign.")
        return create_player(server_url, campaign_id)
    
    print("\nExisting Players:")
    for i, p in enumerate(players, start=1):
        print(f"{i}. [ID={p['player_id']}] {p['character_name']} (User: {p['name']})")
    
    choice = input("\nEnter the number of a player to select, or press Enter to create new: ").strip()
    if choice == "":
        return create_player(server_url, campaign_id)
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(players):
                return players[idx-1]['player_id']
        except:
            pass
    # fallback
    return create_player(server_url, campaign_id)

def create_player(server_url, campaign_id):
    print("\nLet's create a new player record.")
    name = input("Real user name (e.g., John): ").strip()
    character_name = input("Character name (e.g., Thorin): ").strip()
    race = input("Race (e.g., Dwarf): ").strip()
    char_class = input("Class (e.g., Fighter): ").strip()
    level_input = input("Level (default 1): ").strip()
    level = 1
    if level_input.isdigit():
        level = int(level_input)

    data = {
        "name": name,
        "character_name": character_name,
        "race": race,
        "char_class": char_class,
        "level": level
    }
    try:
        resp = requests.post(
            f"{server_url}/campaigns/{campaign_id}/players",
            json=data
        )
        resp.raise_for_status()
        return resp.json()["player_id"]
    except Exception as e:
        print("Error creating player:", e)
        return None

# ----- WEBSOCKET PART -----
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server.")

@sio.event
def disconnect():
    print("Disconnected from server.")

@sio.on('new_message')
def on_new_message(data):
    """Whenever the server broadcasts 'new_message', print it."""
    message = data.get('message', '')
    print(f"\n--- NEW MESSAGE ---\n{message}\n-------------------\n")


def main():
    print("Welcome to the D&D AI DM WebSocket Client!\n")
    server_url = choose_server_url()
    
    # 1. Choose a campaign
    campaign_id = pick_campaign(server_url)
    print(f"\nSelected campaign_id={campaign_id}")
    
    # 2. Choose or create session
    session_id = pick_session(server_url, campaign_id)
    print(f"Using session_id={session_id}")
    
    # 3. Choose or create player
    player_id = pick_player(server_url, campaign_id)
    print(f"Playing as player_id={player_id}\n")
    
    # 4. We also need to pick a world_id, if your code associates the campaign with a single world
    #    You might already have it from the campaign details. Let's assume we do a quick GET /campaigns/<id>.
    try:
        resp = requests.get(f"{server_url}/campaigns/{campaign_id}")
        resp.raise_for_status()
        campaign_obj = resp.json()
        world_id = campaign_obj.get('world_id', 1)
    except Exception as e:
        print("Could not fetch campaign details, defaulting to world_id=1:", e)
        world_id = 1
    
    # 5. Connect via WebSocket
    print(f"\nConnecting to {server_url} via WebSocket...")
    sio.connect(server_url, transports=['websocket'])  # Force WebSocket if you like
    
    # 6. Join the session room
    sio.emit('join_session', {'session_id': session_id})
    
    print(f"\nAll set! You are player_id={player_id} in session_id={session_id}, campaign_id={campaign_id}, world_id={world_id}.")
    print("Type 'quit' or Ctrl+C to exit.\n")
    
    # 7. Main chat loop
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                break
            
            # Send the message to the server
            # This will invoke the AI logic on the server if set up in @socketio.on('send_message')
            # Make sure your server code expects these fields: session_id, campaign_id, world_id, player_id, message
            sio.emit('send_message', {
                'session_id': session_id,
                'campaign_id': campaign_id,
                'world_id': world_id,
                'player_id': player_id,
                'message': user_input
            })
        except KeyboardInterrupt:
            break
    
    print("Closing connection...")
    sio.disconnect()

if __name__ == "__main__":
    main()
