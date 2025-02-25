import streamlit as st
import os
import sys
import tempfile
from pathlib import Path

# Set page title and favicon - THIS MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Blog Content Creator",
    page_icon="📝",
    layout="wide"
)

# Add the project root directory to Python path (same as in your examples)
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Import the BlogProcessor
try:
    from src.blog_processor import BlogProcessor

    blog_processor_available = True
except ImportError as e:
    blog_processor_available = False
    import_error = str(e)

try:
    from src.screenshot_extractor import extract_screenshots_at_times
    from src.video_clipper import extract_video_clip

    video_utils_available = True
except ImportError:
    video_utils_available = False

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4A90E2;
    }
    .section-header {
        font-size: 1.8rem;
        color: #5A6F8C;
        margin-top: 2rem;
    }
    .success-message {
        background-color: #D5F5E3;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #2E7D32;
    }
    .file-info {
        background-color: #E8F4F8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Now check if video utilities are accessible
try:
    from src.videoclipper import extract_video_clip
    from src.screenshot_extractor import extract_screenshots_at_times

    st.sidebar.success("✅ Video utilities successfully imported")
except ImportError as e:
    st.sidebar.error(f"❌ Failed to import video utilities: {str(e)}")

# Display debug info in sidebar
debug_expander = st.sidebar.expander("Debug Info")
with debug_expander:
    st.write("Current working directory:", os.getcwd())
    st.write("Python path:")
    for path in sys.path:
        st.write(f"- {path}")

    if blog_processor_available:
        st.write("✅ BlogProcessor successfully imported")
    else:
        st.write(f"❌ BlogProcessor import error: {import_error}")

    # List files in current directory to help with debugging
    st.write("Files in current directory:")
    try:
        files = os.listdir(".")
        for file in files:
            st.write(f"- {file}")

        if os.path.exists("src"):
            st.write("Files in src directory:")
            src_files = os.listdir("src")
            for file in src_files:
                st.write(f"- src/{file}")
    except Exception as e:
        st.write(f"Error listing files: {str(e)}")

# Sidebar navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose the tool",
    ["Home", "Blog Processor", "Video Screenshot Tool", "Video Clipper"]
)


# Function to create temp directory
def get_temp_dir():
    temp_dir = Path(tempfile.gettempdir()) / "blog_creator_temp"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


