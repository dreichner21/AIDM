import requests

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)

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
        url = f"{base_url}/api/campaigns"
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
