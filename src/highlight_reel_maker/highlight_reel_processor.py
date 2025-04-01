import re
from pathlib import Path
import cv2
import numpy as np
import sys
from typing import List, Dict, Callable, Optional, Tuple
import tempfile
import os

# Add the virtual environment's site-packages to the Python path
venv_path = Path(sys.executable).parent.parent / "lib" / "python3.11" / "site-packages"
if str(venv_path) not in sys.path:
    sys.path.append(str(venv_path))

try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
except ImportError as e:
    print(f"Error importing moviepy: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    raise

class HighlightReelProcessor:
    def __init__(self):
        self.temp_dir = None
        self.main_title = None
        
    def process_reel(self, video_path: str, instructions: str, 
                    progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """Process the highlight reel according to the instructions."""
        # Create temporary directory for intermediate files
        self.temp_dir = tempfile.mkdtemp()
        
        try:
            # Parse instructions
            self.main_title, segments = self._parse_instructions(instructions)
            if not segments:
                raise ValueError("No valid segments found in instructions")
            
            # Phase 1: Create all title cards
            title_card_paths = []
            
            # Main title card
            if self.main_title:
                main_title_path = os.path.join(self.temp_dir, "00_main_title.mp4")
                self._create_title_card(
                    self.main_title,
                    "",  # No description for main title
                    duration=4.0,
                    style="main"
                ).write_videofile(main_title_path, fps=30, codec='libx264', audio=False)
                title_card_paths.append(main_title_path)
            
            # Segment title cards and description cards
            for i, segment in enumerate(segments):
                # Segment title
                segment_title_path = os.path.join(self.temp_dir, f"{i+1:02d}_segment_title.mp4")
                self._create_title_card(
                    segment['title'],
                    "",  # No description for segment title
                    duration=3.0,
                    style="segment"
                ).write_videofile(segment_title_path, fps=30, codec='libx264', audio=False)
                title_card_paths.append(segment_title_path)
                
                # Description cards and video clips for this segment
                for j, clip_info in enumerate(segment['clips']):
                    if clip_info['description']:
                        desc_path = os.path.join(self.temp_dir, f"{i+1:02d}_{j+1:02d}_description.mp4")
                        self._create_title_card(
                            "",  # No title for description
                            clip_info['description'],
                            duration=3.0,
                            style="description"
                        ).write_videofile(desc_path, fps=30, codec='libx264', audio=False)
                        title_card_paths.append(desc_path)
            
            # Phase 2: Extract video clips
            video_clip_paths = []
            for i, segment in enumerate(segments):
                for j, clip_info in enumerate(segment['clips']):
                    clip_path = os.path.join(self.temp_dir, f"{i+1:02d}_{j+1:02d}_clip.mp4")
                    clip = self._extract_clip(
                        video_path,
                        clip_info['timestamp'],
                        clip_info['duration']
                    )
                    clip.write_videofile(clip_path, fps=30, codec='libx264', audio_codec='aac')
                    video_clip_paths.append(clip_path)
                    clip.close()
            
            # Phase 3: Combine all clips in order
            clips = []
            all_paths = []  # Keep track of the order
            
            # Load main title if present
            if self.main_title:
                clips.append(VideoFileClip(title_card_paths[0]))
                all_paths.append(title_card_paths[0])
            
            title_idx = 1 if self.main_title else 0
            video_idx = 0
            
            # Load segment titles, descriptions, and video clips
            for segment in segments:
                # Add segment title
                clips.append(VideoFileClip(title_card_paths[title_idx]))
                all_paths.append(title_card_paths[title_idx])
                title_idx += 1
                
                for _ in segment['clips']:
                    # Add description card
                    clips.append(VideoFileClip(title_card_paths[title_idx]))
                    all_paths.append(title_card_paths[title_idx])
                    title_idx += 1
                    
                    # Add video clip
                    clips.append(VideoFileClip(video_clip_paths[video_idx]))
                    all_paths.append(video_clip_paths[video_idx])
                    video_idx += 1
            
            # Concatenate all clips
            from moviepy.editor import concatenate_videoclips
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Generate output path
            output_dir = Path("highlight_reels")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"highlight_reel_{Path(video_path).stem}.mp4"
            
            # Write final video
            final_clip.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up video objects
            final_clip.close()
            for clip in clips:
                clip.close()
            
            return str(output_path)
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            print("Temporary files are preserved in:", self.temp_dir)
            raise
            
    def _parse_instructions(self, instructions: str) -> Tuple[Optional[str], List[Dict]]:
        """Parse the instructions string into a main title and list of segments."""
        segments = []
        current_segment = None
        main_title = None
        current_clip = None
        
        # Split instructions into lines and process each line
        lines = instructions.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:  # Skip empty lines
                i += 1
                continue
                
            if line.startswith('[Title]'):
                main_title = line[7:].strip()
                print(f"Found main title: {main_title}")
                
            elif line.startswith('[Segment]'):
                # If we have a previous segment, add it to our list
                if current_segment is not None and current_segment.get('clips'):
                    print(f"Adding segment: {current_segment}")
                    segments.append(current_segment)
                
                # Start a new segment
                current_segment = {
                    'title': line[9:].strip(),  # Remove '[Segment] ' prefix
                    'clips': []
                }
                print(f"Started new segment: {current_segment['title']}")
                
            elif line.startswith('[Description]'):
                description = line[13:].strip()  # Remove '[Description] ' prefix
                if current_segment is not None:
                    # Start a new clip info
                    current_clip = {'description': description}
                    print(f"Added description to current clip: {description}")
                
            elif line.startswith('[CLIP') and current_segment is not None and current_clip is not None:
                clip_match = re.search(r'timestamp="([^"]+)" duration="(\d+)"', line)
                if clip_match:
                    current_clip['timestamp'] = clip_match.group(1)
                    current_clip['duration'] = int(clip_match.group(2))
                    print(f"Parsed clip info: timestamp={current_clip['timestamp']}, duration={current_clip['duration']}")
                    # Add the complete clip info to the current segment
                    current_segment['clips'].append(current_clip)
                    print(f"Added clip to segment {current_segment['title']}: {current_clip}")
                    current_clip = None
                else:
                    print(f"Failed to parse clip info from line: {line}")
            
            i += 1
        
        # Don't forget to add the last segment
        if current_segment is not None and current_segment.get('clips'):
            print(f"Adding final segment: {current_segment}")
            segments.append(current_segment)
        
        if not segments:
            raise ValueError("No valid segments found in instructions")
        
        print(f"\nFinal parsed structure:")
        print(f"Main title: {main_title}")
        print("Segments:")
        for segment in segments:
            print(f"  {segment['title']}:")
            for clip in segment['clips']:
                print(f"    - {clip}")
            
        return main_title, segments
    
    def _create_title_card(self, title: str, description: str, duration: float, style: str = "description") -> CompositeVideoClip:
        """Create a title card with title and description."""
        # Create background
        bg = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=duration)
        
        clips = [bg]
        
        # Configure text properties based on style
        if style == "main":
            if title:
                title_clip = TextClip(
                    title,
                    fontsize=90,
                    color='white',
                    font='Arial-Bold',
                    size=(1600, None),
                    method='caption',
                    align='center'
                ).set_position(('center', 400)).set_duration(duration)
                clips.append(title_clip)
                
        elif style == "segment":
            if title:
                title_clip = TextClip(
                    title,
                    fontsize=70,
                    color='white',
                    font='Arial-Bold',
                    size=(1600, None),
                    method='caption',
                    align='center'
                ).set_position(('center', 400)).set_duration(duration)
                clips.append(title_clip)
                
        else:  # description style
            if description:
                desc_clip = TextClip(
                    description,
                    fontsize=40,
                    color='white',
                    font='Arial',
                    size=(1400, None),
                    method='caption',
                    align='center'
                ).set_position(('center', 400)).set_duration(duration)
                clips.append(desc_clip)
        
        # Combine all elements
        composite = CompositeVideoClip(clips, size=(1920, 1080))
        return composite.set_duration(duration)
    
    def _extract_clip(self, video_path: str, timestamp: str, duration: int) -> VideoFileClip:
        """Extract a clip from the video at the specified timestamp and duration."""
        # Convert timestamp to seconds
        h, m, s = map(int, timestamp.split(':'))
        start_time = h * 3600 + m * 60 + s
        
        # Load video and extract clip
        video = VideoFileClip(video_path)
        clip = video.subclip(start_time, start_time + duration)
        
        # Resize if necessary (assuming 1920x1080 output)
        if clip.size != (1920, 1080):
            clip = clip.resize((1920, 1080))
        
        return clip 