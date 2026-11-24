
import streamlit as st
import fitz
from google import genai
from supabase import create_client, AuthClientOptions

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✨",
    layout="wide"
)

st.title("✨ NOVA AI")
st.caption("Your Personal AI Assistant")

# ==========================================
# SESSION DEFAULTS
# ==========================================

defaults = {
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "messages": [],
    "pdf_text": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# SUPABASE AUTH STORAGE
# ==========================================

# PKCE verifier ko Streamlit session mein rakhta hai.
if "_supabase_auth_storage" not in st.session_state:
    st.session_state["_supabase_auth_storage"] = {}


class StreamlitAuthStorage:
    def __init__(self, storage):
        self.storage = storage

    def get_item(self, key):
        return self.storage.get(key)

    def set_item(self, key, value):
        self.storage[key] = value

    def remove_item(self, key):
        self.storage.pop(key, None)


auth_storage = StreamlitAuthStorage(
    st.session_state["_supabase_auth_storage"]
)

# ==========================================
# API CONNECTIONS
# ==========================================

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    gemini = genai.Client(api_key=GEMINI_API_KEY)

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
        auth=AuthClientOptions(
            flow_type="pkce",
            session_storage=auth_storage
        )
    )

except Exception as e:
    st.error("API settings ya Supabase configuration check karo.")
    st.error(str(e))
    st.stop()

MODEL = "gemini-2.5-flash"

# ==========================================
# SAVE LOGIN SESSION
# ==========================================

def save_session(session):
    if not session:
        return False

    try:
        user_response = supabase.auth.get_user(
            session.access_token
        )

        user = user_response.user

        if not user:
            return False

        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token
        st.session_state.user_id = user.id

        return True

    except Exception:
        return False


# ==========================================
# GOOGLE OAUTH CALLBACK
# ==========================================

oauth_code = st.query_params.get("code")
oauth_error = st.query_params.get("error_description")

if oauth_error:
    st.query_params.clear()
    st.error("Google Login error: " + str(oauth_error))

elif oauth_code:

    try:
        response = supabase.auth.exchange_code_for_session(
            oauth_code
        )

        if save_session(response.session):
            st.query_params.clear()
            st.rerun()
        else:
            st.query_params.clear()
            st.error("Google login session nahi ban paaya.")

    except Exception as e:
        st.query_params.clear()
        st.error("Google Login failed.")
        st.error(str(e))


# ==========================================
# RESTORE SESSION
# ==========================================

if (
    st.session_state.access_token
    and st.session_state.refresh_token
    and not st.session_state.user_id
):
    try:
        session = supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

        save_session(session)

    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_id = None


# ==========================================
# LOGIN / SIGNUP
# ==========================================

if not st.session_state.user_id:

    st.subheader("🔐 Welcome to NOVA AI")
    st.write("Login to continue using your personal AI assistant.")

    if st.button("🌐 Continue with Google", use_container_width=True):

        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": (
                        "https://nova-ai-platform-vdmjwhqww8hoczjust8oac.streamlit.app"
                    )
                }
            })

            st.link_button(
                "Continue to Google",
                response.url,
                use_container_width=True
            )

        except Exception as e:
            st.error("Google login start nahi hua.")
            st.error(str(e))

    st.divider()

    login_tab, signup_tab = st.tabs([
        "Email Login",
        "Create Account"
    ])

    with login_tab:

        email = st.text_input("Email Address", key="login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", use_container_width=True):

            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if save_session(response.session):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login session nahi ban paaya.")

            except Exception as e:
                st.error("Login failed.")
                st.error(str(e))

    with signup_tab:

        new_email = st.text_input(
            "Email Address",
            key="signup_email"
        )

        new_password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password"
        )

        if st.button("Create Account", use_container_width=True):

            try:
                response = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })

                if response.session:
                    if save_session(response.session):
                        st.success("Account created!")
                        st.rerun()
                    else:
                        st.error("Account bana, lekin session nahi bana.")
                else:
                    st.success(
                        "Account created! Email confirmation complete karke login karo."
                    )

            except Exception as e:
                st.error("Signup failed.")
                st.error(str(e))

    st.stop()


# ==========================================
# MEMORY SYSTEM
# ==========================================

