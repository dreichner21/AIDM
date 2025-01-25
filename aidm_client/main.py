import sys
from PySide6 import QtWidgets
from .app import AIDMWizardApp

def main():
    """
    Main entry point for the AI-DM application.
    Instantiates QApplication, creates AIDMWizardApp, and starts the event loop.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = AIDMWizardApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
