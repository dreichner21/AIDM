from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

from ..constants import HEADER_FONT

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
