#!/bin/bash

# Agent Chat Interface Setup Script
echo "🚀 Setting up Agent Chat Interface..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in PATH. Please install Anaconda or Miniconda first."
    echo "Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if environment.yml exists
if [ ! -f "setup/environment.yml" ]; then
    echo "❌ setup/environment.yml not found. Please make sure you're in the correct directory."
    exit 1
fi

# Create and activate conda environment
echo "📦 Creating conda environment from setup/environment.yml..."
conda env create -f setup/environment.yml

if [ $? -ne 0 ]; then
    echo "❌ Failed to create conda environment. Please check setup/environment.yml"
    exit 1
fi

echo "✅ Conda environment created successfully!"

# Activate the environment
echo "🔧 Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate agents-env

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate conda environment"
    exit 1
fi

echo "✅ Conda environment activated!"

# Ask for Gemini API key
echo ""
echo "🔑 Please enter your Gemini API key:"
echo "   (You can get one from: https://makersuite.google.com/app/apikey)"
read -s GEMINI_API_KEY

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ No API key provided. Please run the script again and provide a valid API key."
    exit 1
fi

# Export the API key
export GEMINI_API_KEY="$GEMINI_API_KEY"
echo "✅ API key exported successfully!"

# Download Titanic dataset only if data folder doesn't exist or is empty
echo ""
if [ ! -d "data" ] || [ -z "$(ls -A data 2>/dev/null)" ]; then
    echo "📊 Downloading Titanic dataset..."
    python download_titanic.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to download Titanic dataset"
        exit 1
    fi
    
    echo "✅ Titanic dataset downloaded successfully!"
else
    echo "📊 Data folder already exists with data. Skipping download."
fi

# Start the Flask application
echo ""
echo "🌐 Starting the Flask web server..."
echo "   The application will be available at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

python app.py 