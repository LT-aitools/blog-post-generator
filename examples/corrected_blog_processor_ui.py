import sys
import os
import webbrowser
from pathlib import Path
from datetime import datetime

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QTextEdit, QProgressBar, QTabWidget, QSplitter,
                             QScrollArea, QGridLayout, QFrame, QToolButton)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView  # Make sure to install PyQt6-WebEngine
from src.blog_processor import BlogProcessor


class HtmlViewer(QWidget):
    """Widget for displaying HTML content."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Web view for rendering HTML
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        # Button to open in browser
        open_button = QPushButton("Open in Browser")
        open_button.clicked.connect(self.open_in_browser)
        self.layout.addWidget(open_button)

        self.html_path = None

    def set_html(self, html_content, base_url=None):
        """Set HTML content to display."""
        self.web_view.setHtml(html_content, base_url)

    def set_html_file(self, html_path):
        """Load HTML from file."""
        self.html_path = html_path
        base_url = QUrl.fromLocalFile(str(Path(html_path).parent))

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                self.set_html(html_content, base_url)
        except Exception as e:
            print(f"Error loading HTML: {str(e)}")

    def open_in_browser(self):
        """Open the HTML file in the default web browser."""
        if self.html_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.html_path))


class MediaGallery(QWidget):
    """Widget for displaying media files in a grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Scroll area to contain the grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # Container widget for the grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.scroll_area.setWidget(self.container)

        # Media file paths
        self.media_files = []

    def load_media_directory(self, media_dir):
        """Load media files from directory."""
        # Clear existing items
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        # Find image files
        self.media_files = []
        for root, dirs, files in os.walk(media_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.media_files.append(os.path.join(root, file))

        # Add media files to grid
        cols = 3  # Number of columns
        for i, media_path in enumerate(self.media_files):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame_layout = QVBoxLayout(frame)

            # Image
            pixmap = QPixmap(media_path)
            if not pixmap.isNull():
                # Scale pixmap to reasonable size
                pixmap = pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio)
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                frame_layout.addWidget(img_label)

            # Filename label
            filename_label = QLabel(os.path.basename(media_path))
            filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            filename_label.setWordWrap(True)
            frame_layout.addWidget(filename_label)

            # Open button
            open_button = QPushButton("Open")
            open_button.clicked.connect(lambda checked, path=media_path:
                                        QDesktopServices.openUrl(QUrl.fromLocalFile(path)))
            frame_layout.addWidget(open_button)

            # Add to grid
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(frame, row, col)


class BlogProcessorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blog Media Processor")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Initialize file paths
        self.doc_path = None
        self.video_path = None

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create file selection area
        self._create_file_selection(main_layout)

        # Create splitter for log and preview areas
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter, 1)

        # Add log area to top of splitter
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        self._create_log_area(log_layout)
        splitter.addWidget(log_widget)

        # Add tab widget for previews to bottom of splitter
        self.preview_tabs = QTabWidget()
        splitter.addWidget(self.preview_tabs)

        # Add HTML viewer tab
        self.html_viewer = HtmlViewer()
        self.preview_tabs.addTab(self.html_viewer, "HTML Preview")

        # Add media gallery tab
        self.media_gallery = MediaGallery()
        self.preview_tabs.addTab(self.media_gallery, "Media Files")

        # Create process button
        self._create_process_button(main_layout)

        # Show initial instructions
        self.log_output.append("Welcome to Blog Media Processor!")
        self.log_output.append("Please select your Word document and video file to begin.")

        # Set initial splitter sizes (1/3 for log, 2/3 for preview)
        splitter.setSizes([200, 400])

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
        self.log_output.setMinimumHeight(100)
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
        self.process_button.setMinimumHeight(40)  # Make button larger
        self.process_button.setStyleSheet("font-weight: bold;")
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

                # Update preview tabs with new content
                self.html_viewer.set_html_file(result.html_path)
                self.media_gallery.load_media_directory(result.media_folder)

                # Switch to HTML preview tab
                self.preview_tabs.setCurrentIndex(0)

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
            # Print stack trace to console for debugging
            import traceback
            traceback.print_exc()

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