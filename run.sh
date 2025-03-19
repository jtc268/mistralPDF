#!/bin/bash

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null
then
    echo "Python could not be found. Please install Python 3.7 or higher."
    exit 1
fi

# Determine which Python command to use
if command -v python3 &> /dev/null
then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Check for dependencies
echo "Checking dependencies..."
$PYTHON_CMD -m pip install requests tk

# Run the application
echo "Starting PDF to Markdown Converter..."
$PYTHON_CMD simple_pdf_to_md.py 