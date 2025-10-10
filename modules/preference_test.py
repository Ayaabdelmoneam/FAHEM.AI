# modules/preference_test.py
import datetime
import streamlit as st
import config
from modules.utils import save_json
import json

QUIZ_FILE = config.QUIZ_FILE

def render_test_ui():
    st.title("🎯 Learning Style Test")
    st.write("Answer the following questions to discover your learning style!")

    try:
        with open(QUIZ_FILE, "r", encoding="utf-8") as f:
            quiz_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Missing quiz file: {QUIZ_FILE}. Put your JSON in project root.")
        st.stop()
        return

    # render questions
    answers = []
    for i, q in enumerate(quiz_data["questions"]):
        st.subheader(f"Question {i+1}")
        st.write(q["question"])
        options = [opt["text"] for opt in q["options"]]
        choice = st.radio("Select one:", options, key=f"q{i}")
        answers.append(options.index(choice))

    if st.button("Submit Test"):
        scores = {"mindmap": 0, "audio": 0, "text": 0 ,"video": 0}
        for q_idx, sel_idx in enumerate(answers):
            style = quiz_data["questions"][q_idx]["options"][sel_idx]["style"]
            scores[style] += 1

        dominant_style = max(scores, key=scores.get)
        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "dominant_style": dominant_style,
            "scores": scores,
            "answers": answers
        }

        # Save to session and to disk for chatbot to read
        st.session_state["learning_result"] = result
        save_json("learning_style_result.json", result)

        st.success(f"✅ Your dominant learning style is: **{dominant_style}**")
        st.json(result)

def load_saved_result():
    """
    Loads previously saved learning result if present in session or file.
    """
    if "learning_result" in st.session_state:
        return st.session_state["learning_result"]
    try:
        with open("learning_style_result.json", "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
            st.session_state["learning_result"] = data
            return data
    except Exception:
        return None
