import requests

from PySide6.QtWidgets import (
    QComboBox, QPushButton, QMessageBox, QLabel, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt

from ..constants import LABEL_FONT, BUTTON_FONT, INPUT_FONT
from .base_page import BasePage
from ..dialogs.player_dialogs import PlayerCreateDialog

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
        if dialog.exec() == dialog.Accepted:
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
