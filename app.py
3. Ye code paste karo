
import streamlit as st
import fitz
from google import genai

st.set_page_config(
    page_title="NOVA AI",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 NOVA AI")
st.subheader("Your Smart AI Assistant")

# Gemini API connection
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API key nahi mili. Streamlit Secrets check karo.")
    st.stop()

MODEL = "gemini-3.8-flash"

# Choose AI mode
mode = st.radio(
    "Choose your mode:",
    ["💬 General Chat", "📄 PDF Assistant"],
    horizontal=False
)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# PDF upload
pdf_text = ""

if mode == "📄 PDF Assistant":
    uploaded_file = st.file_uploader(
        "Upload your PDF",
        type=["pdf"]
    )

    if uploaded_file:
        try:
            pdf = fitz.open(
                stream=uploaded_file.getvalue(),
                filetype="pdf"
            )

            st.success(
                f"PDF loaded! Total pages: {len(pdf)}"
            )

            # Add page numbers to extracted text
            for page_number, page in enumerate(pdf):
                page_content = page.get_text()
                pdf_text += (
                    f"\n[Page {page_number + 1}]\n"
                    f"{page_content}\n"
                )

            if len(pdf_text) > 60000:
                pdf_text = pdf_text[:60000]
                st.warning(
                    "MVP limit: PDF text is limited "
                    "to the first 60,000 characters."
                )

        except Exception as e:
            st.error(f"PDF read error: {e}")

# Show previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ask a question
question = st.chat_input("Ask NOVA AI anything...")

if question:
    if mode == "📄 PDF Assistant" and not pdf_text:
        st.warning("Pehle ek PDF upload karo.")
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        # Build prompt
        if mode == "📄 PDF Assistant":
            prompt = f"""
You are NOVA AI, a helpful PDF assistant.

Answer using the PDF text below.
Mention page numbers when possible.
If the answer is not in the PDF, say so honestly.

PDF TEXT:
{pdf_text}

USER QUESTION:
{question}
"""
        else:
            history = st.session_state.messages[-10:-1]

            conversation = ""
            for item in history:
                conversation += (
                    f'{item["role"]}: {item["content"]}\n'
                )

            prompt = f"""
You are NOVA AI, a friendly and intelligent AI assistant.
Answer questions clearly and helpfully.
You can speak Hindi or English depending on the user.

Conversation:
{conversation}

User: {question}
NOVA AI:
"""

        with st.chat_message("assistant"):
            with st.spinner("NOVA AI is thinking..."):
                try:
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=prompt
                    )

                    answer = response.text or (
                        "Sorry, I could not generate an answer."
                    )

                    st.markdown(answer)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as e:
                    st.error(
                        "AI connection error. "
                        "Please try again."
                    )
                    st.caption(str(e))

st.divider()
st.caption("NOVA AI | Building the future of intelligence 🚀")
