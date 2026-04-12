# CPE020 - SMS Phishing Detection

A web application for detecting SMS phishing (smishing) messages using machine learning models.

## Project Structure

- `main.py` - FastAPI backend serving the detection API
- `index.html`, `style.css`, `script.js` - Frontend web interface
- `requirements.txt` - Python dependencies
- `Models/` - Directory containing trained ML models (must be downloaded separately)

## Prerequisites

- Python 3.8 or higher
- The `Models` folder must be downloaded and placed in the project root before running the application

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Leon/CPE020.git
   cd CPE020
   ```

2. **Download the Models folder**

   Download the `Models` folder containing the trained ML models and place it in the project root directory. The folder should contain:
   - `svm_smishing_pipeline.pkl` - SVM model pipeline
   - `distilbert_final/distilbert_smishing_model_FINAL/` - DistilBERT model files

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the backend server**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`

2. **Open the frontend**
   
   Open `index.html` in your web browser.

## Available Models

- **SVM**: LinearSVC with TF-IDF vectorizer
- **DistilBERT**: Fine-tuned DistilBERT transformer model

## API Endpoints

- `POST /analyze` - Analyze text for phishing (body: `{"text": "...", "model": "svm"|"distilbert"}`)
- `GET /health` - Health check endpoint