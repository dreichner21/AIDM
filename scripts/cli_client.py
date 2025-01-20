"""
cli_client.py

A simple CLI tool that interacts with the AI DM server via REST endpoints.
Useful for testing or for users who prefer a terminal-based interface.
"""

import requests
import sys
import time
from typing import Optional, Dict, List
from datetime import datetime

# Adjust this default URL to your local or remote server
BASE_URL = "http://localhost:5000"

class DnDClient:
    def __init__(self):
        self.campaign_id: Optional[int] = None
        self.world_id: Optional[int] = None
        self.session_id: Optional[int] = None
        self.player_id: Optional[int] = None

    def check_server(self) -> bool:
        """Check if the server is responsive."""
        try:
            requests.get(BASE_URL, timeout=2)
            return True
        except requests.RequestException:
            return False

    def wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for server to become available, up to 'timeout' seconds."""
        print("Checking server connection...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.check_server():
                print("Server is running!")
                return True
            print("Server not available. Retrying in 5 seconds...")
            time.sleep(5)

        print(f"\nServer connection timed out after {timeout} seconds.")
        return False

    def list_sessions(self, campaign_id: int) -> List[Dict]:
        """List all sessions for a given campaign."""
        try:
            response = requests.get(f"{BASE_URL}/campaigns/{campaign_id}/sessions")
            response.raise_for_status()
            sessions = response.json()
            return sessions
        except requests.RequestException as e:
            print(f"Error listing sessions: {e}")
            return []

    def load_session(self, session_id: int, campaign_id: int, world_id: int) -> bool:
        """Load existing session details into the client."""
        if not self.check_server() and not self.wait_for_server():
            return False

        self.campaign_id = campaign_id
        self.world_id = world_id
        self.session_id = session_id
        return True

    def start_session(self, campaign_id: int, world_id: int) -> bool:
        """Start a new D&D session in a campaign."""
        if not self.check_server() and not self.wait_for_server():
            return False

        self.campaign_id = campaign_id
        self.world_id = world_id

        try:
            response = requests.post(
                f"{BASE_URL}/sessions/start",
                json={"campaign_id": campaign_id}
            )
            response.raise_for_status()
            self.session_id = response.json()["session_id"]
            return True
        except requests.RequestException as e:
            print(f"Error starting session: {e}")
            return False

    def send_message(self, user_input: str, player_id: Optional[int] = None) -> Optional[str]:
        """
        Send a message to the DM and return the AI's response.
        """
        if not all([self.campaign_id, self.world_id, self.session_id]):
            print("Session not initialized!")
            return None

        payload = {
            "user_input": user_input,
            "campaign_id": self.campaign_id,
            "world_id": self.world_id
        }
        if player_id is not None:
            payload["player_id"] = player_id

        try:
            response = requests.post(
                f"{BASE_URL}/sessions/{self.session_id}/interact",
                json=payload
            )
            response.raise_for_status()
            return response.json().get("dm_response", "").replace("<br>", "\n")
        except requests.RequestException as e:
            print(f"Error sending message: {e}")
            return None

    def end_session(self) -> Optional[str]:
        """End the current session and get a recap from the server."""
        if not self.session_id:
            return None
        try:
            response = requests.post(f"{BASE_URL}/sessions/{self.session_id}/end")
            response.raise_for_status()
            return response.json().get("recap")
        except requests.RequestException as e:
            print(f"Error ending session: {e}")
            return None

def main():
    client = DnDClient()

    # Parse command-line arguments
    try:
        campaign_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        world_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        player_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
    except (IndexError, ValueError):
        print("Usage: python cli_client.py [campaign_id] [world_id] [player_id]")
        print("Using defaults: campaign_id=1, world_id=1, player_id=None")
        campaign_id, world_id, player_id = 1, 1, None

    # List existing sessions
    sessions = client.list_sessions(campaign_id)
    if sessions:
        print("\nExisting sessions for this campaign:")
        for i, session in enumerate(sessions, 1):
            created_at_str = session['created_at'].replace('Z', '')
            try:
                dt_created = datetime.fromisoformat(created_at_str)
                display_date = dt_created.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                display_date = created_at_str
            print(f"{i}. Session {session['session_id']} (Created: {display_date})")

        choice = input("\nEnter session number to load, or press Enter for new session: ").strip()
        if choice and choice.isdigit() and 1 <= int(choice) <= len(sessions):
            chosen_session = sessions[int(choice) - 1]
            if client.load_session(chosen_session['session_id'], campaign_id, world_id):
                print(f"\nLoaded session {chosen_session['session_id']}")
            else:
                print("Failed to load session. Exiting.")
                return
        else:
            # Start new session
            print("\nStarting new D&D session...")
            if not client.start_session(campaign_id, world_id):
                print("Failed to start session. Exiting.")
                return
    else:
        # No existing sessions found, start a new one
        print("\nNo existing sessions found. Starting new D&D session...")
        if not client.start_session(campaign_id, world_id):
            print("Failed to start session. Exiting.")
            return

    print("\nWelcome to the D&D AI DM CLI! Type 'quit' or 'exit' to end the session.")
    print("Session started. You can begin your adventure.\n")

    # Main input loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break

            dm_response = client.send_message(user_input, player_id)
            if dm_response:
                print(f"\nDM: {dm_response}")
        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Ending session...")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            break

    # End session and print recap
    print("\nEnding session...")
    recap = client.end_session()
    if recap:
        print("\nSession Recap:")
        print(recap)

if __name__ == "__main__":
    main()
