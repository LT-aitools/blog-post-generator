from setuptools import setup, find_packages

setup(
    name="blog-post-generator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "opencv-python>=4.8.0",
        "ffmpeg-python",
        "moviepy>=1.0.3",
        "PyQt6>=6.8.0",
        "python-docx>=0.8.11",
        "PyPDF2>=3.0.0",
        "numpy>=1.22.0",
        "Pillow>=9.0.0",
        "markdown>=3.4.1",
        "imageio>=2.31.1",
    ],
    python_requires=">=3.7",
) 