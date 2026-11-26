
import streamlit as st
import fitz
from google import genai
from openai import OpenAI

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")

st.title("✨ NOVA AI")
st.caption("AI Chat and PDF Assistant")

# API clients
gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

openai_client = None
if st.secrets.get("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

# Gemini models: try in order
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

def get_ai_response(prompt, history=None):
    history = history or []

    conversation = ""
    for item in history[-10:]:
        conversation += f"\n{item['role']}: {item['content']}\n"

    full_prompt = (
        "You are NOVA AI, a helpful and friendly AI assistant. "
        "Answer clearly and helpfully.\n\n"
        + conversation
        + "\nUser: "
        + prompt
    )

    # Try Gemini models first
    errors = []

    for model_name in GEMINI_MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )

            if response.text:
                return response.text, f"Gemini ({model_name})"

        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")

    # OpenAI fallback if Gemini models fail
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are NOVA AI, a helpful and friendly AI assistant."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )

            answer = response.choices[0].message.content
            if answer:
                return answer, "OpenAI fallback"

        except Exception as e:
            errors.append(f"OpenAI: {str(e)}")

    return (
        "Sorry, abhi AI response nahi mil paaya.\n\n"
        + "\n".join(errors[-3:]),
        "Error"
    )

# Tabs
chat_tab, pdf_tab = st.tabs(["💬 AI Chat", "📄 PDF Assistant"])

# AI Chat
with chat_tab:
    st.subheader("💬 Chat with NOVA")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Message NOVA AI...", key="nova_chat_input")

    if user_prompt:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_prompt}
        )

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer, provider = get_ai_response(
                    user_prompt,
                    st.session_state.chat_history[:-1]
                )
            st.markdown(answer)
            st.caption(f"Powered by {provider}")

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )

    if st.button("🗑️ Clear Chat", key="clear_nova_chat"):
        st.session_state.chat_history = []
        st.rerun()

# PDF Assistant
with pdf_tab:
    st.subheader("📄 Ask questions about your PDF")

    uploaded_pdf = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="nova_pdf_upload"
    )

    if uploaded_pdf:
        if st.session_state.pdf_name != uploaded_pdf.name:
            try:
                doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
                extracted_text = "\n".join(
                    page.get_text() for page in doc
                )

                st.session_state.pdf_text = extracted_text
                st.session_state.pdf_name = uploaded_pdf.name

            except Exception as e:
                st.error(f"PDF read error: {e}")

        if st.session_state.pdf_text:
            st.success(f"PDF loaded: {uploaded_pdf.name}")
            st.caption(
                f"Extracted text: {len(st.session_state.pdf_text)} characters"
            )

            pdf_question = st.text_input(
                "Ask something about this PDF",
                key="nova_pdf_question"
            )

            if st.button("Ask NOVA", key="nova_pdf_ask"):
                if pdf_question.strip():
                    pdf_prompt = (
                        "Answer the question using the following PDF text. "
                        "If the answer is not in the document, say so.\n\n"
                        "PDF CONTENT:\n"
                        + st.session_state.pdf_text[:100000]
                        + "\n\nQUESTION:\n"
                        + pdf_question
                    )

                    with st.spinner("Reading PDF and answering..."):
                        answer, provider = get_ai_response(pdf_prompt)

                    st.markdown("### Answer")
                    st.markdown(answer)
                    st.caption(f"Powered by {provider}")

                else:
                    st.warning("Please enter a question first.")

    else:
        st.info("Upload a PDF to get started.")

# Footer
st.divider()
st.caption("✨ NOVA AI | AI Chat + PDF Assistant")