# Home page
if app_mode == "Home":
    st.markdown('<p class="main-header">Blog Content Creator Tools</p>', unsafe_allow_html=True)

    st.write("""
    Welcome to the Blog Content Creator toolkit! This application helps you create rich blog content
    with support for processing Word documents, extracting video screenshots, and creating video clips.

    **Available Tools:**

    * **Blog Processor**: Convert Word documents to formatted HTML for your blog
    * **Video Screenshot Tool**: Extract specific frames from videos for your blog posts
    * **Video Clipper**: Create short video clips from longer videos

    Select a tool from the sidebar to get started!
    """)

    # Show tool availability
    st.markdown('<p class="section-header">System Status</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if blog_processor_available:
            st.success("✅ Blog Processor: Available")
        else:
            st.error("❌ Blog Processor: Not available")

    with col2:
        if video_utils_available:
            st.success("✅ Video Utilities: Available")
        else:
            st.error("❌ Video Utilities: Not available")

# Blog Processor
elif app_mode == "Blog Processor" and blog_processor_available:
    st.markdown('<p class="main-header">Blog Processor</p>', unsafe_allow_html=True)
    st.write("Convert Word documents and videos to blog content")

    # Create two columns for document and video upload
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Document")
        uploaded_doc = st.file_uploader("Upload a Word document", type=["docx"])

    with col2:
        st.subheader("Video")
        uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])

    # Check if both files are uploaded
    if uploaded_doc is not None and uploaded_video is not None:
        # Create temporary files
        temp_dir = get_temp_dir()
        temp_doc = temp_dir / uploaded_doc.name
        temp_video = temp_dir / uploaded_video.name

        with open(temp_doc, "wb") as f:
            f.write(uploaded_doc.getvalue())

        with open(temp_video, "wb") as f:
            f.write(uploaded_video.getvalue())

        st.markdown(
            f'<div class="file-info">Document: {uploaded_doc.name} ({uploaded_doc.size / 1024:.1f} KB)<br>Video: {uploaded_video.name} ({uploaded_video.size / 1024 / 1024:.1f} MB)</div>',
            unsafe_allow_html=True)

        output_folder = st.text_input("Output folder name", "processed_blogs")

        if st.button("Process Blog"):
            with st.spinner("Processing blog..."):
                try:
                    # Create output directory
                    os.makedirs(output_folder, exist_ok=True)

                    # Initialize processor with the output directory
                    # This matches exactly how you use it in blog_processor_example.py
                    processor = BlogProcessor(output_base_dir=output_folder)

                    # Extra debug info during processing
                    st.info("Starting blog processing...")
                    st.text(f"Document path: {temp_doc}")
                    st.text(f"Video path: {temp_video}")

                    # Process the blog
                    result = processor.process_blog(str(temp_doc), str(temp_video))

                    # Show result
                    if hasattr(result, 'success') and result.success:
                        st.markdown(f'<div class="success-message">Blog processed successfully!</div>',
                                    unsafe_allow_html=True)
                        st.markdown("### Generated Files:")
                        st.markdown(f"**HTML file:** {result.html_path}")
                        st.markdown(f"**Media folder:** {result.media_folder}")

                        if hasattr(result, 'warnings') and result.warnings:
                            st.warning("### Warnings:")
                            for warning in result.warnings:
                                st.write(f"- {warning}")

                        # Provide download links if possible
                        try:
                            with open(result.html_path, "r") as f:
                                html_content = f.read()
                                st.download_button(
                                    "Download HTML",
                                    html_content,
                                    file_name=os.path.basename(result.html_path),
                                    mime="text/html"
                                )
                        except Exception as e:
                            st.warning(f"Could not prepare HTML download: {str(e)}")
                    else:
                        st.error("Blog processing failed!")
                        if hasattr(result, 'errors') and result.errors:
                            for error in result.errors:
                                st.error(f"Error: {error}")

                except Exception as e:
                    st.error(f"Error processing blog: {str(e)}")
                    st.exception(e)  # This will display the full traceback

# Video Screenshot Tool
elif app_mode == "Video Screenshot Tool" and video_utils_available:
    st.markdown('<p class="main-header">Video Screenshot Tool</p>', unsafe_allow_html=True)
    st.write("Extract screenshots from videos at specific timestamps")

    uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_video is not None:
        # Create a temporary file
        temp_dir = get_temp_dir()
        temp_video = temp_dir / uploaded_video.name

        with open(temp_video, "wb") as f:
            f.write(uploaded_video.getvalue())

        st.markdown(
            f'<div class="file-info">Video uploaded: {uploaded_video.name} ({uploaded_video.size / 1024 / 1024:.1f} MB)</div>',
            unsafe_allow_html=True)

        # Get timestamps
        st.markdown("### Enter timestamps (in seconds)")

        col1, col2 = st.columns(2)

        with col1:
            timestamps_input = st.text_area(
                "Enter timestamps (one per line)",
                "10\n30\n60",
                help="Enter timestamps in seconds, one per line"
            )

        with col2:
            st.write("Preview of timestamps:")
            try:
                timestamps = [float(t.strip()) for t in timestamps_input.strip().split("\n") if t.strip()]
                for i, ts in enumerate(timestamps):
                    mins, secs = divmod(ts, 60)
                    st.text(f"Screenshot {i + 1}: {int(mins)}m {secs:.1f}s")
            except ValueError:
                st.error("Please enter valid numbers for timestamps")

        output_folder = st.text_input("Output folder name", "screenshots")

        if st.button("Extract Screenshots"):
            if len(timestamps) > 0:
                with st.spinner("Extracting screenshots..."):
                    try:
                        # Create output directory
                        os.makedirs(output_folder, exist_ok=True)

                        # Extract screenshots
                        extract_screenshots_at_times(str(temp_video), output_folder, timestamps)

                        # Show success message
                        st.markdown(
                            f'<div class="success-message">Screenshots extracted successfully! Saved to {output_folder}</div>',
                            unsafe_allow_html=True)

                        # Try to display the screenshots
                        try:
                            st.markdown("### Generated Screenshots:")
                            screenshot_files = [f for f in os.listdir(output_folder) if f.endswith(('.jpg', '.png'))]

                            if screenshot_files:
                                for i, img_file in enumerate(screenshot_files[:5]):  # Show up to 5 images
                                    img_path = os.path.join(output_folder, img_file)
                                    st.image(img_path, caption=f"Screenshot {i + 1}: {img_file}")

                                if len(screenshot_files) > 5:
                                    st.write(f"... and {len(screenshot_files) - 5} more screenshots")
                        except Exception as e:
                            st.warning(f"Could not display screenshots: {str(e)}")

                    except Exception as e:
                        st.error(f"Error extracting screenshots: {str(e)}")
                        st.exception(e)
            else:
                st.error("Please enter at least one valid timestamp")

