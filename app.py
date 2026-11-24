
import streamlit as st
import fitz
from google import genai
from supabase import create_client

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✨",
    layout="wide"
)

st.title("✨ NOVA AI")
st.caption("Your personal AI assistant")

# ---------- CONNECTIONS ----------

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    gemini = genai.Client(api_key=GEMINI_API_KEY)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

except Exception as e:
    st.error("Connection settings check karo. Streamlit Secrets mein API keys verify karo.")
    st.stop()

MODEL = "gemini-2.5-flash"

# ---------- SESSION ----------

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# Restore Supabase session
if st.session_state.access_token and st.session_state.refresh_token:
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_id = None

# ---------- AUTHENTICATION ----------


{extra_context}

USER QUESTION:
{prompt}
"""

    response = gemini.models.generate_content(
        model=MODEL,
        contents=full_prompt
    )

    return response.text or "Mujhe abhi jawab nahi mil paaya."

# ---------- CHAT MODES ----------

mode = st.radio(
    "Choose Assistant",
    ["General Chat", "PDF Assistant"],
    horizontal=True
)

if mode == "General Chat":

    st.subheader("💬 Chat with NOVA")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("NOVA se kuch bhi poochho...")

    if user_prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt
        })

        # Basic trigger-based automatic memory
        triggers = [
            "remember that",
            "please remember",
            "yaad rakhna",
            "yaad rakh lo",
            "meri preference hai"
        ]

        if any(t in user_prompt.lower() for t in triggers):
            save_memory(user_prompt, "automatic")

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("NOVA soch raha hai..."):
                    answer = ask_ai(user_prompt)

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"AI response error: {e}")

elif mode == "PDF Assistant":

    st.subheader("📄 Chat with your PDF")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_file:
        try:
            document = fitz.open(stream=uploaded_file.read(), filetype="pdf")

            st.session_state.pdf_text = "\n".join(
                page.get_text() for page in document
            )

            st.success("PDF successfully loaded!")

        except Exception as e:
            st.error(f"PDF read nahi ho paayi: {e}")

    pdf_question = st.chat_input("PDF ke baare mein sawaal poochho...")

    if pdf_question:

        if not st.session_state.pdf_text:
            st.warning("Pehle PDF upload karo.")

        else:
            with st.spinner("PDF padhkar jawab bana raha hoon..."):
                try:
                    answer = ask_ai(
                        pdf_question,
                        extra_context=st.session_state.pdf_text[:30000]
                    )

                    st.markdown(answer)

                except Exception as e:
                    st.error(f"PDF assistant error: {e}")

st.divider()
st.caption("NOVA AI • Built with Streamlit, Gemini and Supabase")
