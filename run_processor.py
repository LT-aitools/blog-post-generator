import sys
from PyQt6.QtWidgets import QApplication
from examples.corrected_blog_processor_ui import BlogProcessorUI

def main():
    app = QApplication(sys.argv)
    window = BlogProcessorUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 