# Video Clipper
elif app_mode == "Video Clipper" and video_utils_available:
    st.markdown('<p class="main-header">Video Clipper</p>', unsafe_allow_html=True)
    st.write("Extract clips from videos for your blog posts")

    uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_video is not None:
        # Create a temporary file
        temp_dir = get_temp_dir()
        temp_video = temp_dir / uploaded_video.name

        with open(temp_video, "wb") as f:
            f.write(uploaded_video.getvalue())

        st.markdown(
            f'<div class="file-info">Video uploaded: {uploaded_video.name} ({uploaded_video.size / 1024 / 1024:.1f} MB)</div>',
            unsafe_allow_html=True)

        # Get clip parameters
        st.markdown("### Clip Parameters")

        col1, col2 = st.columns(2)

        with col1:
            start_min = st.number_input("Start Time (minutes)", min_value=0, step=1)
            start_sec = st.number_input("Start Time (seconds)", min_value=0, max_value=59, step=1)
            start_time = start_min * 60 + start_sec

        with col2:
            duration_min = st.number_input("Duration (minutes)", min_value=0, step=1)
            duration_sec = st.number_input("Duration (seconds)", min_value=1 if duration_min == 0 else 0, max_value=59,
                                           step=1)
            duration = duration_min * 60 + duration_sec

        st.markdown(
            f"Clip will start at **{start_min}m {start_sec}s** and last for **{duration_min}m {duration_sec}s**")

        output_folder = st.text_input("Output folder name", "clips")

        if st.button("Extract Clip"):
            with st.spinner("Extracting video clip..."):
                try:
                    # Create output directory
                    os.makedirs(output_folder, exist_ok=True)

                    # Extract clip
                    output_path = extract_video_clip(str(temp_video), output_folder, start_time, duration)

                    # Show success message
                    st.markdown(f'<div class="success-message">Video clip extracted successfully!</div>',
                                unsafe_allow_html=True)
                    st.markdown(f"Saved to: **{output_path}**")

                    # Try to create a video player
                    try:
                        video_file = open(output_path, 'rb')
                        video_bytes = video_file.read()
                        st.video(video_bytes)
                    except Exception as e:
                        st.warning(f"Could not display video: {str(e)}")

                except Exception as e:
                    st.error(f"Error extracting clip: {str(e)}")
                    st.exception(e)

# Module not available warnings
elif app_mode == "Blog Processor" and not blog_processor_available:
    st.error("Blog Processor module is not available. Please check your installation.")
    st.info("""
    To fix this issue:
    1. Make sure your project structure includes a src/blog_processor.py file
    2. Make sure BlogProcessor class is defined in that file
    3. Check that all required dependencies are installed
    """)

    if 'import_error' in locals():
        st.code(f"Import error: {import_error}")

elif (app_mode == "Video Screenshot Tool" or app_mode == "Video Clipper") and not video_utils_available:
    st.error("Video utilities are not available. Please check your installation.")
    st.info("""
    To fix this issue:
    1. Make sure your project structure includes src/screenshot_extractor.py and src/video_clipper.py files
    2. Make sure all required dependencies (like opencv-python and ffmpeg-python) are installed
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    """
    This app is maintained on [GitHub](https://github.com/yourusername/blog-content-creator).

    © 2025 Your Name
    """
)