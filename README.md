# 🧠 FAHEM.AI — Multimodal Educational Chatbot (RAG + Gemini + LipSync)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.20%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![AI](https://img.shields.io/badge/Powered_by-Gemini_&_ColPali-purple)

---

## 🎥 **[Watch Demo Video](https://drive.google.com/file/d/107wF6hW7qxQIVBKk41gxsvWMRNBh5Bxk/view)**  
*(Click to see FAHEM in action — full walkthrough of features and UI!)*

## Overview

**FAHEM** is an interactive **multimodal educational assistant** built with **Streamlit**.  
It combines **Retrieval-Augmented Generation (RAG)** using **ColPali**, **Google Gemini** for reasoning and explanation generation, and **Wav2Lip** for realistic lip-synced video narration.

The chatbot provides personalized learning experiences by adapting to each user's **learning style** — whether they prefer **reading**, **listening**, **visuals**, or **video explanations**.

---

## Key Features

### 🔍 1. Intelligent PDF-Based Q&A
- Upload any educational PDF.
- The system retrieves relevant knowledge using **ColPali** embeddings.
- Every answer includes **citations** linked to the **exact PDF pages**.

### 💬 2. Conversational AI in English & Arabic
- Uses **Google Gemini** for natural dialogue.
- Supports **bilingual interaction** (English and Arabic).

### 🔊 3. Text-to-Speech (TTS)
- Converts answers into spoken narration.
- Supports **male or female** voices using Google Cloud TTS.

### 🎬 4. Lip-Synced Video Narration
- Generates a realistic **talking-head educational video** using **Wav2Lip**.
- Ideal for visual and auditory learners.

### 🧠 5. Learning Style Personalization
- Built-in **Learning Style Test** determines your dominant style:
  - ✏️ Reading/Writing  
  - 🎧 Auditory  
  - 🎥 Visual or Video-Based
- Adapts answers accordingly.

### 🗂️ 6. Flashcards Generator
-Automatically generates interactive flashcards from PDF content or chatbot responses.
- Designed to enhance active recall and memory retention.
- Suitable for quick revision sessions or self-testing.

### 🧩 7. Mind Map Visualizer
-Transforms retrieved knowledge into structured mind maps.
- Helps learners visualize relationships between concepts.
- Perfect for spatial and conceptual understanding.
### ⚙️ 8. Configurable & Modular
- Simple configuration through the **Settings** tab.
- Modular code design — easy to extend or integrate.

---

## 🏗️ Project Structure
```bash
FAHEM/
│
├── app.py                     # Main Streamlit app entry point
│
├── modules/                   # Core modules of the FAHEM system
│   ├── chatbot.py             # Gemini-based chatbot logic
│   ├── rag_colpali.py         # ColPali retrieval and embedding
│   ├── response_router.py     # Routes response modes (text, audio, video)
│   ├── preference_test.py     # Learning style test logic and UI
│   ├── utils.py               # Utility helpers (JSON, file ops, formatting)
│   └── google_tts.py          # Text-to-speech implementation
│
├── lipsync.py                 # Lip-syncing using Wav2Lip
│
├── config.py                  # Configuration (API keys, model names, URLs)
│
├── cache/                     # Cached data and temporary files
│
├── requirements.txt           # Python dependencies
│
└── README.md                  # Project documentation
````

## ⚙️ Installation Guide

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/fahem-chatbot.git
cd fahem-chatbot
````
### 2. Create and Activate a Virtual Environment
python -m venv venv
```bash
venv\Scripts\activate   # Windows
````
# or
```bash
source venv/bin/activate  # macOS/Linux
````
### 3. Install Requirements
```bash
pip install -r requirements.txt
````
### 4. Run the App
```bash
streamlit run app.py
````


