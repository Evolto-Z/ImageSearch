from PyQt6.QtWidgets import QApplication
from ui import ImageSearchUI
import sys


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageSearchUI()
    sys.exit(app.exec())
