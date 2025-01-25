import requests

from PySide6.QtWidgets import (
    QComboBox, QPushButton, QMessageBox, QLabel, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt

from ..constants import LABEL_FONT, BUTTON_FONT, INPUT_FONT
from .base_page import BasePage

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
        url = f"{base_url}/api/sessions/start"
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
