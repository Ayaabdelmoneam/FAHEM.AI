from modules.chatbot import Chatbot
from io import BytesIO
from pydub import AudioSegment
def route_response(mode: str, base_answer: str, chat: Chatbot):
    """
    Only routes/rendering — no extra prompting.
    """
    mode = (mode or "text").lower()

    if mode == "audio":
        audio_bytes = chat.text_to_speech_Audio(base_answer)
            # Convert to WAV (requires ffmpeg)
        audio_seg = AudioSegment(
                data=audio_bytes,
                sample_width=2,  # 16-bit PCM
                frame_rate=24000,
                channels=1
            )  # or actual format
        buf = BytesIO()
        audio_seg.export(buf, format="wav")
    
        return {"type": "audio", "content": buf.getvalue(), "subtype": "speech"}
     
    
    if mode == "video":
        audio_bytes = chat.text_to_speech(base_answer)
            # Convert to WAV (requires ffmpeg)
        audio_seg = AudioSegment(
                data=audio_bytes,
                sample_width=2,  # 16-bit PCM
                frame_rate=24000,
                channels=1
            )  # or actual format
        buf = BytesIO()
        audio_seg.export(buf, format="wav")
    
        return {"type": "video", "content": buf.getvalue(), "subtype": "speech"}
       

    if mode == "visual":
        # Assume LLM already produced SVG or visual-friendly text
        return {"type": "svg", "content": base_answer}

    if mode == "byquestion":
        return {"type": "questions", "content": base_answer}

    # default: plain text
    return {"type": "text", "content": base_answer}
