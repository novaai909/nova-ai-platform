
import streamlit as st
import fitz
import uuid
import base64
from datetime import datetime
from google import genai
from openai import OpenAI

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✨",
    layout="wide"
)

# ==========================================
# API SETUP
# ==========================================

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    gemini = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    st.error("GEMINI_API_KEY missing in Secrets.")
    st.stop()

openai_client = None

try:
    if st.secrets.get("OPENAI_API_KEY"):
        openai_client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )
except Exception:
    openai_client = None

# ==========================================
# GEMINI TEXT GENERATION
# ==========================================

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]

def generate_with_fallback(contents):

    errors = []

    for model_name in GEMINI_MODELS:

        try:

            result = gemini.models.generate_content(
                model=model_name,
                contents=contents
            )

            if result.text:
                return result.text

        except Exception as e:

            errors.append(
                model_name + ": " + str(e)
            )

    raise RuntimeError(
        "Gemini failed: " + " | ".join(errors)
    )

# ==========================================
# SESSION STATE
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memories" not in st.session_state:
    st.session_state.memories = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ==========================================
# MEMORY FUNCTIONS
# ==========================================

def save_memory(content, memory_type="manual"):

    content = content.strip()

    if not content:
        return False

    for memory in st.session_state.memories:

        if memory["content"].lower() == content.lower():
            return False

    st.session_state.memories.insert(0, {
        "id": str(uuid.uuid4()),
        "content": content,
        "memory_type": memory_type,
        "created_at": datetime.now().isoformat()
    })

    return True


def delete_memory(memory_id):

    st.session_state.memories = [
        memory
        for memory in st.session_state.memories
        if memory["id"] != memory_id
    ]

# ==========================================
# HEADER
# ==========================================

st.title("✨ NOVA AI")
st.caption("Your Personal AI Assistant • Always Here for You")

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("🧠 NOVA Memory")

    memory_input = st.text_area(
        "What should NOVA remember?",
        placeholder="Example: I love learning technology.",
        key="nova_memory_input"
    )

    if st.button(
        "Save Memory",
        key="nova_save_memory",
        use_container_width=True
    ):

        if save_memory(memory_input):
            st.success("Memory saved!")
            st.rerun()
        else:
            st.info("Empty or duplicate memory.")

    st.divider()

    st.subheader("Saved Memories")

    if st.session_state.memories:

        for memory in st.session_state.memories:

            with st.expander(
                memory["content"][:45],
                key="memory_exp_" + memory["id"]
            ):

                st.write(memory["content"])

                if st.button(
                    "Delete Memory",
                    key="memory_del_" + memory["id"]
                ):

                    delete_memory(memory["id"])
                    st.rerun()

    else:

        st.caption("No memories saved yet.")

    st.divider()

    if st.button(
        "Clear Chat History",
        key="nova_clear_chat"
    ):

        st.session_state.messages = []
        st.rerun()

    if st.button(
        "Clear All Memories",
        key="nova_clear_memories"
    ):

        st.session_state.memories = []
        st.rerun()

# ==========================================
# TABS
# ==========================================

chat_tab, pdf_tab, photo_tab = st.tabs([
    "💬 AI Chat",
    "📄 PDF Assistant",
    "🎨 Photo Editor"
])

# ==========================================
# AI CHAT
# ==========================================

with chat_tab:

    st.subheader("Chat with NOVA")

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask NOVA anything...",
        key="nova_chat_input"
    )

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        memory_context = "\n".join(
            memory["content"]
            for memory in st.session_state.memories
        )

        history = st.session_state.messages[-20:]

        conversation = "\n".join(
            f'{m["role"].upper()}: {m["content"]}'
            for m in history
        )

        system_prompt = (
            "You are NOVA AI, a friendly and helpful assistant. "
            "Speak naturally in the language used by the user. "
            "Use memories when relevant. "
            "Never pretend to remember unavailable information. "
            "Never claim to save memories unless the app confirms it.\n\n"
            "USER MEMORIES:\n" + memory_context +
            "\n\nRECENT CONVERSATION:\n" + conversation
        )

        try:

            with st.chat_message("assistant"):

                with st.spinner("NOVA is thinking..."):

                    answer = generate_with_fallback(
                        system_prompt
                    )

                st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            triggers = [
                "remember that",
                "remember this",
                "yaad rakhna",
                "ise yaad rakhna",
                "याद रखना"
            ]

            if any(
                trigger in prompt.lower()
                for trigger in triggers
            ):

                if save_memory(prompt, "automatic"):
                    st.toast("🧠 Memory saved!")

        except Exception as e:

            st.error("NOVA could not respond right now.")
            st.caption(str(e))

