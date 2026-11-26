
import streamlit as st
import fitz
import io
import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    from google import genai
except Exception:
    genai = None

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✨",
    layout="wide"
)

st.title("✨ NOVA AI")
st.caption("Your Personal AI Assistant")

# ---------------- GEMINI SETUP ----------------

gemini_key = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

gemini_client = None

if gemini_key and genai is not None:
    try:
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception:
        gemini_client = None


def ask_gemini(prompt):
    if gemini_client is None:
        return "Please configure GEMINI_API_KEY in Streamlit Secrets."

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text or "No response received."

    except Exception as e:
        return f"AI Error: {e}"


# ---------------- SESSION STATE ----------------

if "nova_messages" not in st.session_state:
    st.session_state.nova_messages = []

if "nova_pdf_text" not in st.session_state:
    st.session_state.nova_pdf_text = ""


# ---------------- TABS ----------------

chat_tab, pdf_tab, photo_tab = st.tabs(
    ["💬 AI Chat", "📄 PDF Assistant", "🎨 Free Photo Editor"]
)


# ---------------- AI CHAT ----------------

with chat_tab:

    st.subheader("💬 Chat with NOVA")

    for message in st.session_state.nova_messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input(
        "Ask NOVA anything...",
        key="nova_chat_input"
    )

    if user_input:

        st.session_state.nova_messages.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        history = "\n".join(
            f'{m["role"]}: {m["content"]}'
            for m in st.session_state.nova_messages[-12:]
        )

        with st.chat_message("assistant"):

            with st.spinner("NOVA is thinking..."):
                answer = ask_gemini(history)

            st.markdown(answer)

        st.session_state.nova_messages.append(
            {"role": "assistant", "content": answer}
        )

    if st.button("🗑️ Clear Chat", key="clear_nova_chat"):

        st.session_state.nova_messages = []
        st.rerun()


# ---------------- PDF ASSISTANT ----------------

with pdf_tab:

    st.subheader("📄 PDF Assistant")

    pdf_file = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="nova_pdf_upload"
    )

    if pdf_file is not None:

        try:

            pdf_doc = fitz.open(
                stream=pdf_file.read(),
                filetype="pdf"
            )

            extracted_text = "\n\n".join(
                page.get_text() for page in pdf_doc
            )

            st.session_state.nova_pdf_text = extracted_text

            st.success(f"PDF loaded: {len(pdf_doc)} pages")

            with st.expander("Preview PDF text"):
                st.text(extracted_text[:5000])

        except Exception as e:
            st.error(f"PDF Error: {e}")

    pdf_question = st.text_area(
        "Ask a question about your PDF",
        key="nova_pdf_question"
    )

    if st.button("🔎 Ask PDF", key="nova_pdf_ask"):

        if not st.session_state.nova_pdf_text:
            st.warning("Please upload a PDF first.")

        elif not pdf_question.strip():
            st.warning("Please type a question.")

        else:

            prompt = (
                "Answer the question using the PDF text below. "
                "If the answer is not in the PDF, say so.\n\n"
                "PDF TEXT:\n"
                + st.session_state.nova_pdf_text[:100000]
                + "\n\nQUESTION:\n"
                + pdf_question
            )

            with st.spinner("Reading PDF..."):
                answer = ask_gemini(prompt)

            st.markdown(answer)


# ---------------- FREE PHOTO EDITOR ----------------

with photo_tab:

    st.subheader("🎨 NOVA Free Photo Editor")

    st.info(
        "Edit your photos without a paid photo editing API."
    )

    uploaded_photo = st.file_uploader(
        "📷 Upload your photo",
        type=["png", "jpg", "jpeg", "webp"],
        key="nova_free_photo_upload"
    )

    if uploaded_photo is not None:

        try:

            original = Image.open(uploaded_photo).convert("RGB")

            st.image(
                original,
                caption="Original Photo",
                use_container_width=True
            )

            st.subheader("⚙️ Editing Tools")

            brightness = st.slider(
                "☀️ Brightness",
                0.0, 3.0, 1.0, 0.05,
                key="nova_brightness"
            )

            contrast = st.slider(
                "🌓 Contrast",
                0.0, 3.0, 1.0, 0.05,
                key="nova_contrast"
            )

            saturation = st.slider(
                "🌈 Saturation",
                0.0, 3.0, 1.0, 0.05,
                key="nova_saturation"
            )

            sharpness = st.slider(
                "🔍 Sharpness",
                0.0, 3.0, 1.0, 0.05,
                key="nova_sharpness"
            )

            rotation = st.selectbox(
                "🔄 Rotate",
                [0, 90, 180, 270],
                key="nova_rotation"
            )

            flip_horizontal = st.checkbox(
                "↔️ Flip Horizontally",
                key="nova_flip_h"
            )

            flip_vertical = st.checkbox(
                "↕️ Flip Vertically",
                key="nova_flip_v"
            )

            effect = st.selectbox(
                "🎨 Filter",
                [
                    "None",
                    "Black & White",
                    "Sepia",
                    "Blur",
                    "Vintage"
                ],
                key="nova_filter"
            )

            # Apply adjustments

            edited = ImageEnhance.Brightness(
                original
            ).enhance(brightness)

            edited = ImageEnhance.Contrast(
                edited
            ).enhance(contrast)

            edited = ImageEnhance.Color(
                edited
            ).enhance(saturation)

            edited = ImageEnhance.Sharpness(
                edited
            ).enhance(sharpness)

            if rotation != 0:
                edited = edited.rotate(
                    rotation,
                    expand=True
                )

            if flip_horizontal:
                edited = ImageOps.mirror(edited)

            if flip_vertical:
                edited = ImageOps.flip(edited)

            # Apply filters

            if effect == "Black & White":

                edited = ImageOps.grayscale(
                    edited
                ).convert("RGB")

            elif effect == "Sepia":

                gray = ImageOps.grayscale(edited)

                edited = ImageOps.colorize(
                    gray,
                    "#3b2515",
                    "#f2dfb5"
                ).convert("RGB")

            elif effect == "Blur":

                edited = edited.filter(
                    ImageFilter.GaussianBlur(radius=2)
                )

            elif effect == "Vintage":

                gray = ImageOps.grayscale(edited)

                edited = ImageOps.colorize(
                    gray,
                    "#2b2118",
                    "#e6c99a"
                ).convert("RGB")

                edited = ImageEnhance.Contrast(
                    edited
                ).enhance(0.85)

            # Preview

            st.subheader("✨ Edited Photo")

            st.image(
                edited,
                use_container_width=True
            )

            # Download

            output = io.BytesIO()

            edited.save(
                output,
                format="JPEG",
                quality=95
            )

            st.download_button(
                "⬇️ Download Edited Photo",
                data=output.getvalue(),
                file_name="nova_edited_photo.jpg",
                mime="image/jpeg",
                key="nova_download_photo"
            )

        except Exception as e:

            st.error(f"Photo Editor Error: {e}")


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "✨ NOVA AI | Free Photo Editing Tools"
)
