import requests

from PySide6.QtWidgets import (
    QLineEdit, QPushButton, QMessageBox, QLabel, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt

from ..constants import LABEL_FONT, BUTTON_FONT, INPUT_FONT
from .base_page import BasePage

class ServerPage(BasePage):
    """
    Page to connect to the AI-DM server.
    """
    def __init__(self, parent):
        super().__init__(parent, title="1. Connect to AI-DM Server")

        self.server_edit = QLineEdit(self)
        self.server_edit.setFont(INPUT_FONT)
        self.server_edit.setText("http://localhost:5000")  # Default server URL

        self.button_next = QPushButton("Next")
        self.button_next.setFont(BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

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
