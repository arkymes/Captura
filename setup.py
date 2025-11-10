from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="captura",
    version="1.0.0",
    author="Victor Llera",
    author_email="",
    description="Sistema de geração automática de documentação de processos a partir de vídeos usando IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arkymes/Captura",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Documentation",
        "Topic :: Office/Business",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "google-genai>=0.2.0",
        "python-docx>=0.8.11",
        "markdown>=3.5.0",
        "beautifulsoup4>=4.12.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "captura=Captura.ai_doc_generator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.css", "*.json"],
    },
)
