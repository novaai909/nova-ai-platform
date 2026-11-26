
import streamlit as st
import fitz
import uuid
from datetime import datetime
from google import genai

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

gemini = None
openai_client = None

try:
    if st.secrets.get("GEMINI_API_KEY"):
        gemini = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"]
        )
except Exception:
    gemini = None

try:
    if st.secrets.get("OPENAI_API_KEY"):
        from openai import OpenAI
        openai_client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )
except Exception:
    openai_client = None

# ==========================================
# AI FALLBACK
# ==========================================

def generate_answer(prompt):

    errors = []

    # Try Gemini first
    if gemini is not None:

        models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite"
        ]

        for model_name in models:

            try:
                result = gemini.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if result.text:
                    return result.text

            except Exception as e:
                errors.append(
                    "Gemini " + model_name + ": " + str(e)
                )

    # Try OpenAI if Gemini fails
    if openai_client is not None:

        try:
            response = openai_client.responses.create(
                model="gpt-5.5",
                input=prompt
            )

            if response.output_text:
                return response.output_text

        except Exception as e:
            errors.append("OpenAI: " + str(e))

    raise RuntimeError(
        "All AI providers failed. " + " | ".join(errors)
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
        memory for memory in st.session_state.memories
        if memory["id"] != memory_id
    ]

# ==========================================
# HEADER
# ==========================================

st.title("✨ NOVA AI")
st.caption("Your Personal AI Assistant")

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("🧠 NOVA Memory")

    memory_input = st.text_area(
        "What should NOVA remember?",
        key="nova_memory_input",
        placeholder="Example: I love technology."
    )

    if st.button(
        "Save Memory",
        key="nova_save_memory_btn",
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
                memory["content"][:40],
                key="exp_" + memory["id"]
            ):

                st.write(memory["content"])

                if st.button(
                    "Delete Memory",
                    key="del_" + memory["id"]
                ):

                    delete_memory(memory["id"])
                    st.rerun()

    else:
        st.caption("No memories saved.")

    st.divider()

    if st.button(
        "Clear Chat History",
        key="nova_clear_chat_btn",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()

    if st.button(
        "Clear All Memories",
        key="nova_clear_memories_btn",
        use_container_width=True
    ):

        st.session_state.memories = []
        st.rerun()

    st.caption(
        "Memories and chats currently last for this session."
    )

# ==========================================
# TABS
# ==========================================

chat_tab, pdf_tab = st.tabs(
    ["💬 AI Chat", "📄 PDF Assistant"]
)

# ==========================================
# CHAT
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
            "Speak in the language used by the user. "
            "Use the memories when relevant. "
            "Do not pretend to remember anything unavailable. "
            "Do not claim to save memories unless the app saves them.\n\n"
            "MEMORIES:\n" + memory_context +
            "\n\nCONVERSATION:\n" + conversation
        )

        try:

            with st.chat_message("assistant"):

                with st.spinner("NOVA is thinking..."):

                    answer = generate_answer(
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
                    st.toast("Memory saved!")

        except Exception as e:

            st.error(
                "NOVA could not respond right now."
            )

            st.caption(str(e))

# ==========================================
# PDF ASSISTANT
# ==========================================

with pdf_tab:

    st.subheader("PDF Assistant")

    uploaded_pdf = st.file_uploader(
        "Upload PDF",
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

                st.success("PDF text extracted!")

            else:

                st.warning(
                    "No readable text found in this PDF."
                )

        except Exception as e:

            st.error("PDF error: " + str(e))

    if st.session_state.pdf_text:

        st.caption(
            f"Extracted characters: "
            f"{len(st.session_state.pdf_text)}"
        )

        pdf_question = st.text_input(
            "Ask a question about your PDF",
            key="nova_pdf_question"
        )

        if st.button(
            "Ask NOVA",
            key="nova_pdf_ask_btn"
        ):

            if pdf_question.strip():

                pdf_prompt = (
                    "Answer using the PDF text. "
                    "If the answer is not present, say so.\n\n"
                    "PDF:\n"
                    + st.session_state.pdf_text[:80000]
                    + "\n\nQUESTION:\n"
                    + pdf_question
                )

                try:

                    with st.spinner("Reading PDF..."):

                        answer = generate_answer(
                            pdf_prompt
                        )

                    st.markdown("### NOVA's Answer")
                    st.write(answer)

                except Exception as e:

                    st.error(
                        "PDF response failed."
                    )

                    st.caption(str(e))

        if st.button(
            "Clear PDF",
            key="nova_clear_pdf_btn"
        ):

            st.session_state.pdf_text = ""
            st.rerun()

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption("NOVA AI • Your Personal AI Assistant ✨")
