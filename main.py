"""
main.py — FastAPI backend for SMS Phishing Detection
Supports two models:
  - svm   : LinearSVC + TF-IDF pipeline (svm_smishing_pipeline.pkl)
  - distilbert : Fine-tuned DistilBERT (folder with config.json + model.safetensors)

Usage:
  uvicorn main:app --reload
"""

import re
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Paths ──────────────────────────────────────────────────────────────────────
SVM_MODEL_PATH       = Path("Models/svm_smishing_pipeline.pkl")   # single pipeline file
DISTILBERT_MODEL_DIR = Path("Models/distilbert_final/distilbert_smishing_model_FINAL")  # folder with HuggingFace files

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="SMS Phishing Detector")

# Allow the HTML frontend (served as a local file) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy-loaded models ─────────────────────────────────────────────────────────
_svm_pipeline    = None
_distilbert_pipe = None


def get_svm():
    global _svm_pipeline
    if _svm_pipeline is None:
        if not SVM_MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=f"SVM model not found at '{SVM_MODEL_PATH}'. "
                       "Export it from Colab with joblib.dump(pipeline, 'svm_smishing_pipeline.pkl').",
            )
        _svm_pipeline = joblib.load(SVM_MODEL_PATH)
    return _svm_pipeline


def get_distilbert():
    global _distilbert_pipe
    if _distilbert_pipe is None:
        if not DISTILBERT_MODEL_DIR.exists():
            raise HTTPException(
                status_code=503,
                detail=f"DistilBERT model folder not found at '{DISTILBERT_MODEL_DIR}'.",
            )
        # Import here so the server still starts even if torch/transformers are missing
        try:
            from transformers import pipeline as hf_pipeline
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="transformers / torch not installed. Run: pip install transformers torch",
            )
        _distilbert_pipe = hf_pipeline(
            "text-classification",
            model=str(DISTILBERT_MODEL_DIR),
            tokenizer=str(DISTILBERT_MODEL_DIR),
            truncation=True,
            max_length=128,
        )
    return _distilbert_pipe


# ── Preprocessing (mirrors the Colab notebook) ─────────────────────────────────
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

def preprocess(text: str) -> str:
    text = text.lower()
    text = URL_PATTERN.sub("[URL]", text)
    return text


# ── Request / Response schemas ─────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    text: str
    model: str  # "svm" or "distilbert"


class AnalyzeResponse(BaseModel):
    model: str
    label: str        # "Safe" or "Smishing"
    confidence: float # 0.0 – 1.0  (best-effort)


# ── Endpoint ───────────────────────────────────────────────────────────────────
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    model_name = req.model.strip().lower()
    clean_text = preprocess(req.text)

    if model_name == "svm":
        pipe = get_svm()
        pred = int(pipe.predict([clean_text])[0])          # 0 = Ham, 1 = Smishing
        score = float(pipe.decision_function([clean_text])[0])  # signed margin distance
        # Map decision score to a rough 0-1 confidence via sigmoid
        import math
        confidence = 1 / (1 + math.exp(-score))
        label = "Smishing" if pred == 1 else "Safe"
        return AnalyzeResponse(model="SVM", label=label, confidence=round(confidence, 4))

    elif model_name == "distilbert":
        pipe = get_distilbert()
        result = pipe(clean_text)[0]
        # HuggingFace label names depend on fine-tuning; map LABEL_0/LABEL_1 or explicit names
        raw_label = result["label"].upper()
        score = float(result["score"])
        if raw_label in ("LABEL_1", "SMISHING", "1"):
            label = "Smishing"
            confidence = score
        else:
            label = "Safe"
            confidence = score
        return AnalyzeResponse(model="DistilBERT", label=label, confidence=round(confidence, 4))

    else:
        raise HTTPException(status_code=400, detail=f"Unknown model '{req.model}'. Use 'svm' or 'distilbert'.")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}