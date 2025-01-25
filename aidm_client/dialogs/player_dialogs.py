import requests

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)

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

        self.name_edit = QLineEdit(self)
        self.char_name_edit = QLineEdit(self)
        self.race_edit = QLineEdit(self)
        self.class_edit = QLineEdit(self)
        self.level_edit = QLineEdit(self)
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
