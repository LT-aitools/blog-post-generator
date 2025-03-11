import sys
import os
import json
import subprocess
from datetime import timedelta
from pathlib import Path

# Add project root to path - this is crucial for imports to work correctly
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import the highlight reel processor - note we're using src. prefix
from src.titled_highlight_reel import HighlightSegment, create_titled_highlight_reel

# Try importing PyQt6, provide helpful error if not installed
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                                 QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                                 QTextEdit, QProgressBar, QFrame, QScrollArea,
                                 QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
                                 QHeaderView, QMessageBox, QDialog, QFormLayout)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt6.QtGui import QFont, QIcon
except ImportError:
    print("Error: PyQt6 is not installed. Please install it with:")
    print("pip install PyQt6")
    sys.exit(1)


class StyledButton(QPushButton):
    """Custom styled button with modern appearance"""

    def __init__(self, text, primary=False, icon=None):
        super().__init__(text)
        self.setMinimumHeight(36)
        font = self.font()
        font.setPointSize(10)
        font.setBold(True)
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


class SegmentDialog(QDialog):
    """Dialog for adding or editing a segment"""

    def __init__(self, parent=None, segment=None):
        super().__init__(parent)
        self.setWindowTitle("Segment Details")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Title field
        self.title_input = QLineEdit()
        if segment:
            self.title_input.setText(segment.title)
        layout.addRow("Title:", self.title_input)

        # Start time field
        self.start_time_input = QLineEdit()
        if segment:
            hours = segment.start_time // 3600
            minutes = (segment.start_time % 3600) // 60
            seconds = segment.start_time % 60
            self.start_time_input.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        layout.addRow("Start Time (HH:MM:SS):", self.start_time_input)

        # Duration field
        self.duration_input = QLineEdit()
        if segment:
            minutes = segment.duration // 60
            seconds = segment.duration % 60
            self.duration_input.setText(f"{minutes:02d}:{seconds:02d}")
        layout.addRow("Duration (MM:SS):", self.duration_input)

        # Help text
        help_text = QLabel("Format examples: '01:30:45' for 1h 30m 45s or '05:30' for 5m 30s")
        help_text.setStyleSheet("color: #777777; font-style: italic;")
        layout.addRow("", help_text)

        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = StyledButton("Save", primary=True)
        self.save_button.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addRow("", button_layout)

    def get_segment(self):
        """Get the HighlightSegment from the dialog data"""
        try:
            title = self.title_input.text().strip()
            if not title:
                raise ValueError("Title cannot be empty")

            # Parse start time
            start_time_parts = self.start_time_input.text().strip().split(':')
            if len(start_time_parts) == 3:
                hours, minutes, seconds = map(int, start_time_parts)
                start_time = hours * 3600 + minutes * 60 + seconds
            elif len(start_time_parts) == 2:
                minutes, seconds = map(int, start_time_parts)
                start_time = minutes * 60 + seconds
            else:
                raise ValueError("Invalid start time format")

            # Parse duration
            duration_parts = self.duration_input.text().strip().split(':')
            if len(duration_parts) == 2:
                minutes, seconds = map(int, duration_parts)
                duration = minutes * 60 + seconds
            elif len(duration_parts) == 3:
                hours, minutes, seconds = map(int, duration_parts)
                duration = hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError("Invalid duration format")

            return HighlightSegment(
                title=title,
                start_time=start_time,
                duration=duration
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return None


class WorkerThread(QThread):
    """Worker thread for creating highlight reels without freezing the UI."""
    update_progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, video_path, segments, output_dir, title_duration):
        super().__init__()
        self.video_path = video_path
        self.segments = segments
        self.output_dir = output_dir
        self.title_duration = title_duration

    def run(self):
        try:
            self.update_progress.emit("Creating highlight reel...")

            # Log the segments
            for i, segment in enumerate(self.segments):
                total_seconds = segment.start_time
                h = total_seconds // 3600
                m = (total_seconds % 3600) // 60
                s = total_seconds % 60

                self.update_progress.emit(
                    f"Segment {i + 1}: {segment.title}\n"
                    f"  Start: {h:02d}:{m:02d}:{s:02d}\n"
                    f"  Duration: {segment.duration // 60:02d}:{segment.duration % 60:02d}"
                )

            output_path = create_titled_highlight_reel(
                self.video_path,
                self.segments,
                self.output_dir,
                self.title_duration
            )

            self.update_progress.emit(f"Highlight reel created successfully!")
            self.finished.emit(True, output_path)

        except Exception as e:
            self.update_progress.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))


