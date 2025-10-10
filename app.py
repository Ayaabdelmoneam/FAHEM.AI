# app.py
import os
# os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
import streamlit as st
from modules.rag_colpali import ColPaliRAG
import streamlit.components.v1 as components
from modules.Mind_Map import RAGExtensions 
import requests
# import aifc
from modules.router import judge_relevance, web_search_agent ,judge_answer_relevance
import json 
from lipsync import LipSync
from modules.router import router
from modules.response_router import route_response
from modules.chatbot import Chatbot
import torch
from pydub import AudioSegment
from modules.preference_test import render_test_ui, load_saved_result
from io import BytesIO
import base64
import markdown
import time



st.set_page_config(page_title="🧠 FAHEM", layout="wide")
st.title("🧠 FAHEM.AI")

# st.markdown("This app connects to a ColPali server running on Google Colab.")
st.markdown("Upload a PDF and chat in English or Arabic. Hover over citations for details.")


@st.cache_resource
def load_lipsync():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    return LipSync(
        model='wav2lip',
        checkpoint_path="wav2lip.pth",
        nosmooth=True,
        device=device,
        img_size=96,
        save_cache=True,
        fps=25
    )
if "lipsync" not in st.session_state:
    st.session_state["lipsync"] = load_lipsync()
# Paths for lip-sync video generation
base_video_path = r"C:\Users\REWAN\Downloads\FAHEM\FAHEM\final.mp4"
checkpoint_path = r"wav2lip.pth"
cache_dir = r"C:\Users\REWAN\Downloads\FAHEM\FAHEM\cache"
device = 'cuda' if torch.cuda.is_available() else 'cpu'



# --- Session State Initialization (with Quiz additions) ---
if "rag_client" not in st.session_state:
    st.session_state.rag_client = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"
if "mindmap_html" not in st.session_state:
    st.session_state.mindmap_html = None
# --- NEW: Session state for Quiz ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_results" not in st.session_state:
    st.session_state.quiz_results = None
# ------------------------------------

# --- Sidebar for API Connection ---
# st.sidebar.title("API Connection")
ngrok_url = os.getenv("NGROK_URL", "")
# ngrok_url = st.sidebar.text_input("Paste your ngrok URL here", key="ngrok_url")

if ngrok_url and st.session_state.rag_client is None:
    try:
        st.session_state.rag_client = ColPaliRAG(api_url=ngrok_url)
        st.sidebar.success("✅ Connected to API server!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ Connection failed: {e}")

# --- View Mode Selection (with Quiz option) ---
if st.session_state.rag_client:
    st.sidebar.markdown("---")
    st.sidebar.title("📊 View Options")
    
    # --- UPDATED: Added "📝 Quiz" to the list ---
    view_option = st.sidebar.radio(
    "Select View:",
    ["💬 Chat Interface", "🧠 Mind Map", "🎴 Flash Cards","📝 Quiz", "📝 Learning Style Test"],
    key="view_selector"
)

    
    # Update view mode based on selection
    if view_option == "💬 Chat Interface":
        st.session_state.view_mode = "chat"
    elif view_option == "🧠 Mind Map":
        st.session_state.view_mode = "mindmap"
        # Load mind map if not already loaded
        if st.session_state.mindmap_html is None:
            with st.spinner("🎨 Generating mind map..."):
                try:
                    # Use the full ngrok_url from session state for reliability
                    api_url = st.session_state.rag_client.api_url
                    response = requests.get(f"{api_url}/mindmap", timeout=60)
                    if response.status_code == 200:
                        st.session_state.mindmap_html = response.text
                        st.sidebar.success("✅ Mind map loaded!")
                    else:
                        st.sidebar.error(f"❌ Failed to load mind map: {response.status_code}")
                except Exception as e:
                    st.sidebar.error(f"❌ Error loading mind map: {e}")
    
    elif view_option == "🎴 Flash Cards":
        st.session_state.view_mode = "flash_cards"
    elif view_option == "📝 Learning Style Test":
        st.session_state.view_mode = "learning_style"
    else: # This handles the "📝 Quiz" option
        st.session_state.view_mode = "quiz"
        

