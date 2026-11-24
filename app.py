
import streamlit as st
import fitz
from google import genai
from supabase import create_client
from urllib.parse import urlparse

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
# SECRETS / CONFIGURATION
# ==========================================

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error(
        "API configuration error. Please check GEMINI_API_KEY, "
        "SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets."
    )
    st.stop()

APP_URL = "https://nova-ai-platform-vdmjwhqww8hoczjust8oac.streamlit.app"

# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "user_email": None,
    "messages": [],
    "pdf_text": "",
    "memory_text": "",
    "supabase_client": None,
    "gemini_client": None,
    "auth_error": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# CLIENTS
# ==========================================

# Keep one Supabase client per Streamlit session.
# Its default auth storage keeps the PKCE verifier in memory.
if st.session_state.supabase_client is None:
    st.session_state.supabase_client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

supabase = st.session_state.supabase_client

if st.session_state.gemini_client is None:
    st.session_state.gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

gemini = st.session_state.gemini_client

# ==========================================
# SESSION HELPERS
# ==========================================

def save_session(session):
    if not session:
        return False

    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token

    try:
        user_response = supabase.auth.get_user(
            session.access_token
        )
        user = user_response.user

        if not user:
            return False

        st.session_state.user_id = user.id
        st.session_state.user_email = user.email
        return True

    except Exception:
        return False


def clear_session():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.messages = []
    st.session_state.pdf_text = ""
    st.session_state.memory_text = ""


def restore_session():
    access = st.session_state.access_token
    refresh = st.session_state.refresh_token

    if access and refresh:
        try:
            response = supabase.auth.set_session(
                access,
                refresh
            )

            if response.session:
                return save_session(response.session)

        except Exception:
            clear_session()

    return False


# ==========================================
# GOOGLE OAUTH CALLBACK
# ==========================================

oauth_error = st.query_params.get("error_description")
oauth_code = st.query_params.get("code")

if oauth_error:
    st.error("Google Login error: " + str(oauth_error))
    st.query_params.clear()

elif oauth_code and not st.session_state.user_id:
    try:
        # Do not clear the callback URL before exchanging the code.
        response = supabase.auth.exchange_code_for_session(
            {"auth_code": oauth_code}
        )

        if save_session(response.session):
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Google login session could not be created.")

    except Exception as e:
        st.error("Google Login failed.")
        st.error(str(e))
        st.info(
            "If this is a PKCE verifier error, restart Google Login "
            "in the same browser tab. Do not reuse an old callback URL."
        )

# Restore a previous login if possible.
if not st.session_state.user_id:
    restore_session()

# ==========================================
# AUTH SCREEN
# ==========================================

if not st.session_state.user_id:

    st.subheader("Welcome to NOVA AI")

    login_tab, signup_tab = st.tabs(
        ["Login", "Sign Up"]
    )

    with login_tab:
        email = st.text_input(
            "Email address",
            key="login_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password
                })

                if save_session(response.session):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(
                        "Login session nahi ban paaya. "
                        "Email confirmation check karein."
                    )

            except Exception as e:
                st.error("Login failed: " + str(e))

    with signup_tab:
        new_email = st.text_input(
            "Email address",
            key="signup_email"
        )
        new_password = st.text_input(
            "Create password",
            type="password",
            key="signup_password"
        )

        if st.button("Create Account", use_container_width=True):
            try:
                response = supabase.auth.sign_up({
                    "email": new_email.strip(),
                    "password": new_password
                })

                if response.session and save_session(response.session):
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.success(
                        "Account created. Please verify your email, "
                        "then come back and log in."
                    )

            except Exception as e:
                st.error("Sign Up failed: " + str(e))

    st.divider()
    st.subheader("Or continue with Google")

    if st.button("Continue with Google", use_container_width=True):
        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": APP_URL
                }
            })

            if response.url:
                st.link_button(
                    "Open Google Login",
                    response.url,
                    use_container_width=True
                )
            else:
                st.error("Google login URL was not generated.")

        except Exception as e:
            st.error("Google Login could not start: " + str(e))

    st.stop()

# ==========================================
# LOGGED-IN USER
# ==========================================

st.sidebar.success(
    "Logged in: " + str(st.session_state.user_email)
)

if st.sidebar.button("Logout", use_container_width=True):
    clear_session()
    st.rerun()

# ==========================================
# MEMORY FUNCTIONS
# ==========================================

