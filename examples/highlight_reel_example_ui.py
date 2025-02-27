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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.highlight_reel_extractor import extract_segments_from_text, create_highlight_reel


class WorkerThread(QThread):
    """Worker thread for creating highlight reels without freezing the UI."""
    update_progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, video_path, content, output_dir):
        super().__init__()
        self.video_path = video_path
        self.content = content
        self.output_dir = output_dir

    def run(self):
        try:
            # Extract segments from content
            self.update_progress.emit("Analyzing content for video segments...")
            segments = extract_segments_from_text(self.content)

            if not segments:
                self.update_progress.emit("No valid segments found in the content.")
                self.finished.emit(False, "No valid segments found.")
                return

            self.update_progress.emit(f"Found {len(segments)} segments to extract.")

            # Create output filename
            video_filename = os.path.splitext(os.path.basename(self.video_path))[0]
            output_filename = f"{video_filename}_highlight_reel.mp4"
            output_path = os.path.join(self.output_dir, output_filename)

            # Create highlight reel
            self.update_progress.emit("Creating highlight reel (this may take a while)...")
            output = create_highlight_reel(self.video_path, segments, output_path)

            self.update_progress.emit(f"Highlight reel created successfully!")
            self.finished.emit(True, output)

        except Exception as e:
            self.update_progress.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))


class HighlightReelUI(QMainWindow):
    """UI for creating highlight reels from content specifications."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Highlight Reel Creator")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.video_path = None

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add header
        header = QLabel("Highlight Reel Creator")
        header_font = header.font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        description = QLabel("Create a highlight reel by specifying video segments")
        main_layout.addWidget(description)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Video selection section
        main_layout.addWidget(QLabel("1. Select Source Video"))

        video_layout = QHBoxLayout()
        self.video_label = QLabel("No video selected")
        video_layout.addWidget(self.video_label)

        self.select_video_button = QPushButton("Select Video")
        self.select_video_button.clicked.connect(self.select_video)
        video_layout.addWidget(self.select_video_button)

        main_layout.addLayout(video_layout)

        # Content specification section
        main_layout.addWidget(QLabel("2. Specify Highlight Reel Content"))
        main_layout.addWidget(QLabel("Enter segment specifications in the format:"))
        main_layout.addWidget(
            QLabel("#### Segment Title (duration in minutes)\nSTARTING TIMESTAMP: HH:MM:SS\n- Content description"))

        self.content_editor = QTextEdit()
        self.content_editor.setMinimumHeight(200)
        self.content_editor.setPlaceholderText("""Example:
#### Segment 1: Introduction (2 minutes)
STARTING TIMESTAMP: 00:01:30
- Opening remarks
- Overview of topics

#### Segment 2: Main Discussion (3 minutes)
STARTING TIMESTAMP: 00:15:45
- Key points
- Examples
""")
        # Connect text changed signal to update button state
        self.content_editor.textChanged.connect(self._update_create_button)
        main_layout.addWidget(self.content_editor)

        # Output directory section
        main_layout.addWidget(QLabel("3. Select Output Directory"))

        output_layout = QHBoxLayout()
        self.output_label = QLabel(os.path.join(os.getcwd(), "highlight_reels"))
        output_layout.addWidget(self.output_label)

        self.select_output_button = QPushButton("Select Directory")
        self.select_output_button.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.select_output_button)

        main_layout.addLayout(output_layout)

        # Create button
        self.create_button = QPushButton("Create Highlight Reel")
        self.create_button.setMinimumHeight(40)
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self.create_highlight_reel)
        main_layout.addWidget(self.create_button)

        # Progress section
        self.progress_label = QLabel("Ready")
        main_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        main_layout.addWidget(self.log_output)

        # Initialize
        self._update_create_button()

    def select_video(self):
        """Handle video selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            os.path.expanduser("~/Desktop"),
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )

        if file_path:
            self.video_path = file_path
            self.video_label.setText(file_path)
            self.log_output.append(f"Selected video: {file_path}")
            self._update_create_button()

    def select_output_dir(self):
        """Handle output directory selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.expanduser("~/Desktop")
        )

        if dir_path:
            self.output_label.setText(dir_path)
            self.log_output.append(f"Output directory: {dir_path}")

    def _update_create_button(self):
        """Update the state of the create button based on inputs."""
        has_video = self.video_path is not None
        has_content = len(self.content_editor.toPlainText().strip()) > 0

        # Always enable the button if we have a video and any content
        self.create_button.setEnabled(has_video and has_content)

        # Log the state to help with debugging
        print(f"Button state update - Has video: {has_video}, Has content: {has_content}")
        self.log_output.append(f"Ready to create highlight reel: {has_video and has_content}")

    def create_highlight_reel(self):
        """Start the highlight reel creation process."""
        try:
            self.log_output.append("Starting highlight reel creation...")

            content = self.content_editor.toPlainText()
            output_dir = self.output_label.text()

            # Basic validation with better error messages
            if not self.video_path:
                self.log_output.append("Error: No video path selected.")
                return

            if not os.path.exists(self.video_path):
                self.log_output.append(f"Error: Video file not found at {self.video_path}")
                return

            if not content.strip():
                self.log_output.append("Error: No segment content specified.")
                return

            # Validate segments can be extracted
            segments = extract_segments_from_text(content)
            if not segments:
                self.log_output.append(
                    "Error: Could not extract any valid segments from the text. Please check your format.")
                self.log_output.append(
                    "Each segment needs a title with '#' heading marks, duration in parentheses, and a STARTING TIMESTAMP line.")
                return

            # Log the segments that were found to help debugging
            self.log_output.append(f"Found {len(segments)} segments to include in the highlight reel:")
            for i, segment in enumerate(segments):
                self.log_output.append(
                    f"  {i + 1}. {segment.title} - Start: {segment.start_time}s, Duration: {segment.duration}s")

            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Show progress
            self.progress_bar.setVisible(True)
            self.create_button.setEnabled(False)
            self.progress_label.setText("Processing...")

            # Start worker thread
            self.worker = WorkerThread(self.video_path, content, output_dir)
            self.worker.update_progress.connect(self.update_progress)
            self.worker.finished.connect(self.process_finished)
            self.worker.start()

        except Exception as e:
            self.log_output.append(f"Critical error: {str(e)}")
            import traceback
            self.log_output.append(traceback.format_exc())

    def update_progress(self, message):
        """Update progress message."""
        self.log_output.append(message)
        self.progress_label.setText(message)

        # Scroll to bottom of log
        scroll_bar = self.log_output.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def process_finished(self, success, result):
        """Handle completion of the worker thread."""
        self.progress_bar.setVisible(False)
        self.create_button.setEnabled(True)

        if success:
            self.progress_label.setText("Completed successfully!")
            self.log_output.append(f"Highlight reel saved to: {result}")

            # Try to open the output folder
            try:
                if sys.platform == "darwin":  # macOS
                    os.system(f'open "{os.path.dirname(result)}"')
                elif sys.platform == "win32":  # Windows
                    os.startfile(os.path.dirname(result))
            except Exception:
                pass
        else:
            self.progress_label.setText("Failed")
            self.log_output.append(f"Error: {result}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = HighlightReelUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()