from setuptools import setup, find_packages

setup(
    name="blog_processor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-docx>=0.8.11",
        "moviepy>=1.0.3",
        "imageio>=2.31.1",
    ],
    python_requires=">=3.7",
) 