# config.py
import os

# Model / SDK names
GEMINI_MODEL = "models/gemini-2.5-flash"                # LLM for text generation / RAG answers
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"      # TTS-capable model (if available)

# ColPali model name
COLPALI_MODEL = "vidore/colpali-v1.2"

# Qdrant config (":memory:" for in-memory; change to host config for persistent)
QDRANT_URL = ":memory:"

# Quiz file
QUIZ_FILE = "ai_generated_questions.json"

# Environment key
GEMINI_API_KEY_ENV = ""