# --- Main Content Area ---
if st.session_state.rag_client:
    
    # MIND MAP VIEW (No changes)
    if st.session_state.view_mode == "mindmap":
        st.markdown("## 🧠 Interactive Document Mind Map")
        st.markdown("Explore the document structure visually. Click nodes to see details, use search to find keywords.")
        
        if st.session_state.mindmap_html:
            components.html(st.session_state.mindmap_html, height=850, scrolling=False)
        else:
            st.info("The mind map is loading or failed to load. Check the sidebar for status.")
            if st.button("🔄 Refresh Mind Map"):
                st.session_state.mindmap_html = None
                st.rerun()
    
    # CHAT VIEW (No changes)
    elif st.session_state.view_mode == "chat":
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and message.get("is_html", False):
                    components.html(message["content"], height=600, scrolling=False)
                else:
                    st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about your document..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🧠 Calling API and thinking..."):
                    try:
                        history = st.session_state.messages[-5:-1]
                        # response_data = st.session_state.rag_client.query(prompt,chat_history=history)
                        # base_answer = response_data["answer"]
                        # retrieved = response_data.get("retrieved", [])
                        # history = st.session_state.messages[-5:-1]

                        # 1️⃣ First retrieve docs
                        temp_response = st.session_state.rag_client.query(prompt, chat_history=history)
                        retrieved_docs = temp_response.get("retrieved", [])

                        # 2️⃣ Router decides (LLM intent + relevance + threshold)
                        llm = Chatbot().model
                        judge_llm = llm  # e.g., Gemini Flash or local model
                        # is_relevant = judge_answer_relevance(judge_llm, prompt, temp_response.get("answer", ""))
                        routing_result = router(llm, retrieved_docs,temp_response.get("answer", ""), prompt, min_score_threshold=0.4)
                        route_mode = routing_result.get("mode")
                        context = routing_result.get("context", "")

                        # 3️⃣ Answer generation
                        if route_mode == "internal":
                            response_data = temp_response
                            base_answer = response_data["answer"]
                            retrieved = response_data.get("retrieved", [])
                        else:
                            # Using the context returned by Tavily agent
                            web_context = routing_result["context"]
                            web_answer_resp = llm.generate_content(
                                f"Answer the question using this web info:\n\n{web_context}\n\nQ: {prompt}"
                            )
                            base_answer = getattr(web_answer_resp, "text", None) or "No answer found."
                            retrieved = []  # no structured sources from web

                        

                        # 2️⃣ Get learning style
                        saved = load_saved_result()
                        style = saved['dominant_style'] if saved else "text"

                        # context_text = "\n\n".join([d.get("content", "") for d in retrieved]) if retrieved else ""
                        # if context_text.strip():
                        #     llm = Chatbot().model
                        #     is_relevant = judge_relevance( llm, prompt, context_text)
                        #     is_relevant = bool(is_relevant)
                        # else:
                        #     is_relevant = False

                        # if not is_relevant:
                        #     print("isrelevent",is_relevant)
                        #     print("⚠️ Retrieved context seems irrelevant — searching the web...")
                        #     web_context = web_search_agent(prompt, timeout=20) or ""
                        #     llm = Chatbot().model
                        #     web_answer_resp = llm.generate_content( f"Answer using this web info:\n\n{web_context}\n\nQ: {prompt}", timeout=20)
                        #     base_answer = getattr(web_answer_resp, "text", None) or web_context or base_answer
                        #     retrieved = []  # web fallback has no structured retrieved sources
                        # else:
                        #     print("✅ Using internal RAG answer.")
                        # # 1️⃣ Decide whether to use internal RAG or web search
                        # try:
                        #     llm = Chatbot().model
                        #     rag = st.session_state.rag_client
                        #     routing_result = router(llm, retrieved, prompt, min_score_threshold=0.4)
                        #     route_mode = routing_result.get("mode")
                        #     context = routing_result.get("context", "")
                        #     if route_mode == "internal" and rag:
                        #         retrieved_docs = retrieved
                        #     else:
                        #         retrieved_docs = []  # web search has no structured sources
                        # except Exception as e:
                        #     st.error(f"Routing error: {e}")
                        #     route_mode = "internal"
                        #     context = ""
                        #     retrieved_docs = []

                        #####################
         # 2️⃣ Generate answer using Chatbot with the chosen context
                        chat = Chatbot()
                        # try:
                        #     base_answer =base_answer
                        #     # st.write(f"🌐 Language: {'Arabic' if language=='ar' else 'English'}")
                        # except Exception as e:
                        #     st.error(f"LLM error: {e}")
                        #     # base_answer, language = f"Error: {e}", "en"

                        # 4️⃣ Route response
                        # chat = Chatbot()
                        routed = route_response(style, base_answer,chat)
                                    # 5️⃣ Display output
                        if routed["type"] == "text":
                            answer_html = st.session_state.rag_client.build_citation_html(base_answer, retrieved)
                            components.html(answer_html, height=800, scrolling=False)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer_html,
                                "is_html": True
                            })

                        elif routed["type"] == "audio":
                            audio_bytes = routed["content"]
                            audio_seg = AudioSegment(data=audio_bytes, sample_width=2, frame_rate=24000, channels=1)
                            audio_path = "answeraudio.wav"
                            audio_seg.export(audio_path, format="wav")
                            st.audio(audio_path, format="audio/wav")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Audio response generated.",
                                "audio": audio_bytes,
                                # "language": language,
                                "sources": retrieved
                            })
                        elif routed["type"] == "video":
                            audio_bytes = routed["content"]
                            audio_seg = AudioSegment(data=audio_bytes, sample_width=2, frame_rate=24000, channels=1)
                            audio_path = "answeraudio.wav"
                            audio_seg.export(audio_path, format="wav")

                            st.info("⏳ Processing video...")
                            start_time = time.time()
                            lip = st.session_state["lipsync"]
                            output_video_path = os.path.join(os.getcwd(), "output_synced_video.mp4")
                            try:
                                lip.sync(base_video_path, audio_path, output_video_path)
                                end_time = time.time()
                                st.success(f"✅ Video done! Time: {end_time - start_time:.2f}s")
                                if os.path.exists(output_video_path):
                                    st.video(output_video_path)
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": routed.get("text", "🎬 Video response generated."),
                                        "audio": audio_bytes,
                                        "video_path": output_video_path,
                                        # "language": language,
                                        "sources": retrieved
                                    })
                            except Exception as e:
                                st.error(f"❌ Video generation error: {e}")


                       
               
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

    # --- NEW: FLASH CARDS VIEW ---
    elif st.session_state.view_mode == "flash_cards":
        st.header("🎴 Study with Flash Cards")
        st.markdown("Generate interactive flash cards from your document to test your knowledge. Click on a card to flip it.")
    
        api_url = st.session_state.rag_client.api_url
    
    # Add controls to the sidebar
        with st.sidebar:
            st.markdown("---")
            st.subheader("Flash Card Options")
            num_cards_to_generate = st.slider("Number of cards to generate", 1, 15, 5, key="num_flash_cards")
    
    # Add a session state variable for flash cards
        if "flash_cards_html" not in st.session_state:
            st.session_state.flash_cards_html = None
        
        if st.button("✨ Generate Flash Cards", use_container_width=True):
            with st.spinner("🤖 Generating flash cards..."):
                try:
                    data = {"num_cards": str(num_cards_to_generate)}
                    response = requests.post(f"{api_url}/generate_flash_cards", data=data, timeout=180)
                
                    if response.status_code == 200:
                        response_data = response.json()
                        st.session_state.flash_cards_html = response_data.get("html")
                    else:
                        st.error(f"Error generating flash cards: {response.text}")
                        st.session_state.flash_cards_html = None
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.session_state.flash_cards_html = None

        # Display the flash cards if they exist
        if st.session_state.flash_cards_html:
            st.markdown("---")
            st.components.v1.html(st.session_state.flash_cards_html, height=600, scrolling=True)
        
    # --- NEW: QUIZ VIEW ---
    elif st.session_state.view_mode == "quiz":
        st.header("📝 Test Your Knowledge")
        
        col1, col2 = st.columns([1, 2])
        api_url = st.session_state.rag_client.api_url

        with col1:
            with st.form("quiz_generation_form"):
                st.subheader("Create a New Quiz")
                num_mcq = st.slider("Number of MCQs", 1, 10, 5)
                num_tf = st.slider("Number of True/False", 0, 5, 2)
                lang = st.selectbox("Quiz Language", ["en", "ar"])
                if st.form_submit_button("✨ Generate Quiz", use_container_width=True):
                    with st.spinner("🤖 Generating new quiz..."):
                        data = {"num_mcq": str(num_mcq), "num_tf": str(num_tf), "lang": lang}
                        response = requests.post(f"{api_url}/generate_quiz", data=data, timeout=180)
                        if response.status_code == 200:
                            st.session_state.quiz_data = response.json().get("quiz")
                            st.session_state.quiz_results = None
                            st.success("Quiz generated!")
                        else:
                            st.error(f"Error: {response.text}")
            
            if st.session_state.quiz_results:
                results = st.session_state.quiz_results
                st.subheader("📈 Your Results")
                st.metric("Final Score", f"{results['score']} / {results['total']}")
                if not results['incorrect']:
                    st.balloons()
                    st.success("🎉 Perfect score! Excellent work.")
                    st.image("sh.jpeg", caption="شكلك فاهم يا نصة!")

        with col2:
            if st.session_state.quiz_data:
                quiz = st.session_state.quiz_data
                mcq, tf = quiz.get("mcq", []), quiz.get("true_false", [])
                
                with st.form("quiz_submission_form"):
                    st.subheader("Answer the Questions Below")
                    user_answers = {}
                    for i, q in enumerate(mcq):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        user_answers[f"mcq_{i}"] = st.radio("Options:", q.get("options", []), key=f"mcq_{i}", label_visibility="collapsed")
                    for i, q in enumerate(tf):
                        st.markdown(f"**{len(mcq)+i+1}. {q['question']}**")
                        user_answers[f"tf_{i}"] = st.radio("Select:", ["True", "False"], key=f"tf_{i}", label_visibility="collapsed")
                    
                    if st.form_submit_button("✅ Submit Answers", use_container_width=True):
                        score, total = 0, len(mcq) + len(tf)
                        incorrect_for_feedback = []
                        for i, q in enumerate(mcq):
                            answer_key = q.get("answer")
                            options = q.get("options", [])
                            correct_text = ""
                            if answer_key and len(answer_key) == 1 and 'A' <= answer_key.upper() <= 'Z':
                                correct_idx = ord(answer_key.upper()) - 65  # 'A' -> 0, 'B' -> 1, etc.
                                if 0 <= correct_idx < len(options):
                                    correct_text = options[correct_idx]
                            else:
                                correct_text = answer_key

                            user_answer = user_answers[f"mcq_{i}"]

                            if user_answer == correct_text:
                                score += 1
                            else:
                                incorrect_for_feedback.append({
                                    "id": f"q_mcq_{i}",
                                    "question": q['question'],
                                    "user_answer": user_answer,
                                    "correct_answer": correct_text 
                                })                   
                        for i, q in enumerate(tf):
                            correct_str = "True" if q.get("answer", True) else "False"
                            if user_answers[f"tf_{i}"] == correct_str: score += 1
                            else: incorrect_for_feedback.append({"id": f"q_tf_{i}", "question": q['question'], "user_answer": user_answers[f"tf_{i}"], "correct_answer": correct_str})
                        
                        feedback = {}
                        if incorrect_for_feedback:
                            with st.spinner("🤖 Getting feedback..."):
                                payload = {"incorrect_answers": incorrect_for_feedback}
                                response = requests.post(f"{api_url}/grade_quiz", json=payload, timeout=180)
                                if response.status_code == 200: feedback = response.json().get("feedback", {})
                        
                        st.session_state.quiz_results = {"score": score, "total": total, "incorrect": incorrect_for_feedback, "feedback": feedback}
                        st.rerun()

            if st.session_state.quiz_results and st.session_state.quiz_results['incorrect']:
                st.subheader("🧐 Mistakes Review")
                results = st.session_state.quiz_results
                for item in results['incorrect']:
                    with st.container(border=True):
                        st.markdown(f"**Question:** {item['question']}")
                        st.markdown(f"**Your Answer:** <span style='color: #FF4B4B;'>{item['user_answer']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Correct Answer:** <span style='color: #2ECC71;'>{item['correct_answer']}</span>", unsafe_allow_html=True)
                        feedback_text = results.get("feedback", {}).get(item['id'])
                        if feedback_text:
                            st.info(f"**Explanation:** {feedback_text}")
    elif st.session_state.view_mode == "learning_style":
        # st.title("📝 Learning Style Test")
        # st.markdown("Answer a few questions to discover your learning style.")
        render_test_ui()

        # Load and display saved result if exists
        saved = load_saved_result()
        if saved:
            st.success(f"✅ Your current dominant style: **{saved['dominant_style'].title()}**")

else:
    st.info("Please paste the ngrok URL from your Colab notebook into the sidebar to connect.")