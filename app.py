
import streamlit as st
import fitz
import json
import uuid
from datetime import datetime
from google import genai
from streamlit_local_storage import LocalStorage

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✨",
    layout="wide"
)

# ==========================================
# GEMINI API
# ==========================================

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("GEMINI_API_KEY missing in Streamlit Secrets.")
    st.stop()

gemini = genai.Client(api_key=GEMINI_API_KEY)

from openai import OpenAI

openai_client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)
# ========================================== 
# GEMINI AUTO FALLBACK
# ==========================================

import time

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

def generate_with_fallback(contents):
    errors = []

    for model_name in GEMINI_MODELS:
        for attempt in range(2):
            try:
                result = gemini.models.generate_content(
                    model=model_name,
                    contents=contents
                )

                if result.text:
                    return result.text

                errors.append(f"{model_name}: Empty response")
                break

            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                time.sleep(2 + attempt * 3)

    raise RuntimeError(
        "All models failed. " + " | ".join(errors)
    )
# ==========================================
# BROWSER LOCAL STORAGE
# ==========================================

localS = LocalStorage()
STORAGE_KEY = "nova_ai_saved_data"

if "storage_loaded" not in st.session_state:
    saved_data = localS.getItem(STORAGE_KEY)

    if isinstance(saved_data, str):
        try:
            saved_data = json.loads(saved_data)
        except Exception:
            saved_data = {}

    if not isinstance(saved_data, dict):
        saved_data = {}

    st.session_state.messages = saved_data.get("messages", [])
    st.session_state.memories = saved_data.get("memories", [])
    st.session_state.storage_loaded = True

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memories" not in st.session_state:
    st.session_state.memories = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ==========================================
# SAVE DATA
# ==========================================

def save_browser_data():
    data = {
        "messages": st.session_state.messages,
        "memories": st.session_state.memories
    }

    localS.setItem(
        STORAGE_KEY,
        json.dumps(data, ensure_ascii=False)
    )


# ==========================================
# MEMORY FUNCTIONS
# ==========================================

def save_memory(content, memory_type="manual"):
    content = content.strip()

    if not content:
        return False

    # Avoid duplicate memories
    for memory in st.session_state.memories:
        if memory.get("content", "").lower() == content.lower():
            return False

    st.session_state.memories.insert(0, {
        "id": str(uuid.uuid4()),
        "content": content,
        "memory_type": memory_type,
        "created_at": datetime.now().isoformat()
    })

    save_browser_data()
    return True


def delete_memory(memory_id):
    st.session_state.memories = [
        memory for memory in st.session_state.memories
        if memory.get("id") != memory_id
    ]
    save_browser_data()


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

    st.caption("NOVA can remember important things about you.")

    memory_input = st.text_area(
        "What should NOVA remember?",
        placeholder="Example: I love learning new technology."
    )

    if st.button("Save Memory", use_container_width=True):
        if save_memory(memory_input):
            st.success("Memory saved!")
            st.rerun()
        else:
            st.info("This memory is empty or already saved.")

    st.divider()
    st.subheader("Your Saved Memories")

    if st.session_state.memories:
        for memory in st.session_state.memories:

            with st.expander(
                memory.get("content", "Saved memory")[:45]
            ):
                st.write(memory.get("content", ""))

                if st.button(
                    "Delete Memory",
                    key="delete_" + memory["id"]
                ):
                    delete_memory(memory["id"])
                    st.rerun()
    else:
        st.caption("No memories saved yet.")

    st.divider()

    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        save_browser_data()
        st.rerun()

    st.caption("Memories remain saved when chat history is cleared.")

# ==========================================
# TABS
# ==========================================

chat_tab, pdf_tab = st.tabs([
    "💬 AI Chat",
    "📄 PDF Assistant"
])

# ==========================================
# AI CHAT
# ==========================================

with chat_tab:

    st.subheader("Chat with NOVA")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask NOVA anything...")

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        save_browser_data()

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
            "You are NOVA AI, a friendly and helpful personal assistant. "
            "Speak naturally in the language the user uses. "
            "Use saved memories when relevant. "
            "Never pretend to remember information that is not provided. "
            "If the user asks you to remember something, acknowledge it. "
            "Do not claim a memory was saved unless the app confirms it.\n\n"
            "USER MEMORIES:\n"
            + memory_context
            + "\n\nRECENT CONVERSATION:\n"
            + conversation
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

            save_browser_data()

            lower_prompt = prompt.lower()

            triggers = [
                "remember that",
                "remember this",
                "yaad rakhna",
                "ise yaad rakhna",
                "याद रखना"
            ]

            if any(trigger in lower_prompt for trigger in triggers):

                if save_memory(prompt, "automatic"):
                    st.toast("🧠 NOVA saved this memory!")

        except Exception as e:

            st.error(
                "NOVA could not respond right now. "
                "Please try again later."
            )

            st.caption(str(e))
# ==========================================
# PDF ASSISTANT
# ==========================================

with pdf_tab:

    st.subheader("Ask questions about your PDF")

    uploaded_pdf = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"]
    )

    if uploaded_pdf:

        try:

            document = fitz.open(
                stream=uploaded_pdf.read(),
                filetype="pdf"
            )

            extracted_text = "\n".join(
                page.get_text()
                for page in document
            )

            if not extracted_text.strip():

                st.warning(
                    "No readable text found. "
                    "This may be a scanned PDF."
                )

            else:

                st.session_state.pdf_text = extracted_text

                st.success(
                    "PDF uploaded and text extracted."
                )

        except Exception as e:

            st.error(
                "PDF reading failed: " + str(e)
            )

    if st.session_state.pdf_text:

        st.caption(
            f"Extracted text: "
            f"{len(st.session_state.pdf_text)} characters"
        )

        pdf_question = st.text_input(
            "Ask something about this PDF",
            key="nova_pdf_question"
        )

        if st.button("Ask NOVA about PDF"):

            if pdf_question.strip():

                try:

                    with st.spinner("Reading your PDF..."):

                        pdf_prompt = (
                            "Answer the question using the PDF text. "
                            "If the answer is not in the PDF, say so.\n\n"
                            "PDF TEXT:\n"
                            + st.session_state.pdf_text[:80000]
                            + "\n\nQUESTION:\n"
                            + pdf_question
                        )

                        answer = generate_with_fallback(
                            pdf_prompt
                        )

                    st.markdown("### NOVA's Answer")

                    st.write(answer)

                except Exception as e:

                    st.error(
                        "NOVA could not answer from the PDF "
                        "right now. Please try again later."
                    )

                    st.caption(str(e))

        if st.button("Clear PDF"):

            st.session_state.pdf_text = ""

            st.rerun()
# ==========================================
# FOOTER
# ==========================================

st.divider()
st.caption("NOVA AI • Your Personal AI Assistant ✨") 
