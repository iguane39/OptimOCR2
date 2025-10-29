"""
Setup script for OptimOCR2.

This script allows the package to be installed using pip.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)

setup(
    name='optimocr2',
    version='1.0.0',
    description='Advanced PDF to Word converter with formatting preservation',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='iguane39',
    author_email='',
    url='https://github.com/iguane39/OptimOCR2',
    license='MIT',

    # Package discovery
    packages=find_packages(exclude=['tests', 'tests.*']),

    # Include package data
    include_package_data=True,

    # Dependencies
    install_requires=requirements,

    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.11.1',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
        ],
        'advanced': [
            'easyocr>=1.7.0',
            'spacy>=3.7.0',
            'language-tool-python>=2.7.1',
        ],
        'docs': [
            'sphinx>=7.2.0',
            'sphinx-rtd-theme>=1.3.0',
        ],
    },

    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'optimocr=main:convert_pdf_to_docx',
            'optimocr-info=main:info',
        ],
    },

    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Office/Business :: Office Suites',
        'Topic :: Text Processing',
        'Topic :: Multimedia :: Graphics :: Capture :: Scanners',
    ],

    # Python version requirement
    python_requires='>=3.8',

    # Keywords
    keywords='ocr pdf word docx tesseract converter formatting',

    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/iguane39/OptimOCR2/issues',
        'Source': 'https://github.com/iguane39/OptimOCR2',
        'Documentation': 'https://github.com/iguane39/OptimOCR2/blob/main/README.md',
    },
)
