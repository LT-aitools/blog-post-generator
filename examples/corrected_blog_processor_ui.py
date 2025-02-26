import sys
import os
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QTextEdit, QProgressBar, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon
from src.blog_processor import BlogProcessor


class StyledButton(QPushButton):
    """Custom styled button with modern appearance"""

    def __init__(self, text, primary=False, icon=None):
        super().__init__(text)
        self.setMinimumHeight(36)
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4a86e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #3a76d8;
                }
                QPushButton:pressed {
                    background-color: #2a66c8;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #888888;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)

        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(18, 18))


class FileSelectionCard(QFrame):
    """Card for file selection with icon and status"""

    def __init__(self, title, icon_path=None, select_text="Select File"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)

        # Header with title
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # File status
        status_layout = QHBoxLayout()
        self.status_icon = QLabel("📄")  # Using emoji as placeholder
        status_layout.addWidget(self.status_icon)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #777777;")
        status_layout.addWidget(self.file_label, 1)

        self.select_button = StyledButton(select_text)
        status_layout.addWidget(self.select_button)

        layout.addLayout(status_layout)

    def set_file(self, file_path):
        if file_path:
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: #333333; font-weight: bold;")
            self.status_icon = QLabel("✅")  # Change to checkmark
        else:
            self.file_label.setText("No file selected")
            self.file_label.setStyleSheet("color: #777777;")


class BlogProcessorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blog Media Processor")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
        """)

        # Initialize file paths
        self.doc_path = None
        self.video_path = None

        # Processing state
        self.is_processing = False

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Create header
        header = QLabel("Blog Content Processor")
        header_font = header.font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        # Description
        description = QLabel("Extract media from blog posts and create HTML pages")
        description.setStyleSheet("color: #666666;")
        main_layout.addWidget(description)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)

        # Create file selection area
        main_layout.addWidget(QLabel("1. Select your files"))
        file_selection_layout = QVBoxLayout()
        file_selection_layout.setSpacing(12)

        # Document selection card
        self.doc_card = FileSelectionCard("Blog Document (DOCX)", select_text="Select Document")
        self.doc_card.select_button.clicked.connect(self._select_document)
        file_selection_layout.addWidget(self.doc_card)

        # Video selection card
        self.video_card = FileSelectionCard("Video File", select_text="Select Video")
        self.video_card.select_button.clicked.connect(self._select_video)
        file_selection_layout.addWidget(self.video_card)

        main_layout.addLayout(file_selection_layout)

        # Add processing section
        main_layout.addWidget(QLabel("2. Process your blog"))

        # Process button
        self.process_button = StyledButton("Process Blog", primary=True)
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._process_blog)
        main_layout.addWidget(self.process_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Create log output area with scroll
        main_layout.addWidget(QLabel("3. Results"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(180)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-family: monospace;
            }
        """)
        log_layout.addWidget(self.log_output)

        scroll.setWidget(log_container)
        main_layout.addWidget(scroll)

        # Show initial instructions
        self.log_output.append("Welcome to Blog Media Processor!")
        self.log_output.append("Please select your Word document and video file to begin.")

    def _select_document(self):
        """Handle document selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Blog Document",
            os.path.expanduser("~/Desktop"),  # Start in Desktop
            "Word Documents (*.docx);;All Files (*.*)"
        )

        if file_path:
            self.doc_path = file_path
            self.doc_card.set_file(file_path)
            self._check_ready()
            self.log_output.append(f"Selected document: {os.path.basename(file_path)}")

    def _select_video(self):
        """Handle video selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            os.path.expanduser("~/Desktop"),  # Start in Desktop
            "Video Files (*.mp4 *.avi *.mov);;All Files (*.*)"
        )

        if file_path:
            self.video_path = file_path
            self.video_card.set_file(file_path)
            self._check_ready()
            self.log_output.append(f"Selected video: {os.path.basename(file_path)}")

    def _check_ready(self):
        """Check if both files are selected and enable/disable process button."""
        self.process_button.setEnabled(bool(self.doc_path and self.video_path) and not self.is_processing)

    def _process_blog(self):
        """Process the blog with selected files."""
        # Prevent multiple processing attempts
        if self.is_processing:
            return

        self.is_processing = True

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.process_button.setEnabled(False)
            self.log_output.append("\nProcessing blog...")

            # Change cursor to waiting
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # Use a timer to allow the UI to update before starting processing
            QTimer.singleShot(100, self._execute_processing)

        except Exception as e:
            self._reset_ui()
            self.log_output.append(f"\n❌ Error setting up processing: {str(e)}")

    def _execute_processing(self):
        """Execute the actual blog processing (called by timer)"""
        try:
            # Initialize processor
            processor = BlogProcessor(output_base_dir="processed_blogs")

            # Process blog
            result = processor.process_blog(self.doc_path, self.video_path)

            # Handle result
            if result.success:
                self.log_output.append("\n✅ Blog processing completed successfully!")
                self.log_output.append(f"\nOutputs created:")
                self.log_output.append(f"HTML file: {result.html_path}")
                self.log_output.append(f"Media folder: {result.media_folder}")

                if result.warnings:
                    self.log_output.append("\n⚠️ Warnings:")
                    for warning in result.warnings:
                        self.log_output.append(f"  - {warning}")

                # Try to open output folder
                try:
                    if sys.platform == "darwin":  # macOS
                        os.system(f'open "{os.path.dirname(result.html_path)}"')
                    elif sys.platform == "win32":  # Windows
                        os.startfile(os.path.dirname(result.html_path))
                    self.log_output.append("\nOpened output folder!")
                except Exception:
                    self.log_output.append(f"\nOutput folder is at: {os.path.dirname(result.html_path)}")
            else:
                self.log_output.append("\n❌ Blog processing failed!")
                for error in result.errors:
                    self.log_output.append(f"Error: {error}")

        except Exception as e:
            self.log_output.append(f"\n❌ Error: {str(e)}")

        finally:
            # Reset UI using a small delay to ensure everything completes
            QTimer.singleShot(100, self._reset_ui)

    def _reset_ui(self):
        """Reset the UI after processing completes"""
        self.is_processing = False
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(bool(self.doc_path and self.video_path))
        QApplication.restoreOverrideCursor()

        # Ensure we process any pending events
        QApplication.processEvents()


def main():
    app = QApplication(sys.argv)

    # Apply global stylesheet
    app.setStyle("Fusion")

    window = BlogProcessorUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()