import os
import google.generativeai as genai
# from google.generativeai.types import GenerationConfig
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold
import config
from google.generativeai import types

genai.configure(api_key="")

class Chatbot:
    def __init__(self, model_name=config.GEMINI_MODEL, tts_model=config.GEMINI_TTS_MODEL):
        self.model_name = model_name
        self.tts_model = tts_model
        
        self.model = genai.GenerativeModel(model_name)
        self.tts = genai.GenerativeModel("models/gemini-2.5-flash-preview-tts")
        self.chat_history = []

    def detect_language(self, text):
        """Simple language detection based on character patterns."""
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len([c for c in text if c.isalpha()])
        if total_chars == 0:
            return "en"
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"

    def answer_with_context(
        self, user_query: str, context: str, style: str = "text",
        temperature: float = 0.2, max_tokens: int = 512
    ):
        query_lang = self.detect_language(user_query)
        
        style_instructions = {
            "text": "Explain clearly in well-structured written text.",

            "audio": """Answer like a short podcast chat between two people, Joe and Jane.
Joe asks simple questions, and Jane explains the topic clearly and naturally.
Keep it friendly, short, and easy to understand.""",

            "visual": "Explain in a way that could be easily turned into diagrams or visuals. Use concise, spatial descriptions.",
            "byquestion": "Teach Socratically: respond with a sequence of guiding questions instead of direct exposition.",
            "video": "Write a smooth narration for a short educational video. Do not include scene directions or character names. Make it sound like a clear voiceover script.."
        }

        if query_lang == "ar":
            system_prompt = (
                "أنت مساعد متخصص في تحليل المستندات. أجب على سؤال المستخدم باستخدام السياق المقدم فقط. "
                "استخدم الاستشهادات المرقمة مثل [1]، [2] في إجابتك. "
                "أجب باللغة العربية فقط. إذا لم تجد الإجابة في السياق، أخبر المستخدم بذلك بوضوح.\n\n"
            )
        else:
            system_prompt = (
                "You are an expert document analyst. Answer the user's question using ONLY the provided context. "
                "Cite sources inline using numeric citations like [1], [2]. "
                "Answer in English only. If the answer is not present in the provided context, clearly state that you cannot find it.\n\n"
                 f"Adapt your explanation to this learning style: {style_instructions.get(style.lower(), style_instructions['text'])}\n\n"
            )

        prompt = (
            system_prompt +
            (context or "") +
            f"\n\n{'سؤال المستخدم' if query_lang == 'ar' else 'User Question'}: {user_query}\n\n"
            f"{'الإجابة مع الاستشهادات' if query_lang == 'ar' else 'Answer with inline citations'}:"
        )
        print(f"Generated prompt: {prompt}")
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    

                )
            )
            print(f"Raw response: {response}")
            if response and hasattr(response, "text") and response.text:
                answer = response.text
                self.chat_history.append({
                    "question": user_query,
                    "answer": answer,
                    "language": query_lang
                })
                return answer, query_lang
            elif response.candidates and response.candidates[0].content.parts:
                parts = response.candidates[0].content.parts
                texts = [getattr(p, "text", None) for p in parts if getattr(p, "text", None)]
                answer = "\n".join([str(t) for t in texts if t])
                self.chat_history.append({
                    "question": user_query,
                    "answer": answer,
                    "language": query_lang
                })
                print(f"Answer: {answer}")
                return answer, query_lang

            else:
                return "⚠️ No valid text response returned from Gemini.", query_lang

        except Exception as e:
            print(f"❌ Gemini generation error: {e}")
            return f"Error generating answer: {e}", query_lang


    def text_to_speech(self, text: str, voice_name: str = "Kore"):
        """
        Generate speech audio using Gemini TTS.
        Returns raw PCM bytes for st.audio().
        """
        try:
            response = self.tts.generate_content(
                [text],
                generation_config={
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "charon"
                            }
                        }
                    }
                }
            )

            # Extract audio bytes
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data is not None:
                        print(f"✅ Audio generated successfully for text: {text}")
                        return part.inline_data.data

            raise RuntimeError("No audio data found in Gemini response")

        except Exception as e:
            print(f"🔈 TTS error: {e}")
            return None
        
    def text_to_speech_Audio(self, text: str, voice_name: str = "Kore"):
        """
        Generate speech audio using Gemini TTS with two prebuilt voices.
        Returns raw PCM bytes (for st.audio or saving as .wav).
        The input text should include speaker names like:
        "Joe: Hi Jane!\nJane: Hello Joe!"
        """
        from google import genai
        from google.genai import types
        self.tts = genai.Client(api_key="")
        self.tts_model = "gemini-2.5-flash-preview-tts"
        try:
            response = self.tts.models.generate_content(
                model=self.tts_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=[
                                types.SpeakerVoiceConfig(
                                    speaker="Joe",
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                            voice_name=voice_name  # Joe's voice (configurable)
                                        )
                                    )
                                ),
                                types.SpeakerVoiceConfig(
                                    speaker="Jane",
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                            voice_name="Puck"  # Jane's voice
                                        )
                                    )
                                ),
                            ]
                        )
                    )
                )
            )

            # Extract audio bytes
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data is not None:
                        print(f"✅ Dual-voice audio generated successfully for text:\n{text}")
                        return part.inline_data.data

            raise RuntimeError("No audio data found in Gemini response")

        except Exception as e:
            print(f"🔈 TTS error: {e}")
            return None
    # def text_to_speech(self, text: str):
    #     """
    #     Generate speech audio using Gemini (v0.8.5).
    #     Uses default voice and settings.
    #     Returns raw audio bytes for st.audio().
    #     """
    #     try:
    #         response = self.tts.generate_content(
    #             [text],
    #             generation_config={
    #                 "response_modalities": ["AUDIO"],
    #                 "voice_config": {
    #                 "prebuilt_voice_config": {
    #                     "voice_name": "CHARLIE"  
    #                 }
    #                 }
    #             }
    #         )

    #         # Extract inline audio data
    #         if response.candidates:
    #             for part in response.candidates[0].content.parts:
    #                 if hasattr(part, "inline_data") and part.inline_data is not None:
    #                     print(f"✅ Audio generated successfully.{text} .. text finished!!")
    #                     return part.inline_data.data

    #         raise RuntimeError("No audio data found in Gemini response")

    #     except Exception as e:
    #         print(f"🔈 TTS error: {e}")
    #         return None

    # def text_to_speech(self, text: str):
    #     try:
    #         tts_model = genai.GenerativeModel(self.tts_model)
    #         response = tts_model.generate_content(
    #             [text],
    #             generation_config=GenerationConfig(
    #                 response_mime_type="audio/wav"
    #             )
    #         )

    #         if response.candidates:
    #             for part in response.candidates[0].content.parts:
    #                 if hasattr(part, "inline_data") and part.inline_data:
    #                     print(f"✅ Audio generated successfully.")
    #                     return part.inline_data.data

    #         raise RuntimeError("No audio data found in Gemini response")

    #     except Exception as e:
    #         print(f"🔈 TTS error: {e}")
    #         return None

    # def show_chat_history(self):
    #     return self.chat_history