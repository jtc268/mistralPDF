#!/bin/bash

# Script to initialize and push project to GitHub

# Set repository name
REPO_NAME="mistral-ocr-pdf-to-text-markdown"

echo "🚀 Publishing $REPO_NAME to GitHub"
echo "-----------------------------------"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository if not already done
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Add all files to staging
echo "Adding files to staging..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Initial commit: Mistral OCR PDF-to-Text/Markdown Converter"

# Prompt for GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

# Create repository on GitHub
echo "To create a new repository on GitHub:"
echo "1. Go to https://github.com/new"
echo "2. Enter repository name: $REPO_NAME"
echo "3. Add description: High-quality PDF to Text/Markdown converter using Mistral AI's OCR"
echo "4. Choose public or private"
echo "5. Do NOT initialize with README, .gitignore, or license (we already have these)"
echo "6. Click 'Create repository'"

read -p "Have you created the repository on GitHub? (y/n): " RESPONSE
if [[ $RESPONSE != "y" && $RESPONSE != "Y" ]]; then
    echo "Please create the repository on GitHub and run this script again."
    exit 1
fi

# Add remote origin
echo "Adding GitHub remote..."
git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin master || git push -u origin main

echo "-----------------------------------"
echo "✅ Repository successfully published to GitHub!"
echo "🌐 View your repository at: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "Don't forget to update the API key in your code before sharing with others!" 