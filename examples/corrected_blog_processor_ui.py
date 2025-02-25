import sys
import os
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QTextEdit, QProgressBar)
from PyQt6.QtCore import Qt
from src.blog_processor import BlogProcessor


class BlogProcessorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blog Media Processor")
        self.setMinimumWidth(600)

        # Initialize file paths
        self.doc_path = None
        self.video_path = None

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create file selection area
        self._create_file_selection(layout)

        # Create log output area
        self._create_log_area(layout)

        # Create process button
        self._create_process_button(layout)

        # Show initial instructions
        self.log_output.append("Welcome to Blog Media Processor!")
        self.log_output.append("Please select your Word document and video file to begin.")

    def _create_file_selection(self, parent_layout):
        """Create the file selection buttons and labels."""
        # Document selection
        doc_layout = QHBoxLayout()
        self.doc_label = QLabel("No document selected")
        doc_button = QPushButton("Select Document")
        doc_button.clicked.connect(self._select_document)
        doc_layout.addWidget(self.doc_label)
        doc_layout.addWidget(doc_button)
        parent_layout.addLayout(doc_layout)

        # Video selection
        video_layout = QHBoxLayout()
        self.video_label = QLabel("No video selected")
        video_button = QPushButton("Select Video")
        video_button.clicked.connect(self._select_video)
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(video_button)
        parent_layout.addLayout(video_layout)

    def _create_log_area(self, parent_layout):
        """Create the log output area."""
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        parent_layout.addWidget(self.log_output)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)

    def _create_process_button(self, parent_layout):
        """Create the process button."""
        self.process_button = QPushButton("Process Blog")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._process_blog)
        parent_layout.addWidget(self.process_button)

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
            self.doc_label.setText(os.path.basename(file_path))
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
            self.video_label.setText(os.path.basename(file_path))
            self._check_ready()
            self.log_output.append(f"Selected video: {os.path.basename(file_path)}")

    def _check_ready(self):
        """Check if both files are selected and enable/disable process button."""
        self.process_button.setEnabled(bool(self.doc_path and self.video_path))

    def _process_blog(self):
        """Process the blog with selected files."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.process_button.setEnabled(False)
            self.log_output.append("\nProcessing blog...")

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
                except:
                    self.log_output.append(f"\nOutput folder is at: {os.path.dirname(result.html_path)}")
            else:
                self.log_output.append("\n❌ Blog processing failed!")
                for error in result.errors:
                    self.log_output.append(f"Error: {error}")

        except Exception as e:
            self.log_output.append(f"\n❌ Error: {str(e)}")

        finally:
            self.progress_bar.setVisible(False)
            self.process_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = BlogProcessorUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()