# ==========================================
# PDF ASSISTANT
# ==========================================

with pdf_tab:

    st.subheader("📄 Ask Questions About Your PDF")

    uploaded_pdf = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
        key="nova_pdf_upload"
    )

    if uploaded_pdf:

        try:

            document = fitz.open(
                stream=uploaded_pdf.getvalue(),
                filetype="pdf"
            )

            extracted_text = "\n".join(
                page.get_text()
                for page in document
            )

            if extracted_text.strip():

                st.session_state.pdf_text = extracted_text

                st.success("PDF text extracted successfully!")

            else:

                st.warning(
                    "No readable text found in this PDF."
                )

        except Exception as e:

            st.error("PDF reading failed.")
            st.caption(str(e))

    if st.session_state.pdf_text:

        st.caption(
            "Extracted text: "
            + str(len(st.session_state.pdf_text))
            + " characters"
        )

        pdf_question = st.text_input(
            "Ask something about this PDF",
            key="nova_pdf_question"
        )

        if st.button(
            "Ask NOVA about PDF",
            key="nova_pdf_ask"
        ):

            if pdf_question.strip():

                pdf_prompt = (
                    "Answer using the PDF text. "
                    "If the answer is not in the PDF, say so.\n\n"
                    "PDF TEXT:\n"
                    + st.session_state.pdf_text[:80000]
                    + "\n\nQUESTION:\n"
                    + pdf_question
                )

                try:

                    with st.spinner("Reading PDF..."):

                        answer = generate_with_fallback(
                            pdf_prompt
                        )

                    st.markdown("### NOVA's Answer")
                    st.write(answer)

                except Exception as e:

                    st.error("PDF response failed.")
                    st.caption(str(e))

        if st.button(
            "Clear PDF",
            key="nova_pdf_clear"
        ):

            st.session_state.pdf_text = ""
            st.rerun()

# ==========================================
# AI PHOTO EDITOR
# ==========================================

with photo_tab:

    st.subheader("🎨 NOVA AI Photo Editor")

    st.caption(
        "Upload a photo and tell NOVA how you want to edit it."
    )

    photo_file = st.file_uploader(
        "Upload your photo",
        type=["png", "jpg", "jpeg", "webp"],
        key="nova_photo_upload"
    )

    if photo_file:

        st.image(
            photo_file,
            caption="Original Photo",
            use_container_width=True
        )

        edit_prompt = st.text_area(
            "Describe your photo edit",
            placeholder=(
                "Example: Change the background to a beach "
                "at sunset and add cinematic lighting."
            ),
            key="nova_photo_edit_prompt"
        )

        if st.button(
            "✨ Edit My Photo",
            key="nova_photo_edit"
        ):

            if not edit_prompt.strip():

                st.warning("Please enter an editing prompt.")

            elif openai_client is None:

                st.error(
                    "OPENAI_API_KEY is missing in Streamlit Secrets."
                )

            else:

                try:

                    with st.spinner(
                        "NOVA is editing your photo... ✨"
                    ):

                        result = openai_client.images.edit(
                            model="gpt-image-2.6-flare",
                            image=(
                                photo_file.name,
                                photo_file.getvalue(),
                                photo_file.type
                            ),
                            prompt=edit_prompt
                        )

                        edited_bytes = base64.b64decode(
                            result.data[0].b64_json
                        )

                    st.success("Photo edited successfully!")

                    st.image(
                        edited_bytes,
                        caption="NOVA AI Edited Photo",
                        use_container_width=True
                    )

                    st.download_button(
                        "⬇️ Download Edited Photo",
                        data=edited_bytes,
                        file_name="nova_edited_photo.png",
                        mime="image/png",
                        key="nova_photo_download"
                    )

                except Exception as e:

                    st.error("Photo editing failed.")
                    st.caption(str(e))

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "NOVA AI • Your Personal AI Assistant ✨"
)
