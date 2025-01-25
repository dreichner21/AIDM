import requests

from PySide6.QtWidgets import (
    QComboBox, QPushButton, QMessageBox, QLabel, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt

from ..constants import LABEL_FONT, BUTTON_FONT, INPUT_FONT
from .base_page import BasePage
from ..dialogs.campaign_dialogs import CampaignCreateDialog

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
        url = f"{base_url}/api/campaigns"
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
        if dialog.exec() == dialog.Accepted:
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
        c_url = f"{base_url}/api/campaigns/{self.controller.campaign_id}"
        try:
            r = requests.get(c_url, timeout=5)
            r.raise_for_status()
            data = r.json()
            self.controller.world_id = data.get("world_id", 1)
        except:
            self.controller.world_id = 1

        self.controller.show_frame("SessionPage")
