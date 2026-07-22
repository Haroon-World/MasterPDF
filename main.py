# main.py

import sys
import multiprocessing

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

# Import the GUI class from our newly created gui.py
from gui import PDFMasterGUI

def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Configure Dark Mode Palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor("#0F172A"))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#F8FAFC"))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor("#1E293B"))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor("#F8FAFC"))
    app.setPalette(dark_palette)
    
    # Initialize and show the main window
    window = PDFMasterGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    multiprocessing.freeze_support()
    run_app()