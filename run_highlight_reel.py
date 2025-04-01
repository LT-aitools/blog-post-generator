import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from highlight_reel_maker.highlight_reel_ui import main

if __name__ == "__main__":
    main() 