def load_memories():
    try:
        result = (
            supabase.table("memories")
            .select("id, content, memory_type, created_at")
            .eq("user_id", st.session_state.user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        st.error("Could not load memories: " + str(e))
        return []


def save_memory(content, memory_type="manual"):
    content = content.strip()

    if not content:
        return False

    try:
        supabase.table("memories").insert({
            "user_id": st.session_state.user_id,
            "content": content,
            "memory_type": memory_type
        }).execute()
        return True

    except Exception as e:
        st.error("Memory save failed: " + str(e))
        return False


# ==========================================
# SIDEBAR MEMORY
# ==========================================

st.sidebar.divider()
st.sidebar.subheader("🧠 My Memories")

memory_input = st.sidebar.text_area(
    "What should NOVA remember?",
    key="new_memory"
)

if st.sidebar.button("Save Memory"):
    if save_memory(memory_input):
        st.sidebar.success("Memory saved!")
        st.rerun()

memories = load_memories()

if memories:
    for memory in memories:
        with st.sidebar.expander(
            str(memory.get("content", ""))[:45]
        ):
            st.write(memory.get("content", ""))

            if st.button(
                "Delete this memory",
                key="delete_" + str(memory["id"])
            ):
                try:
                    (
                        supabase.table("memories")
                        .delete()
                        .eq("id", memory["id"])
                        .eq("user_id", st.session_state.user_id)
                        .execute()
                    )
                    st.rerun()
                except Exception as e:
                    st.error("Delete failed: " + str(e))
else:
    st.sidebar.caption("No saved memories yet.")

# ==========================================
# AI CHAT / PDF TABS
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

        with st.chat_message("user"):
            st.markdown(prompt)

        # Include the signed-in user's saved memories.
        current_memories = load_memories()
        memory_context = "\n".join(
            [m["content"] for m in current_memories]
        )

        history = st.session_state.messages[-12:]

        conversation = "\n".join(
            [
                f'{m["role"].upper()}: {m["content"]}'
                for m in history
            ]
        )

        system_prompt = (
            "You are NOVA AI, a helpful personal assistant. "
            "Use the user's saved memories only when relevant. "
            "Do not claim to remember things that are not provided.\n\n"
            "USER MEMORIES:\n"
            + memory_context
            + "\n\nCONVERSATION:\n"
            + conversation
        )

        try:
            with st.chat_message("assistant"):
                with st.spinner("NOVA is thinking..."):
                    result = gemini.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=system_prompt
                    )

                    answer = result.text or "I could not generate a response."
                    st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            # Simple memory trigger: only save when user explicitly asks.
            lower_prompt = prompt.lower()
            triggers = [
                "remember that",
                "remember this",
                "yaad rakhna",
                "ise yaad rakhna",
                "याद रखना"
            ]

            if any(t in lower_prompt for t in triggers):
                if save_memory(prompt, "automatic"):
                    st.toast("NOVA saved this memory.")

        except Exception as e:
            st.error("Gemini error: " + str(e))

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
                    "No readable text found. This may be a scanned PDF."
                )
            else:
                st.session_state.pdf_text = extracted_text
                st.success("PDF uploaded and text extracted.")

        except Exception as e:
            st.error("PDF reading failed: " + str(e))

    if st.session_state.pdf_text:
        st.caption(
            f"Extracted text: {len(st.session_state.pdf_text)} characters"
        )

        pdf_question = st.text_input(
            "Ask something about this PDF"
        )

        if st.button("Ask NOVA about PDF"):
            if pdf_question.strip():
                try:
                    with st.spinner("Reading your PDF..."):
                        # Limit context to avoid sending an excessively
                        # large document in one request.
                        pdf_context = st.session_state.pdf_text[:80000]

                        result = gemini.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=(
                                "Answer the question using the PDF text. "
                                "If the answer is not in the PDF, say so.\n\n"
                                "PDF TEXT:\n"
                                + pdf_context
                                + "\n\nQUESTION:\n"
                                + pdf_question
                            )
                        )

                    st.markdown("### NOVA's Answer")
                    st.write(result.text)

                except Exception as e:
                    st.error("PDF Assistant error: " + str(e))

        if st.button("Clear PDF"):
            st.session_state.pdf_text = ""
            st.rerun()

st.divider()
st.caption("NOVA AI • Your Personal AI Assistant")
