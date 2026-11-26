import streamlit as st
import fitz
import io
import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    from google import genai
except Exception:
    genai = None

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")
st.title("✨ NOVA AI")
st.caption("Chat, PDF Assistant and Free Photo Editor")

# Gemini fallback models, newest first
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
client = None
if api_key and genai is not None:
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        client = None

def ask_gemini(prompt):
    if client is None:
        return "Gemini API is not configured. Add GEMINI_API_KEY in Streamlit Secrets."
    errors = []
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            answer = getattr(response, "text", None)
            if answer:
                return answer
            errors.append(f"{model_name}: empty response")
        except Exception as e:
            errors.append(f"{model_name}: {str(e)[:250]}")
    return "All Gemini fallback models failed. Errors:\n\n" + "\n\n".join(errors)

if "nova_messages" not in st.session_state:
    st.session_state.nova_messages = []
if "nova_pdf_text" not in st.session_state:
    st.session_state.nova_pdf_text = ""

chat_tab, pdf_tab, photo_tab = st.tabs(["💬 AI Chat", "📄 PDF Assistant", "🎨 Free Photo Editor"])

with chat_tab:
    st.subheader("Chat with NOVA")
    for message in st.session_state.nova_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    chat_input = st.chat_input("Ask NOVA anything...", key="nova_chat_input")
    if chat_input:
        st.session_state.nova_messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)
        history = "\n".join(f'{m["role"].capitalize()}: {m["content"]}' for m in st.session_state.nova_messages[-12:])
        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking (trying Gemini fallback models)..."):
                answer = ask_gemini(history)
            st.markdown(answer)
        st.session_state.nova_messages.append({"role": "assistant", "content": answer})
    if st.button("🗑️ Clear chat", key="nova_clear_chat"):
        st.session_state.nova_messages = []
        st.rerun()

with pdf_tab:
    st.subheader("PDF Assistant")
    pdf_file = st.file_uploader("Upload a PDF", type=["pdf"], key="nova_pdf_upload")
    if pdf_file is not None:
        try:
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            text = "\n\n".join(page.get_text() for page in doc)
            st.session_state.nova_pdf_text = text
            st.success(f"PDF loaded: {len(doc)} pages")
            if text.strip():
                with st.expander("Preview extracted text"):
                    st.text(text[:5000])
            else:
                st.warning("No text extracted. This may be a scanned PDF.")
        except Exception as e:
            st.error(f"PDF reading error: {e}")
    question = st.text_area("Ask a question about your PDF", key="nova_pdf_question")
    if st.button("🔎 Ask PDF", key="nova_pdf_ask"):
        if not st.session_state.nova_pdf_text.strip():
            st.warning("Upload a PDF with readable text first.")
        elif not question.strip():
            st.warning("Please enter a question.")
        else:
            prompt = ("Answer the question using only the PDF text below. If the answer is not in the text, say so.\n\nPDF TEXT:\n" + st.session_state.nova_pdf_text[:100000] + "\n\nQUESTION:\n" + question)
            with st.spinner("NOVA is reading the PDF (trying Gemini fallback models)..."):
                answer = ask_gemini(prompt)
            st.markdown(answer)

with photo_tab:
    st.subheader("🎨 Free Photo Editor")
    st.info("Photo adjustments and filters are processed locally. No paid photo-editing API.")
    photo_file = st.file_uploader("Upload your photo", type=["png", "jpg", "jpeg", "webp"], key="nova_free_photo_upload")
    if photo_file is not None:
        try:
            original = Image.open(photo_file).convert("RGB")
            st.image(original, caption="Original Photo", use_container_width=True)
            brightness = st.slider("Brightness", 0.0, 3.0, 1.0, 0.05, key="nova_brightness")
            contrast = st.slider("Contrast", 0.0, 3.0, 1.0, 0.05, key="nova_contrast")
            saturation = st.slider("Saturation", 0.0, 3.0, 1.0, 0.05, key="nova_saturation")
            sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.05, key="nova_sharpness")
            rotation = st.selectbox("Rotate", [0, 90, 180, 270], key="nova_rotation")
            flip_h = st.checkbox("Flip horizontally", key="nova_flip_h")
            flip_v = st.checkbox("Flip vertically", key="nova_flip_v")
            effect = st.selectbox("Filter", ["None", "Black & White", "Sepia", "Blur", "Vintage"], key="nova_filter")
            edited = ImageEnhance.Brightness(original).enhance(brightness)
            edited = ImageEnhance.Contrast(edited).enhance(contrast)
            edited = ImageEnhance.Color(edited).enhance(saturation)
            edited = ImageEnhance.Sharpness(edited).enhance(sharpness)
            if rotation:
                edited = edited.rotate(rotation, expand=True)
            if flip_h:
                edited = ImageOps.mirror(edited)
            if flip_v:
                edited = ImageOps.flip(edited)
            if effect == "Black & White":
                edited = ImageOps.grayscale(edited).convert("RGB")
            elif effect == "Sepia":
                edited = ImageOps.colorize(ImageOps.grayscale(edited), "#3b2515", "#f2dfb5").convert("RGB")
            elif effect == "Blur":
                edited = edited.filter(ImageFilter.GaussianBlur(radius=2))
            elif effect == "Vintage":
                edited = ImageOps.colorize(ImageOps.grayscale(edited), "#2b2118", "#e6c99a").convert("RGB")
                edited = ImageEnhance.Contrast(edited).enhance(0.85)
            st.subheader("Edited Photo")
            st.image(edited, use_container_width=True)
            output = io.BytesIO()
            edited.save(output, format="JPEG", quality=95)
            st.download_button("⬇️ Download Edited Photo", data=output.getvalue(), file_name="nova_edited_photo.jpg", mime="image/jpeg", key="nova_download_photo")
        except Exception as e:
            st.error(f"Photo Editor error: {e}")

st.divider()
st.caption("NOVA AI • Gemini fallback for Chat/PDF • Local free photo tools")

