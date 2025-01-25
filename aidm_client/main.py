"""
app_qt.py

Refactored GUI wizard for the AI-DM application using PySide6 instead of Tkinter.
Requires: PySide6, requests, python-socketio, Pillow (for image resizing, if desired).
"""

import sys
import os
import random
import queue
import requests
import socketio

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, QPlainTextEdit,
    QDialog, QFormLayout, QDialogButtonBox,
)
from PySide6.QtGui import QFont, QTextCursor  # Added QTextCursor here
from PySide6.QtCore import Qt, QTimer

# Global fonts used for a slight fantasy feel (fallback if not installed)
HEADER_FONT = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 24, QFont.Bold)
LABEL_FONT  = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 12)
BUTTON_FONT = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 11, QFont.Bold)
INPUT_FONT  = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 11)

##############################################################################
# Main Wizard Application
##############################################################################

from PySide6.QtGui import QFontDatabase
from pathlib import Path
import subprocess

# Add the client directory to Python path for local imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from install_fonts import check_first_run, mark_first_run_complete

class AIDMWizardApp(QMainWindow):
    """
    Main application window that manages a QStackedWidget of pages:
    1. ServerPage
    2. CampaignPage
    3. SessionPage
    4. PlayerPage
    5. ChatPage
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-DM Wizard (SocketIO)")
        self.setMinimumSize(880, 640)

        if check_first_run():
            self.run_first_time_setup()
            mark_first_run_complete()
            
        self.load_embedded_fonts()

        # Add this debug code to help determine ideal image size
        screen = QtWidgets.QApplication.primaryScreen()
        print(f"Screen size: {screen.size().width()}x{screen.size().height()}")
        print(f"Screen physical DPI: {screen.physicalDotsPerInch()}")
        print(f"Screen logical DPI: {screen.logicalDotsPerInch()}")

        # Get absolute path to background image using correct folder structure
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to scripts folder, then to main AI-DM folder, then into assets
        bg_path = os.path.abspath(os.path.join(current_dir, "..", "assets", "background.jpg"))
        bg_path = bg_path.replace("\\", "/")  # Convert to forward slashes for Qt

        # Debug print to verify path
        print(f"Loading background image from: {bg_path}")

        # Verify image file exists
        if not os.path.exists(bg_path):
            print(f"Warning: Background image not found at {bg_path}")
            # Set a fallback background color
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2B2B2B;
                }
            """)
        else:
            # Set background image with absolute path and improved CSS
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url("{bg_path}");
                    background-repeat: no-repeat;
                    background-position: center center;
                    background-attachment: fixed;
                    /* Change to 'contain' to show full image, or keep 'cover' to fill */
                    background-size: contain;
                }}
                /* Apply the background to the central widget with the same properties */
                QStackedWidget {{
                    background-image: url("{bg_path}");
                    background-repeat: no-repeat;
                    background-position: center center;
                    background-attachment: fixed;
                    background-size: contain;
                    /* Add a dark semi-transparent overlay to improve text readability */
                    background-color: rgba(0, 0, 0, 0.5);
                }}
                QLabel, QCheckBox, QRadioButton, QGroupBox {{
                    color: #FFFFFF;
                    font-size: 12px;
                }}
                QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
                    background-color: rgba(255, 255, 255, 0.9);
                    color: #000000;
                    border: 1px solid #666666;
                    border-radius: 3px;
                }}
                QPushButton {{
                    background-color: rgba(68, 68, 68, 0.8);
                    color: #FFFFFF;
                    border: 1px solid #666666;
                    border-radius: 3px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background-color: rgba(102, 102, 102, 0.8);
                }}
            """)

        # Global state shared across wizard pages
        self.server_url = None
        self.campaign_id = None
        self.world_id = None
        self.session_id = None
        self.player_id = None

        # Central widget: a QStackedWidget that holds all "pages"
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Create pages
        self.pages = {}
        self.pages["ServerPage"]   = ServerPage(self)
        self.pages["CampaignPage"] = CampaignPage(self)
        self.pages["SessionPage"]  = SessionPage(self)
        self.pages["PlayerPage"]   = PlayerPage(self)
        self.pages["ChatPage"]     = ChatPage(self)

        # Add them to the stacked widget
        for name, page_widget in self.pages.items():
            self.central_stack.addWidget(page_widget)

        # Show first page
        self.show_frame("ServerPage")

    def show_frame(self, page_name: str):
        """Switch the QStackedWidget to the page with the given name."""
        widget = self.pages.get(page_name)
        if widget:
            self.central_stack.setCurrentWidget(widget)
            # If the page has on_enter, call it
            if hasattr(widget, "on_enter"):
                widget.on_enter()

    def check_first_run(self):
        from install_fonts import check_first_run
        return check_first_run()
    
    def run_first_time_setup(self):
        try:
            install_script = Path(__file__).parent / "install_fonts.py"
            subprocess.run([
                sys.executable, 
                str(install_script.resolve())
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                None,
                "First Run Setup Failed",
                f"Could not install medieval fonts:\n{e}\n"
                "The app will use system fonts instead.",
                QMessageBox.Ok
            )
            
    def load_embedded_fonts(self):
        font_dir = Path(__file__).parent.parent / "assets" / "fonts"
        loaded = []
        
        for font in ["MedievalSharp-Regular.ttf", "UnifrakturMaguntia-Regular.ttf"]:
            font_path = str(font_dir / font)
            if QFontDatabase.addApplicationFont(font_path) != -1:
                loaded.append(font)
                
        if not loaded:
            print("Warning: Could not load embedded medieval fonts")


##############################################################################
# Base Page
##############################################################################

class BasePage(QWidget):
    """
    A base page widget with a header label. Subclassed by each step page.
    """
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.controller = parent  # The AIDMWizardApp
        self.layout_main = QVBoxLayout(self)
        self.setLayout(self.layout_main)

        # Header Label
        self.label_header = QLabel(title, self)
        self.label_header.setFont(HEADER_FONT)
        self.label_header.setAlignment(Qt.AlignCenter)
        self.layout_main.addWidget(self.label_header)

        # A layout area below the header for content
        self.content_layout = QVBoxLayout()
        self.layout_main.addLayout(self.content_layout)


##############################################################################
# 1. ServerPage
##############################################################################

class ServerPage(BasePage):
    """
    Page to connect to the AI-DM server.
    """
    def __init__(self, parent):
        super().__init__(parent, title="1. Connect to AI-DM Server")

        self.server_edit = QLineEdit(self)
        self.server_edit.setFont(INPUT_FONT)
        # IMPORTANT: Set the default server URL here
        self.server_edit.setText("http://localhost:5000")  

        self.button_next = QPushButton("Next")
        self.button_next.setFont(BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        # Layout
        label = QLabel("Enter your AI-DM Server URL:")
        label.setFont(LABEL_FONT)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.server_edit)
        vbox.addWidget(self.button_next, alignment=Qt.AlignCenter)

        self.content_layout.addLayout(vbox)
        self.content_layout.addStretch()

    def next_step(self):
        """
        Proceed to the next step after validating the server URL.
        """
        url = self.server_edit.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Server URL cannot be empty.")
            return
        self.controller.server_url = url
        self.controller.show_frame("CampaignPage")


##############################################################################
# 2. CampaignPage
##############################################################################

class CampaignPage(BasePage):
    """
    Page to choose or create a campaign.
    """
    def __init__(self, parent):
        super().__init__(parent, title="2. Choose or Create a Campaign")

        label = QLabel("Select or Create a Campaign:")
        label.setFont(LABEL_FONT)

        self.campaign_combo = QComboBox()
        self.campaign_combo.setFont(INPUT_FONT)

        self.button_load = QPushButton("Load Campaigns")
        self.button_load.setFont(BUTTON_FONT)
        self.button_load.clicked.connect(self.load_campaigns)

        self.button_create = QPushButton("Create New")
        self.button_create.setFont(BUTTON_FONT)
        self.button_create.clicked.connect(self.create_campaign_prompt)

        self.button_next = QPushButton("Next")
        self.button_next.setFont(BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        self.content_layout.addWidget(label)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.campaign_combo)
        row_layout.addWidget(self.button_load)
        self.content_layout.addLayout(row_layout)

        row_layout2 = QHBoxLayout()
        row_layout2.addStretch()
        row_layout2.addWidget(self.button_create)
        row_layout2.addWidget(self.button_next)
        row_layout2.addStretch()
        self.content_layout.addLayout(row_layout2)

        self.content_layout.addStretch()

    def on_enter(self):
        """
        Load campaigns when the page is entered.
        """
        self.load_campaigns()

    def load_campaigns(self):
        """
        Load campaigns from the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/campaigns"  # Add /api/ prefix
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            campaigns = resp.json() if resp.text else []
            if not isinstance(campaigns, list):
                campaigns = []

            self.campaign_combo.clear()
            for c in campaigns:
                c_id = c.get("campaign_id")
                c_title = c.get("title")
                text = f"{c_id}: {c_title}"
                self.campaign_combo.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load campaigns:\n{e}")

    def create_campaign_prompt(self):
        """
        Prompt to create a new campaign.
        """
        dialog = CampaignCreateDialog(self.controller)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Campaign created.")
            self.load_campaigns()

    def next_step(self):
        """
        Proceed to the next step after selecting a campaign.
        """
        choice = self.campaign_combo.currentText().strip()
        if not choice:
            QMessageBox.information(self, "Info", "Select or create a campaign first.")
            return

        cid_str = choice.split(":", 1)[0].strip()
        if not cid_str.isdigit():
            return

        self.controller.campaign_id = int(cid_str)
        # Fetch campaign detail to get world_id
        base_url = self.controller.server_url.rstrip("/")
        c_url = f"{base_url}/api/campaigns/{self.controller.campaign_id}"  # Add /api/ prefix
        try:
            r = requests.get(c_url, timeout=5)
            r.raise_for_status()
            data = r.json()
            self.controller.world_id = data.get("world_id", 1)
        except:
            self.controller.world_id = 1

        self.controller.show_frame("SessionPage")