class HighlightReelUI(QMainWindow):
    """UI for creating highlight reels with title cards"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Titled Highlight Reel Creator")
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
        """)
        self.video_path = None
        self.output_dir = os.path.join(os.getcwd(), "highlight_reels")
        self.segments = []
        self.is_processing = False

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Create header
        header = QLabel("Titled Highlight Reel Creator")
        header_font = header.font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        # Description
        description = QLabel("Create a highlight reel with title cards before each segment")
        description.setStyleSheet("color: #666666;")
        main_layout.addWidget(description)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)

        # Create file selection area
        section_label = QLabel("1. Select your video")
        section_font = section_label.font()
        section_font.setBold(True)
        section_font.setPointSize(12)
        section_label.setFont(section_font)
        main_layout.addWidget(section_label)

        # Video selection card
        self.video_card = FileSelectionCard("Video File", select_text="Select Video")
        self.video_card.select_button.clicked.connect(self._select_video)
        main_layout.addWidget(self.video_card)

        # Output directory
        self.output_card = FileSelectionCard("Output Directory", select_text="Select Folder")
        self.output_card.file_label.setText(self.output_dir)
        self.output_card.select_button.clicked.connect(self._select_output_dir)
        main_layout.addWidget(self.output_card)

        # Title duration
        title_duration_layout = QHBoxLayout()
        title_duration_label = QLabel("Title Card Duration (seconds):")
        self.title_duration_input = QSpinBox()
        self.title_duration_input.setMinimum(1)
        self.title_duration_input.setMaximum(10)
        self.title_duration_input.setValue(2)
        self.title_duration_input.setFixedWidth(80)
        title_duration_layout.addWidget(title_duration_label)
        title_duration_layout.addWidget(self.title_duration_input)
        title_duration_layout.addStretch()
        main_layout.addLayout(title_duration_layout)

        # Segment section
        section_label = QLabel("2. Define your segments")
        section_label.setFont(section_font)
        main_layout.addWidget(section_label)

        # Segments table
        segments_frame = QFrame()
        segments_frame.setFrameShape(QFrame.Shape.StyledPanel)
        segments_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        segments_layout = QVBoxLayout(segments_frame)

        # Table
        self.segments_table = QTableWidget(0, 3)
        self.segments_table.setHorizontalHeaderLabels(["Title", "Start Time", "Duration"])
        self.segments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.segments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.segments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        segments_layout.addWidget(self.segments_table)

        # Buttons for segments
        segment_buttons_layout = QHBoxLayout()
        self.add_segment_button = StyledButton("Add Segment")
        self.add_segment_button.clicked.connect(self._add_segment)

        self.edit_segment_button = StyledButton("Edit Segment")
        self.edit_segment_button.clicked.connect(self._edit_segment)

        self.remove_segment_button = StyledButton("Remove Segment")
        self.remove_segment_button.clicked.connect(self._remove_segment)

        segment_buttons_layout.addWidget(self.add_segment_button)
        segment_buttons_layout.addWidget(self.edit_segment_button)
        segment_buttons_layout.addWidget(self.remove_segment_button)
        segments_layout.addLayout(segment_buttons_layout)

        # Import/Export buttons
        io_buttons_layout = QHBoxLayout()
        self.import_button = StyledButton("Import JSON")
        self.import_button.clicked.connect(self._import_segments)

        self.export_button = StyledButton("Export JSON")
        self.export_button.clicked.connect(self._export_segments)

        io_buttons_layout.addWidget(self.import_button)
        io_buttons_layout.addWidget(self.export_button)
        segments_layout.addLayout(io_buttons_layout)

        main_layout.addWidget(segments_frame)

        # Process button
        section_label = QLabel("3. Create highlight reel")
        section_label.setFont(section_font)
        main_layout.addWidget(section_label)

        self.process_button = StyledButton("Create Highlight Reel", primary=True)
        self.process_button.setMinimumHeight(50)
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._process_highlight_reel)
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

        # Log output
        section_label = QLabel("4. Results")
        section_label.setFont(section_font)
        main_layout.addWidget(section_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-family: monospace;
            }
        """)
        main_layout.addWidget(self.log_output)

        # Show initial instructions
        self.log_output.append("Welcome to the Titled Highlight Reel Creator!")
        self.log_output.append("Select your video file and define segments to begin.")
        self.log_output.append("Each segment will begin with its title card, displayed for the specified duration.")

    def _select_video(self):
        """Handle video selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            os.path.expanduser("~/Desktop"),
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )

        if file_path:
            self.video_path = file_path
            self.video_card.set_file(file_path)
            self._check_ready()
            self.log_output.append(f"Selected video: {os.path.basename(file_path)}")

    def _select_output_dir(self):
        """Handle output directory selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.expanduser("~/Desktop")
        )

        if dir_path:
            self.output_dir = dir_path
            self.output_card.set_file(dir_path)
            self.log_output.append(f"Output directory: {dir_path}")

    def _add_segment(self):
        """Add a new segment."""
        dialog = SegmentDialog(self)
        if dialog.exec():
            segment = dialog.get_segment()
            if segment:
                self.segments.append(segment)
                self._update_segments_table()
                self._check_ready()

    def _edit_segment(self):
        """Edit the selected segment."""
        selected_rows = self.segments_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a segment to edit.")
            return

        row = selected_rows[0].row()
        dialog = SegmentDialog(self, self.segments[row])
        if dialog.exec():
            segment = dialog.get_segment()
            if segment:
                self.segments[row] = segment
                self._update_segments_table()

    def _remove_segment(self):
        """Remove the selected segment."""
        selected_rows = self.segments_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a segment to remove.")
            return

        row = selected_rows[0].row()
        self.segments.pop(row)
        self._update_segments_table()
        self._check_ready()

    def _import_segments(self):
        """Import segments from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Segments from JSON",
            os.path.expanduser("~/Desktop"),
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                segments_data = json.load(f)

            # Clear existing segments
            self.segments = []

            # Add imported segments
            for segment in segments_data:
                if isinstance(segment, dict):
                    title = segment.get('title', 'Untitled')

                    # Parse start_time
                    start_time = segment.get('start_time', 0)
                    if isinstance(start_time, str):
                        parts = start_time.split(':')
                        if len(parts) == 3:
                            hours, minutes, seconds = map(int, parts)
                            start_time = hours * 3600 + minutes * 60 + seconds
                        elif len(parts) == 2:
                            minutes, seconds = map(int, parts)
                            start_time = minutes * 60 + seconds

                    # Parse duration
                    duration = segment.get('duration', 30)
                    if isinstance(duration, str):
                        parts = duration.split(':')
                        if len(parts) == 2:
                            minutes, seconds = map(int, parts)
                            duration = minutes * 60 + seconds
                        elif len(parts) == 3:
                            hours, minutes, seconds = map(int, parts)
                            duration = hours * 3600 + minutes * 60 + seconds

                    self.segments.append(HighlightSegment(
                        title=title,
                        start_time=start_time,
                        duration=duration
                    ))

            self._update_segments_table()
            self._check_ready()
            self.log_output.append(f"Imported {len(self.segments)} segments from {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing segments: {str(e)}")

    def _export_segments(self):
        """Export segments to a JSON file."""
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "There are no segments to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Segments to JSON",
            os.path.expanduser("~/Desktop"),
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            # Convert segments to dictionaries
            segments_data = []
            for segment in self.segments:
                # Format times as strings for better readability
                start_h = segment.start_time // 3600
                start_m = (segment.start_time % 3600) // 60
                start_s = segment.start_time % 60
                start_time_str = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"

                duration_m = segment.duration // 60
                duration_s = segment.duration % 60
                duration_str = f"{duration_m:02d}:{duration_s:02d}"

                segments_data.append({
                    'title': segment.title,
                    'start_time': start_time_str,
                    'duration': duration_str
                })

            with open(file_path, 'w') as f:
                json.dump(segments_data, f, indent=2)

            self.log_output.append(f"Exported {len(self.segments)} segments to {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting segments: {str(e)}")

    def _update_segments_table(self):
        """Update the segments table with current segments."""
        self.segments_table.setRowCount(0)

        for segment in self.segments:
            row = self.segments_table.rowCount()
            self.segments_table.insertRow(row)

            # Title
            self.segments_table.setItem(row, 0, QTableWidgetItem(segment.title))

            # Start Time (formatted as HH:MM:SS)
            hours = segment.start_time // 3600
            minutes = (segment.start_time % 3600) // 60
            seconds = segment.start_time % 60
            start_time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.segments_table.setItem(row, 1, QTableWidgetItem(start_time_text))

            # Duration (formatted as MM:SS)
            minutes = segment.duration // 60
            seconds = segment.duration % 60
            duration_text = f"{minutes:02d}:{seconds:02d}"
            self.segments_table.setItem(row, 2, QTableWidgetItem(duration_text))

    def _check_ready(self):
        """Check if all conditions are met to enable the process button."""
        has_video = self.video_path is not None
        has_segments = len(self.segments) > 0
        self.process_button.setEnabled(has_video and has_segments and not self.is_processing)

    def _process_highlight_reel(self):
        """Process the highlight reel."""
        if self.is_processing:
            return

        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please select a video file.")
            return

        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Please add at least one segment.")
            return

        self.is_processing = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.process_button.setEnabled(False)

        # Clear log
        self.log_output.clear()
        self.log_output.append("Starting highlight reel creation...")

        # Get title duration
        title_duration = self.title_duration_input.value()

        # Start worker thread
        self.worker = WorkerThread(
            self.video_path,
            self.segments,
            self.output_dir,
            title_duration
        )
        self.worker.update_progress.connect(self.update_progress)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

        # Change cursor to waiting
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    def update_progress(self, message):
        """Update progress message."""
        self.log_output.append(message)

        # Scroll to bottom of log
        scroll_bar = self.log_output.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def process_finished(self, success, result):
        """Handle completion of the worker thread."""
        self.is_processing = False
        self.progress_bar.setVisible(False)
        self._check_ready()
        QApplication.restoreOverrideCursor()

        if success:
            self.log_output.append("\n✅ Highlight reel created successfully!")
            self.log_output.append(f"Output saved to: {result}")

            # Ask if user wants to open the output folder
            reply = QMessageBox.question(
                self,
                "Highlight Reel Complete",
                "Highlight reel created successfully. Open containing folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if sys.platform == "darwin":  # macOS
                        os.system(f'open "{os.path.dirname(result)}"')
                    elif sys.platform == "win32":  # Windows
                        os.startfile(os.path.dirname(result))
                    else:  # Linux
                        subprocess.run(['xdg-open', os.path.dirname(result)])
                except Exception as e:
                    self.log_output.append(f"Error opening folder: {str(e)}")
        else:
            self.log_output.append("\n❌ Highlight reel creation failed!")
            self.log_output.append(f"Error: {result}")
            QMessageBox.critical(self, "Error", f"Failed to create highlight reel: {result}")


def main():
    app = QApplication(sys.argv)

    # Apply global stylesheet
    app.setStyle("Fusion")

    window = HighlightReelUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()