def save_memory(content, memory_type="personal"):

    try:
        supabase.table("memories").insert({
            "user_id": st.session_state.user_id,
            "content": content,
            "memory_type": memory_type
        }).execute()

        return True

    except Exception as e:
        st.error("Memory save nahi hui.")
        st.error(str(e))
        return False


def get_memories():

    try:
        result = (
            supabase.table("memories")
            .select("content,memory_type")
            .eq("user_id", st.session_state.user_id)
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error("Memory load nahi hui.")
        st.error(str(e))
        return []


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("✨ NOVA AI")
    st.success("Logged in successfully")

    st.divider()
    st.subheader("🧠 Personal Memory")

    memory_input = st.text_area(
        "What should NOVA remember?",
        placeholder="Example: I prefer Hindi answers."
    )

    if st.button("Save Memory"):

        if memory_input.strip():
            if save_memory(memory_input.strip()):
                st.success("Memory saved!")
        else:
            st.warning("Pehle memory likho.")

    if st.button("Show My Memories"):

        memories = get_memories()

        if memories:
            for memory in memories:
                st.write("• " + memory["content"])
        else:
            st.info("No memories found.")

    st.divider()

    if st.button("Logout"):

        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        for key, value in defaults.items():
            st.session_state[key] = value

        st.session_state["_supabase_auth_storage"] = {}

        st.rerun()


# ==========================================
# AI RESPONSE SYSTEM
# ==========================================

def ask_ai(prompt, extra_context=""):

    memories = get_memories()

    memory_text = "\n".join(
        [m["content"] for m in memories]
    )

    history = ""

    for message in st.session_state.messages[-10:]:
        history += (
            message["role"].upper()
            + ": "
            + message["content"]
            + "\n"
        )

    full_prompt = f"""
You are NOVA AI, a helpful and intelligent personal AI assistant.

Answer questions clearly and accurately.
Use the user's saved memories when relevant.
Be friendly and helpful.

USER'S SAVED MEMORIES:
{memory_text}

RECENT CHAT HISTORY:
{history}

ADDITIONAL DOCUMENT CONTEXT:
{extra_context}

CURRENT USER QUESTION:
{prompt}
"""

    response = gemini.models.generate_content(
        model=MODEL,
        contents=full_prompt
    )

    return response.text or "Sorry, no response received."


# ==========================================
# MAIN APP MODES
# ==========================================

mode = st.radio(
    "Choose your assistant",
    ["General Chat", "PDF Assistant"],
    horizontal=True
)


# ==========================================
# GENERAL CHAT
# ==========================================

if mode == "General Chat":

    st.subheader("💬 Chat with NOVA")

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask NOVA anything...")

    if user_prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt
        })

        triggers = [
            "remember that",
            "please remember",
            "yaad rakhna",
            "yaad rakh lo",
            "meri preference hai"
        ]

        if any(
            trigger in user_prompt.lower()
            for trigger in triggers
        ):
            save_memory(user_prompt, "automatic")

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            try:
                with st.spinner("NOVA is thinking..."):
                    answer = ask_ai(user_prompt)

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error("AI response failed.")
                st.error(str(e))


# ==========================================
# PDF ASSISTANT
# ==========================================

elif mode == "PDF Assistant":

    st.subheader("📄 Chat with your PDF")

    uploaded_file = st.file_uploader(
        "Upload your PDF file",
        type=["pdf"]
    )

    if uploaded_file:

        try:
            document = fitz.open(
                stream=uploaded_file.read(),
                filetype="pdf"
            )

            st.session_state.pdf_text = "\n".join(
                page.get_text()
                for page in document
            )

            st.success("PDF uploaded successfully!")

        except Exception as e:
            st.error("PDF reading failed.")
            st.error(str(e))

    if st.session_state.pdf_text:

        st.caption("PDF is ready. Ask questions below.")

        pdf_question = st.chat_input(
            "Ask something about your PDF..."
        )

        if pdf_question:

            with st.spinner("Reading PDF and preparing answer..."):

                try:
                    answer = ask_ai(
                        pdf_question,
                        extra_context=st.session_state.pdf_text[:30000]
                    )

                    st.markdown(answer)

                except Exception as e:
                    st.error("PDF answer failed.")
                    st.error(str(e))

    else:
        st.info("Upload a PDF to start asking questions.")


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "✨ NOVA AI | Powered by Gemini, Supabase and Streamlit"
)