class CampaignCreateDialog(QDialog):
    """
    Dialog to create a new campaign.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("New Campaign")
        self.setModal(True)
        layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.desc_edit = QLineEdit(self)
        self.world_edit = QLineEdit(self)
        self.world_edit.setText("1")

        layout.addRow("Campaign Title:", self.title_edit)
        layout.addRow("Description:", self.desc_edit)
        layout.addRow("World ID:", self.world_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.do_create)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def do_create(self):
        """
        Create a new campaign on the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/campaigns"  # Add /api/ prefix
        data = {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "world_id": int(self.world_edit.text() or "1"),
        }
        try:
            r = requests.post(url, json=data, timeout=5)
            r.raise_for_status()
            cid = r.json().get("campaign_id")
            if cid:
                QMessageBox.information(self, "Success", f"Created Campaign ID={cid}")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Response did not contain campaign_id.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create campaign:\n{e}")


##############################################################################
# 3. SessionPage
##############################################################################

class SessionPage(BasePage):
    """
    Page to choose or create a session.
    """
    def __init__(self, parent):
        super().__init__(parent, title="3. Choose or Create a Session")

        label = QLabel("Select or Create a Session:")
        label.setFont(LABEL_FONT)

        self.session_combo = QComboBox()
        self.session_combo.setFont(INPUT_FONT)

        self.button_load = QPushButton("Load Sessions")
        self.button_load.setFont(BUTTON_FONT)
        self.button_load.clicked.connect(self.load_sessions)

        self.button_create = QPushButton("New Session")
        self.button_create.setFont(BUTTON_FONT)
        self.button_create.clicked.connect(self.create_session)

        self.button_next = QPushButton("Next")
        self.button_next.setFont(BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        self.content_layout.addWidget(label)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.session_combo)
        row_layout.addWidget(self.button_load)
        self.content_layout.addLayout(row_layout)

        row_layout2 = QHBoxLayout()
        row_layout2.addStretch()
        row_layout2.addWidget(self.button_create)
        row_layout2.addWidget(self.button_next)
        row_layout2.addStretch()
        self.content_layout.addLayout(row_layout2)

        self.content_layout.addStretch()

    def on_enter(self):
        """
        Load sessions when the page is entered.
        """
        self.load_sessions()

    def load_sessions(self):
        """
        Load sessions from the server.
        """
        if not self.controller.campaign_id:
            QMessageBox.critical(self, "Error", "No campaign selected.")
            return
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/sessions/campaigns/{self.controller.campaign_id}/sessions"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            sessions = resp.json() if resp.text else []
            if not isinstance(sessions, list):
                sessions = []

            self.session_combo.clear()
            for s in sessions:
                sid = s.get("session_id")
                created = s.get("created_at", "")
                text = f"{sid} (Created: {created})"
                self.session_combo.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sessions:\n{e}")

    def create_session(self):
        """
        Create a new session on the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/sessions/start"  # Remove /api/
        data = {"campaign_id": self.controller.campaign_id}
        try:
            resp = requests.post(url, json=data, timeout=5)
            resp.raise_for_status()
            new_sid = resp.json().get("session_id")
            if new_sid:
                QMessageBox.information(self, "Success", f"Created Session ID={new_sid}")
            else:
                QMessageBox.warning(self, "Error", "No session_id returned.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create session:\n{e}")

    def next_step(self):
        """
        Proceed to the next step after selecting a session.
        """
        choice = self.session_combo.currentText().strip()
        if not choice:
            QMessageBox.information(self, "Info", "Select or create a session first.")
            return
        sid_str = choice.split(" ", 1)[0].strip()
        if not sid_str.isdigit():
            return
        self.controller.session_id = int(sid_str)
        self.controller.show_frame("PlayerPage")


##############################################################################
# 4. PlayerPage
##############################################################################

class PlayerPage(BasePage):
    """
    Page to choose or create a player.
    """
    def __init__(self, parent):
        super().__init__(parent, title="4. Choose or Create a Player")

        label = QLabel("Select or Create a Player:")
        label.setFont(LABEL_FONT)

        self.player_combo = QComboBox()
        self.player_combo.setFont(INPUT_FONT)

        self.button_load = QPushButton("Load Players")
        self.button_load.setFont(BUTTON_FONT)
        self.button_load.clicked.connect(self.load_players)

        self.button_create = QPushButton("New Player")
        self.button_create.setFont(BUTTON_FONT)
        self.button_create.clicked.connect(self.create_player_prompt)

        self.button_next = QPushButton("Next")
        self.button_next.setFont(BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        self.content_layout.addWidget(label)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.player_combo)
        row_layout.addWidget(self.button_load)
        self.content_layout.addLayout(row_layout)

        row_layout2 = QHBoxLayout()
        row_layout2.addStretch()
        row_layout2.addWidget(self.button_create)
        row_layout2.addWidget(self.button_next)
        row_layout2.addStretch()
        self.content_layout.addLayout(row_layout2)

        self.content_layout.addStretch()

    def on_enter(self):
        """
        Load players when the page is entered.
        """
        self.load_players()

    def load_players(self):
        """
        Load players from the server.
        """
        if not self.controller.campaign_id:
            QMessageBox.critical(self, "Error", "No campaign selected.")
            return
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/players/campaigns/{self.controller.campaign_id}/players"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            players = resp.json() if resp.text else []
            if not isinstance(players, list):
                players = []

            self.player_combo.clear()
            for p in players:
                pid = p.get("player_id")
                cname = p.get("character_name")
                uname = p.get("name")
                text = f"{pid}: {cname} ({uname})"
                self.player_combo.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load players:\n{e}")

    def create_player_prompt(self):
        """
        Prompt to create a new player.
        """
        dialog = PlayerCreateDialog(self.controller)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Player created.")
            self.load_players()

    def next_step(self):
        """
        Proceed to the next step after selecting a player.
        """
        choice = self.player_combo.currentText().strip()
        if not choice:
            QMessageBox.information(self, "Info", "Select or create a player first.")
            return
        pid_str = choice.split(":", 1)[0].strip()
        if not pid_str.isdigit():
            return
        self.controller.player_id = int(pid_str)
        self.controller.show_frame("ChatPage")


class PlayerCreateDialog(QDialog):
    """
    Dialog to create a new player.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("New Player")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_edit       = QLineEdit(self)
        self.char_name_edit  = QLineEdit(self)
        self.race_edit       = QLineEdit(self)
        self.class_edit      = QLineEdit(self)
        self.level_edit      = QLineEdit(self)
        self.level_edit.setText("1")

        layout.addRow("User Name:", self.name_edit)
        layout.addRow("Character Name:", self.char_name_edit)
        layout.addRow("Race:", self.race_edit)
        layout.addRow("Class:", self.class_edit)
        layout.addRow("Level:", self.level_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.do_create)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def do_create(self):
        """
        Create a new player on the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/players/campaigns/{self.controller.campaign_id}/players"
        data = {
            "name": self.name_edit.text().strip(),
            "character_name": self.char_name_edit.text().strip(),
            "race": self.race_edit.text().strip(),
            "char_class": self.class_edit.text().strip(),
        }
        lv_str = self.level_edit.text().strip()
        data["level"] = int(lv_str) if lv_str.isdigit() else 1
        try:
            r = requests.post(url, json=data, timeout=5)
            r.raise_for_status()
            pid = r.json().get("player_id")
            if pid:
                QMessageBox.information(self, "Success", f"Player created (ID={pid})")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No player_id returned.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create player:\n{e}")


##############################################################################
# 5. ChatPage
##############################################################################

class ChatPage(BasePage):
    """
    Final step: Real-time chat with the AI DM via SocketIO.
    """
    # Add signal for real-time UI updates
    update_chat_signal = QtCore.Signal(str)

    def __init__(self, parent):
        super().__init__(parent, title="AI-DM")

        # Add QTextCursor enum import
        from PySide6.QtGui import QTextCursor

        # SocketIO client and a thread-safe queue for incoming messages
        self.sio = socketio.Client()
        self.msg_queue = queue.Queue()

        # Register socket.io event handlers
        @self.sio.event
        def connect():
            self.msg_queue.put("Connected to the server via SocketIO.")
            if self.controller.session_id:
                self.sio.emit('join_session', {'session_id': self.controller.session_id})

        @self.sio.event
        def connect_error(data):
            # If something goes wrong during connection, log it to the chat
            self.msg_queue.put(f"Connection failed: {data}")

        @self.sio.event
        def disconnect():
            self.msg_queue.put("Disconnected from the server.")

        @self.sio.on('new_message')
        def on_new_message(data):
            # Just like the old code, add extra line break
            message = data.get('message', '')
            self.msg_queue.put(f"\n--- NEW MESSAGE ---\n{message}\n")

        # NEW: Handle streaming chunks
        @self.sio.on('stream_chunk')
        def on_stream_chunk(data):
            chunk = data.get('chunk', '')
            self.msg_queue.put(chunk)  # Direct chunk streaming to chat

        # Main chat UI - with improved styling
        self.chat_display = QPlainTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(LABEL_FONT)
        
        # More specific styling to ensure text visibility
        self.chat_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #404040;
                selection-color: #FFFFFF;
                border: 1px solid #333333;
            }
        """)
        
        # Add test text to verify visibility
        self.chat_display.setPlainText("Chat initialized. If you can see this text, styling is working correctly.")

        self.input_line = QLineEdit()
        self.input_line.setFont(INPUT_FONT)
        self.input_line.returnPressed.connect(self.send_message)

        self.btn_send = QPushButton("Send")
        self.btn_send.setFont(BUTTON_FONT)
        self.btn_send.clicked.connect(self.send_message)

        self.btn_end = QPushButton("End Session")
        self.btn_end.setFont(BUTTON_FONT)
        self.btn_end.clicked.connect(self.end_session)

        # Dice row with improved styling for macOS visibility
        self.dice_combo = QComboBox()
        self.dice_combo.setFont(INPUT_FONT)
        self.dice_combo.addItems(["d4", "d6", "d8", "d10", "d12", "d20", "d100"])
        # Add specific styling for the combo box to ensure text visibility
        self.dice_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                color: black;
                padding: 5px;
                border: 1px solid #666666;
                border-radius: 3px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                width: 0;
                height: 0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
        """)

        self.btn_roll = QPushButton("Roll")
        self.btn_roll.setFont(BUTTON_FONT)
        self.btn_roll.clicked.connect(self.roll_die)

        self.label_roll_result = QLabel("")
        self.label_roll_result.setFont(QFont(LABEL_FONT.family(), 12, QFont.Bold))

        # Update to use only the generic dice emoji
        self.dice_emojis = ["🎲"]  # Only use the generic dice emoji

        # Layout
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_display)

        send_layout = QHBoxLayout()
        send_layout.addWidget(self.input_line)
        send_layout.addWidget(self.btn_send)
        send_layout.addWidget(self.btn_end)
        chat_layout.addLayout(send_layout)

        dice_layout = QHBoxLayout()
        dice_layout.addWidget(self.dice_combo)
        dice_layout.addWidget(self.btn_roll)
        dice_layout.addWidget(self.label_roll_result)
        dice_layout.addStretch()
        chat_layout.addLayout(dice_layout)

        self.content_layout.addLayout(chat_layout)

        # Set up a QTimer to poll the msg_queue periodically
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_queue)
        self.poll_timer.start(100)  # poll every 100ms

        # Clear the initial test message from chat
        self.chat_display.clear()
        
        # Track if we're currently in a DM response
        self.in_dm_response = False
        self.current_message = []
        
        @self.sio.on('stream_chunk')
        def on_stream_chunk(data):
            chunk = data.get('chunk', '')
            if not self.in_dm_response:
                self.in_dm_response = True
                self.msg_queue.put("\nDM: ")  # Start new DM line
            self.current_message.append(chunk)
            self.msg_queue.put(chunk)  # Stream chunk directly
            
        @self.sio.on('new_message')
        def on_new_message(data):
            message = data.get('message', '')
            if "Player" in message or "You:" in message:
                # This is a player message, reset DM state
                self.in_dm_response = False
                self.current_message = []
            self.msg_queue.put(f"\n{message}")

        # Add state for tracking DM response
        self.current_dm_response = ""
        self.current_dm_session = None
        self.last_message_was_dm = False

        # ...existing socket event handlers...

        @self.sio.on('dm_response_start')
        def handle_dm_start(data):
            self.current_dm_session = data.get('session_id')
            self.current_dm_response = ""
            self.last_message_was_dm = True
            self.msg_queue.put("\nDM: ")

        @self.sio.on('dm_chunk')
        def handle_dm_chunk(data):
            if data.get('session_id') == self.current_dm_session:
                chunk = data.get('chunk', '')
                self.current_dm_response += chunk
                self.msg_queue.put(chunk)

        @self.sio.on('dm_response_end')
        def handle_dm_end(data):
            if data.get('session_id') == self.current_dm_session:
                self.msg_queue.put("\n")
                self.current_dm_response = ""
                self.current_dm_session = None
                self.last_message_was_dm = False

        # Connect the signal to the update_chat_display slot
        self.update_chat_signal.connect(self.update_chat_display)

        # State tracking for DM responses
        self.is_streaming = False
        self.current_response = []
        self.last_line = ""

        # Modify SocketIO event handlers
        @self.sio.on('dm_response_start')
        def handle_dm_start(data):
            self.is_streaming = True
            self.current_response = []
            self.msg_queue.put("\nDM: ")

        @self.sio.on('dm_chunk')
        def handle_dm_chunk(data):
            if self.is_streaming:
                chunk = data.get('chunk', '')
                if chunk:
                    self.current_response.append(chunk)
                    self.msg_queue.put(chunk)

        @self.sio.on('dm_response_end')
        def handle_dm_end(data):
            if self.is_streaming:
                self.msg_queue.put("\n")  # Add newline after response
                self.is_streaming = False
                self.current_response = []
                self.last_line = ""

        # Clean up old conflicting handlers
        if hasattr(self.sio, 'handlers'):
            self.sio.handlers = {
                k: v for k, v in self.sio.handlers.items() 
                if k not in ['stream_chunk', 'new_message']
            }

        @self.sio.on('new_message')
        def handle_new_message(data):
            message = data.get('message', '')
            if message and not self.is_streaming:
                self.msg_queue.put(f"\n{message}\n")

        # Modify the new_message handler to be inside __init__
        @self.sio.on('new_message')
        def handle_new_message(data):
            # Only process messages from the DM
            message = data.get('message', '')
            if not any(message.startswith(prefix) for prefix in ["You:", "Player:"]):
                # This is a DM message, so display it
                self.msg_queue.put(f"\n{message}")

        @self.sio.on('new_message')
        def handle_new_message(data):
            message = data.get('message', '')
            speaker = data.get('speaker', '')  # New: get speaker info
            
            if speaker and message:
                # Format: "Character: Message"
                display_text = f"\n{speaker}: {message}"
            else:
                # Fallback for system messages or DM responses
                display_text = f"\n{message}"
                
            self.msg_queue.put(display_text)

    def on_enter(self):
        """
        Connect to the SocketIO server when the page is entered.
        """
        # Connect socket if not connected
        if not self.sio.connected:
            server_url = self.controller.server_url.strip()
            self.log(f"Connecting to SocketIO server at {server_url}...")
            try:
                # Simplified connection parameters that are supported
                self.sio.connect(
                    server_url,
                    wait=True,
                    transports=["websocket"],
                    socketio_path="socket.io"
                )
            except Exception as e:
                self.log(f"Error connecting to SocketIO server:\n{e}")

    def poll_queue(self):
        """
        Poll the message queue for new messages.
        """
        try:
            while True:
                text = self.msg_queue.get_nowait()
                self.update_chat_signal.emit(text)
        except queue.Empty:
            pass

    def log(self, text):
        """
        Log a message to the chat display.
        """
        self.update_chat_signal.emit(text + "\n")

    def update_chat_display(self, text):
        """
        Update the chat display with new text, handling line breaks properly.
        """
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Add extra spacing between messages if it starts with 'DM:' or 'Player' to visually separate
        if text.strip().startswith(("DM:", "Player")):
            if not self.chat_display.toPlainText().endswith("\n\n"):
                cursor.insertText("\n")

        # Check if this message starts with "You:" and replace with the player's character name
        if text.strip().startswith("You:"):
            base_url = self.controller.server_url.rstrip("/")
            player_url = f"{base_url}/api/players/{self.controller.player_id}"
            try:
                # Attempt to fetch the player's character name
                r = requests.get(player_url, timeout=5)
                r.raise_for_status()
                player_info = r.json()
                # If player_info has 'character_name', use it
                if 'character_name' in player_info:
                    char_name = player_info['character_name']
                    # Perform the actual replacement in text
                    text = text.replace("You:", f"{char_name}:")
                else:
                    # Fallback: if for some reason there's no character_name
                    text = text.replace("You:", "Player:")
            except Exception:
                # If request fails or times out, fallback to "Player:"
                text = text.replace("You:", "Player:")

        # Clean up the text while preserving intentional breaks
        if text.strip():
            # This step merges multiple lines into one; remove if you want each chunk on its own line
            cleaned_text = " ".join(text.splitlines())
            cursor.insertText(cleaned_text)
        
        # Insert a newline if the message ends with punctuation or if streaming has ended
        if not self.is_streaming or text.strip().endswith((".", "!", "?")):
            if not self.chat_display.toPlainText().endswith("\n"):
                cursor.insertText("\n")
        
        # Optional: Smart scrolling—only scroll if near bottom
        scrollbar = self.chat_display.verticalScrollBar()
        should_scroll = scrollbar.value() >= scrollbar.maximum() - 4
        
        if should_scroll:
            scrollbar.setValue(scrollbar.maximum())
            self.chat_display.setTextCursor(cursor)
            self.chat_display.ensureCursorVisible()

    def send_message(self):
        """
        Send a message to the server and display it locally first.
        """
        msg = self.input_line.text().strip()
        if not msg:
            return
            
        # Clear input before processing to prevent double-send
        self.input_line.clear()

        # Always display character name from local state
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/players/{self.controller.player_id}"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            char_name = data.get("character_name", "Unknown Player")
        except:
            char_name = "Unknown Player"

        # Display message locally with character name and ensure spacing
        self.update_chat_signal.emit(f"\n{char_name}: {msg}\n")
        QtWidgets.QApplication.processEvents()

        if not self.sio.connected:
            self.msg_queue.put("Not connected to SocketIO server.")
            return

        payload = {
            "session_id": self.controller.session_id,
            "campaign_id": self.controller.campaign_id,
            "world_id": self.controller.world_id,
            "player_id": self.controller.player_id,
            "message": msg
        }
        self.sio.emit('send_message', payload)

    def end_session(self):
        """
        End the current session.
        """
        if not self.controller.session_id:
            self.msg_queue.put("No session to end.")
            return
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/sessions/{self.controller.session_id}/end"
        try:
            r = requests.post(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            recap = data.get("recap", "No recap.")
            self.msg_queue.put("----- SESSION ENDED -----")
            self.msg_queue.put(f"Recap:\n{recap}")
            # Clear session ID
            self.controller.session_id = None
        except Exception as e:
            self.msg_queue.put(f"Error ending session:\n{e}")

    def roll_die(self):
        """
        Roll a die and display the result.
        """
        die_type = self.dice_combo.currentText()
        if not die_type.startswith("d"):
            return
        max_val = int(die_type[1:])
        result = random.randint(1, max_val)
        self.label_roll_result.setText(str(result))
        # Pick a random dice emoji
        emoji = random.choice(self.dice_emojis)
        self.msg_queue.put(f"{emoji} Roll {die_type}: {result}")

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Clean up SocketIO on close if needed.
        """
        if self.sio and self.sio.connected:
            self.sio.disconnect()
        super().closeEvent(event)


##############################################################################
# main
##############################################################################

def main():
    """
    Main entry point for the application.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = AIDMWizardApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
