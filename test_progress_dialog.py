#!/usr/bin/env python3
"""
Test script for ProgressDialogModern improvements.
Tests the new features: theme integration, indeterminate progress, ESC cancellation.
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

# Add the plugin path to sys.path
sys.path.insert(0, r"c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code")

from widgets.ProgressDialogModern import ProgressDialogModern

class WorkerThread(QThread):
    """Worker thread for testing progress dialog."""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog

    def run(self):
        """Simulate work with progress updates."""
        total_steps = 100

        for i in range(total_steps + 1):
            if self.dialog.wasCanceled():
                self.status.emit("Operation cancelled!")
                return

            self.progress.emit(i)
            self.status.emit(f"Processing step {i}/{total_steps}")

            # Simulate some work
            time.sleep(0.05)

        self.status.emit("Operation completed successfully!")
        self.finished.emit()

class TestWindow(QMainWindow):
    """Test window for ProgressDialogModern."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProgressDialogModern Test")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create test buttons
        self.btn_determinate = QPushButton("Test Determinate Progress")
        self.btn_determinate.clicked.connect(self.test_determinate_progress)

        self.btn_indeterminate = QPushButton("Test Indeterminate Progress")
        self.btn_indeterminate.clicked.connect(self.test_indeterminate_progress)

        layout.addWidget(self.btn_determinate)
        layout.addWidget(self.btn_indeterminate)

        self.progress_dialog = None

    def test_determinate_progress(self):
        """Test determinate progress."""
        self.progress_dialog = ProgressDialogModern(self)
        self.progress_dialog.setTitle("Test Determinate Progress")
        self.progress_dialog.setMaximum(100)

        # Start worker thread
        self.worker = WorkerThread(self.progress_dialog)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.status.connect(self.progress_dialog.setLabelText)
        self.worker.finished.connect(self.progress_dialog.accept)
        self.worker.start()

        result = self.progress_dialog.exec_()
        print(f"Dialog result: {result}")

    def test_indeterminate_progress(self):
        """Test indeterminate progress."""
        self.progress_dialog = ProgressDialogModern(self)
        self.progress_dialog.setTitle("Test Indeterminate Progress")
        self.progress_dialog.setMaximum(0)  # Indeterminate

        # Simulate indeterminate work
        self.progress_dialog.setLabelText("Working on unknown task...")

        # Close after 3 seconds
        QTimer = self.progress_dialog.timer if hasattr(self.progress_dialog, 'timer') else None
        if not QTimer:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, self.progress_dialog.accept)

        result = self.progress_dialog.exec_()
        print(f"Indeterminate dialog result: {result}")

def main():
    """Main test function."""
    app = QApplication(sys.argv)

    # Create test window
    window = TestWindow()
    window.show()

    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
