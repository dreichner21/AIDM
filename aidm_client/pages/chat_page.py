import sys
import random
import queue
import requests
import socketio

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QPlainTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor

from ..constants import HEADER_FONT, LABEL_FONT, BUTTON_FONT, INPUT_FONT
from .base_page import BasePage

class ChatPage(BasePage):
    """
    Final step: Real-time chat with the AI DM via SocketIO.
    """
    update_chat_signal = Signal(str)  # For thread-safe UI updates

    def __init__(self, parent):
        super().__init__(parent, title="AI-DM")

        self.sio = socketio.Client()
        self.msg_queue = queue.Queue()

        # Real-time chat display
        self.chat_display = QPlainTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(LABEL_FONT)
        self.chat_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #404040;
                selection-color: #FFFFFF;
                border: 1px solid #333333;
            }
        """)

        self.input_line = QLineEdit()
        self.input_line.setFont(INPUT_FONT)
        self.input_line.returnPressed.connect(self.send_message)

        self.btn_send = QPushButton("Send")
        self.btn_send.setFont(BUTTON_FONT)
        self.btn_send.clicked.connect(self.send_message)

        self.btn_end = QPushButton("End Session")
        self.btn_end.setFont(BUTTON_FONT)
        self.btn_end.clicked.connect(self.end_session)

        # Dice roll UI
        self.dice_combo = QComboBox()
        self.dice_combo.setFont(INPUT_FONT)
        self.dice_combo.addItems(["d4", "d6", "d8", "d10", "d12", "d20", "d100"])

        self.btn_roll = QPushButton("Roll")
        self.btn_roll.setFont(BUTTON_FONT)
        self.btn_roll.clicked.connect(self.roll_die)

        self.label_roll_result = QLabel("")
        self.label_roll_result.setFont(LABEL_FONT)

        self.dice_emojis = ["🎲"]  # Only a generic dice emoji

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

        # Timer to poll incoming socket messages
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_queue)
        self.poll_timer.start(100)

        # Connect the update signal to update_chat_display
        self.update_chat_signal.connect(self.update_chat_display)

        # State for streaming DM responses
        self.is_streaming = False
        self.current_response = []
        self.last_line = ""

        # Register SocketIO event handlers
        @self.sio.event
        def connect():
            self.msg_queue.put("Connected to the server via SocketIO.")
            if self.controller.session_id:
                self.sio.emit('join_session', {'session_id': self.controller.session_id})

        @self.sio.event
        def connect_error(data):
            self.msg_queue.put(f"Connection failed: {data}")

        @self.sio.event
        def disconnect():
            self.msg_queue.put("Disconnected from the server.")

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
                self.msg_queue.put("\n")
                self.is_streaming = False
                self.current_response = []
                self.last_line = ""

        @self.sio.on('new_message')
        def handle_new_message(data):
            message = data.get('message', '')
            speaker = data.get('speaker', '')
            if speaker and message:
                display_text = f"\n{speaker}: {message}"
            else:
                display_text = f"\n{message}"
            self.msg_queue.put(display_text)

    def on_enter(self):
        """
        Connect to the SocketIO server when the page is entered.
        """
        if not self.sio.connected:
            server_url = self.controller.server_url.strip()
            self.log(f"Connecting to SocketIO server at {server_url}...")
            try:
                self.sio.connect(
                    server_url,
                    wait=True,
                    transports=["websocket"],
                    socketio_path="socket.io"
                )
            except Exception as e:
                self.log(f"Error connecting to SocketIO server:\n{e}")

    def poll_queue(self):
        """Poll the thread-safe queue for new messages."""
        try:
            while True:
                text = self.msg_queue.get_nowait()
                self.update_chat_signal.emit(text)
        except queue.Empty:
            pass

    def log(self, text):
        """Log a message to the chat display."""
        self.update_chat_signal.emit(text + "\n")

    def update_chat_display(self, text):
        """
        Update the chat display with new text, handling line breaks properly.
        """
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # If text starts with "DM:" or "Player", add spacing
        if text.strip().startswith(("DM:", "Player")):
            if not self.chat_display.toPlainText().endswith("\n\n"):
                cursor.insertText("\n")

        # Replace "You:" with the player's character name if it appears
        if text.strip().startswith("You:"):
            base_url = self.controller.server_url.rstrip("/")
            player_url = f"{base_url}/api/players/{self.controller.player_id}"
            try:
                r = requests.get(player_url, timeout=5)
                r.raise_for_status()
                player_info = r.json()
                char_name = player_info.get('character_name', 'Player')
                text = text.replace("You:", f"{char_name}:")
            except Exception:
                text = text.replace("You:", "Player:")

        # Merge lines but preserve spacing
        if text.strip():
            cleaned_text = " ".join(text.splitlines())
            cursor.insertText(cleaned_text)

        # Insert an extra newline if not streaming or if punctuation ended
        if not self.is_streaming or text.strip().endswith((".", "!", "?")):
            if not self.chat_display.toPlainText().endswith("\n"):
                cursor.insertText("\n")

        # Auto-scroll if near bottom
        scrollbar = self.chat_display.verticalScrollBar()
        should_scroll = scrollbar.value() >= scrollbar.maximum() - 4
        if should_scroll:
            scrollbar.setValue(scrollbar.maximum())
            self.chat_display.setTextCursor(cursor)
            self.chat_display.ensureCursorVisible()

    def send_message(self):
        """Send a message to the server and display it locally."""
        msg = self.input_line.text().strip()
        if not msg:
            return

        self.input_line.clear()

        # Get local character name
        char_name = "Unknown Player"
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/players/{self.controller.player_id}"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            char_name = data.get("character_name", "Unknown Player")
        except Exception:
            pass

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
        """End the current session."""
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
            self.controller.session_id = None
        except Exception as e:
            self.msg_queue.put(f"Error ending session:\n{e}")

    def roll_die(self):
        """Roll a die and display the result."""
        die_type = self.dice_combo.currentText()
        if not die_type.startswith("d"):
            return
        max_val = int(die_type[1:])
        result = random.randint(1, max_val)
        self.label_roll_result.setText(str(result))
        emoji = random.choice(self.dice_emojis)
        self.msg_queue.put(f"{emoji} Roll {die_type}: {result}")

    def closeEvent(self, event: QtGui.QCloseEvent):
        """Clean up SocketIO on close if needed."""
        if self.sio and self.sio.connected:
            self.sio.disconnect()
        super().closeEvent(event)
