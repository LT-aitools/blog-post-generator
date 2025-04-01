from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTextEdit, 
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path
from .highlight_reel_processor import HighlightReelProcessor

class HighlightReelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Highlight Reel Maker")
        self.setMinimumSize(800, 600)
        
        # Initialize processor
        self.processor = HighlightReelProcessor()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Video selection
        self.video_label = QLabel("No video selected")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc;")
        layout.addWidget(self.video_label)
        
        select_video_btn = QPushButton("Select Video")
        select_video_btn.clicked.connect(self.select_video)
        layout.addWidget(select_video_btn)
        
        # Instructions input
        instructions_label = QLabel("Reel Instructions:")
        layout.addWidget(instructions_label)
        
        self.instructions_text = QTextEdit()
        self.instructions_text.setPlaceholderText("""Enter your reel instructions here. Example:
[Title] AI vs. AI: Week 6 Highlight Reel
[Segment] First Segment
[Description] Description of the segment
[CLIP timestamp="00:00:00" duration="30"]
...""")
        layout.addWidget(self.instructions_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Generate button
        generate_btn = QPushButton("Generate Highlight Reel")
        generate_btn.clicked.connect(self.generate_reel)
        layout.addWidget(generate_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Initialize video path
        self.video_path = None
        
    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.video_path = file_path
            self.video_label.setText(f"Selected: {Path(file_path).name}")
            
    def generate_reel(self):
        if not self.video_path:
            QMessageBox.warning(self, "Error", "Please select a video file first!")
            return
            
        instructions = self.instructions_text.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(self, "Error", "Please enter reel instructions!")
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Processing...")
            
            # Process the highlight reel
            output_path = self.processor.process_reel(
                self.video_path,
                instructions,
                progress_callback=self.update_progress
            )
            
            self.progress_bar.setValue(100)
            self.status_label.setText(f"Success! Output saved to: {output_path}")
            QMessageBox.information(self, "Success", "Highlight reel generated successfully!")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate highlight reel: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()

def main():
    app = QApplication(sys.argv)
    window = HighlightReelUI()
    window.show()
    sys.exit(app.exec()) 