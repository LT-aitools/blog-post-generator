import streamlit as st
import os
import sys
import tempfile
from pathlib import Path

# THIS MUST BE THE FIRST STREAMLIT COMMAND - NO OTHER STREAMLIT COMMANDS BEFORE THIS
st.set_page_config(
    page_title="Blog Content Creator",
    page_icon="📝",
    layout="wide"
)

# Now you can add the rest of your code
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

# NOW you can add styles
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

# Now check if video utilities are accessible
# (This must be AFTER the page config, unlike in your previous code)
try:
    from src.videoclipper import extract_video_clip as vc_extract

    st.sidebar.success("✅ Video utilities successfully imported")
except ImportError as e:
    st.sidebar.error(f"❌ Failed to import video utilities: {str(e)}")

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
                    processor = BlogProcessor(output_base_dir=output_folder)

                    # Process the blog
                    result = processor.process_blog(str(temp_doc), str(temp_video))

                    # Show result
                    if result.success:
                        st.markdown(f'<div class="success-message">Blog processed successfully!</div>',
                                    unsafe_allow_html=True)
                        st.markdown("### Generated Files:")
                        st.markdown(f"**HTML file:** {result.html_path}")
                        st.markdown(f"**Media folder:** {result.media_folder}")

                        if result.warnings:
                            st.warning("### Warnings:")
                            for warning in result.warnings:
                                st.write(f"- {warning}")
                    else:
                        st.error("Blog processing failed!")
                        if result.errors:
                            for error in result.errors:
                                st.error(f"Error: {error}")

                except Exception as e:
                    st.error(f"Error processing blog: {str(e)}")
                    st.exception(e)  # This will display the full traceback

# Add rest of the app here