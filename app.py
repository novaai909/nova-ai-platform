
import streamlit as st
import fitz
import uuid
from datetime import datetime
from google import genai
from openai import OpenAI
from supabase import create_client

# =====================================================
# NOVA AI V4 - COLORFUL PROJECT SIDEBAR
# =====================================================

st.set_page_config(
    page_title="NOVA AI V4",
    page_icon="✨",
    layout="wide"
)

# ------------------- COLORFUL CSS -------------------

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 10% 5%, #23104a 0%, transparent 28%),
        radial-gradient(circle at 90% 20%, #071c4c 0%, transparent 30%),
        #080816;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#100b29,#080817,#10132b);
    border-right: 1px solid #6d28d9;
}
[data-testid="stSidebar"] * {
    color: #f5f3ff;
}
h1 {
    background: linear-gradient(90deg,#a855f7,#22d3ee,#ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
div.stButton > button {
    border: 1px solid #7c3aed;
    border-radius: 12px;
    background: linear-gradient(110deg,#321065,#102b78);
    color: white;
    transition: 0.2s;
}
div.stButton > button:hover {
    border: 1px solid #22d3ee;
    box-shadow: 0 0 12px #8b5cf6;
    color: white;
}
div[data-testid="stChatInput"] {
    border: 1px solid #a855f7;
    border-radius: 18px;
    box-shadow: 0 0 10px #30145a;
}
.nova-card {
    background: linear-gradient(135deg,#241044,#101e55);
    border: 1px solid #8b5cf6;
    border-radius: 18px;
    padding: 20px;
    margin: 8px 0;
    box-shadow: 0 0 12px #32115c;
}
.nova-title {
    font-size: 30px;
    font-weight: bold;
    background: linear-gradient(90deg,#c084fc,#22d3ee,#f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.nova-small {
    color: #c4b5fd;
}
hr {
    border-color: #472080;
}
</style>
""", unsafe_allow_html=True)

# ------------------- API CLIENTS -------------------

gemini_client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

openai_client = None
if st.secrets.get("OPENAI_API_KEY"):
    openai_client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets.get("SUPABASE_SECRET_KEY", st.secrets.get("SUPABASE_KEY"))
)

# ------------------- STORAGE -------------------

STORAGE_ID = "nova_main"

def load_database():
    try:
        result = (
            supabase.table("nova_storage")
            .select("*")
            .eq("id", STORAGE_ID)
            .execute()
        )

        if result.data:
            row = result.data[0]
            return row.get("chats", {}), row.get("notes", [])

        return {}, []

    except Exception as e:
        st.error(f"Database loading error: {e}")
        return {}, []

def save_database():
    try:
        supabase.table("nova_storage").upsert({
            "id": STORAGE_ID,
            "chats": st.session_state.chats,
            "notes": st.session_state.notes,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Database saving error: {e}")
        return False

# ------------------- CHAT STRUCTURE -------------------

PROJECTS_KEY = "__nova_projects__"
META_KEY = "__nova_chat_projects__"

def initialize_data():
    if "nova_loaded" in st.session_state:
        return

    chats, notes = load_database()

    if not isinstance(chats, dict):
        chats = {}

    # Remove reserved metadata from visible chats
    projects = chats.get(PROJECTS_KEY, [])
    meta = chats.get(META_KEY, {})

    # Preserve legacy chat format
    legacy_chats = {
        k: v for k, v in chats.items()
        if k not in [PROJECTS_KEY, META_KEY]
    }

    if not projects:
        projects = [
            {"id": "default", "name": "General"}
        ]

    for name, history in legacy_chats.items():
        if name not in meta:
            meta[name] = "default"

    if not legacy_chats:
        legacy_chats["Chat 1"] = []
        meta["Chat 1"] = "default"

    st.session_state.chats = legacy_chats
    st.session_state.projects = projects
    st.session_state.chat_projects = meta
    st.session_state.notes = notes or []
    st.session_state.active_chat = list(legacy_chats.keys())[0]
    st.session_state.active_project = "default"
    st.session_state.nova_loaded = True

initialize_data()

def pack_chats():
    data = dict(st.session_state.chats)
    data[PROJECTS_KEY] = st.session_state.projects
    data[META_KEY] = st.session_state.chat_projects
    return data

def save_all():
    original = st.session_state.chats
    st.session_state.chats = pack_chats()
    result = save_database()
    st.session_state.chats = original
    return result

def project_name(project_id):
    for p in st.session_state.projects:
        if p["id"] == project_id:
            return p["name"]
    return "General"

def chats_in_project(project_id):
    return [
        name for name in st.session_state.chats
        if st.session_state.chat_projects.get(name, "default") == project_id
    ]

def new_chat(project_id):
    name = "New Chat"
    number = 1

    while name in st.session_state.chats:
        number += 1
        name = f"New Chat {number}"

    st.session_state.chats[name] = []
    st.session_state.chat_projects[name] = project_id
    st.session_state.active_chat = name
    st.session_state.active_project = project_id
    save_all()

def new_project(name):
    name = name.strip()
    if not name:
        return

    project_id = str(uuid.uuid4())[:8]

    st.session_state.projects.append({
        "id": project_id,
        "name": name
    })

    st.session_state.active_project = project_id
    new_chat(project_id)
    save_all()

# ------------------- AI ENGINE -------------------

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

def ask_ai(prompt, history=None):
    history = history or []
    conversation = ""

    for item in history[-12:]:
        conversation += (
            f"\n{item['role']}: {item['content']}\n"
        )

    full_prompt = (
        "You are NOVA AI, a friendly, helpful and capable assistant. "
        "Answer accurately, clearly, and in the language of the user.\n"
        + conversation
        + "\nUser: "
        + prompt
    )

    # Try Gemini models first
    for model in GEMINI_MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model,
                contents=full_prompt
            )

            if response.text:
                return response.text, f"Gemini • {model}"

        except Exception:
            continue

    # OpenAI fallback
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are NOVA AI, a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )

            answer = response.choices[0].message.content

            if answer:
                return answer, "OpenAI • Fallback"

        except Exception:
            pass

    return (
        "NOVA abhi jawab nahi de paaya. API keys, quota ya model availability check karein.",
        "Error"
    )

# ------------------- SIDEBAR -------------------

with st.sidebar:

    st.markdown('<div class="nova-title">✨ NOVA AI</div>', unsafe_allow_html=True)

    if st.button("➕  New Chat", use_container_width=True):
        new_chat(st.session_state.active_project)
        st.rerun()

    search = st.text_input(
        "🔎 Search Chat",
        placeholder="Search chats...",
        key="nova_search"
    )

    st.divider()

    # Sidebar navigation
    nav = st.radio(
        "Navigation",
        [
            "📚 Library",
            "🎨 Customize",
            "📁 Projects",
            "🖥️ Remote",
            "🔲 Explore"
        ],
        label_visibility="collapsed",
        key="nova_navigation"
    )

    st.divider()

    st.markdown("### 💜 My Projects")

    for project in st.session_state.projects:
        project_id = project["id"]
        project_label = project["name"]

        if st.button(
            f"📂 {project_label}",
            key=f"project_{project_id}",
            use_container_width=True
        ):
            st.session_state.active_project = project_id
            project_chats = chats_in_project(project_id)

            if project_chats:
                st.session_state.active_chat = project_chats[0]
            else:
                new_chat(project_id)

            st.rerun()

        # Show chats under each project
        project_chats = chats_in_project(project_id)

        for chat_name in project_chats:
            if search and search.lower() not in chat_name.lower():
                continue

            if st.button(
                f"　↳ 💬 {chat_name}",
                key=f"sidebar_chat_{chat_name}",
                use_container_width=True
            ):
                st.session_state.active_project = project_id
                st.session_state.active_chat = chat_name
                st.rerun()

    st.divider()

    with st.expander("➕ New Project"):
        project_input = st.text_input(
            "Project name",
            key="nova_new_project_name"
        )

        if st.button("Create Project", key="create_project_button"):
            if project_input.strip():
                new_project(project_input)
                st.rerun()

    with st.expander("⚙️ Manage Projects"):
        if st.session_state.projects:
            selected_project = st.selectbox(
                "Select project",
                st.session_state.projects,
                format_func=lambda p: p["name"],
                key="manage_project_select"
            )

            rename_value = st.text_input(
                "Rename project",
                key="project_rename_input"
            )

            if st.button("Rename", key="project_rename_button"):
                if rename_value.strip():
                    selected_project["name"] = rename_value.strip()
                    save_all()
                    st.rerun()

            if selected_project["id"] != "default":
                if st.button("Delete project", key="project_delete_button"):
                    project_id = selected_project["id"]
                    names = chats_in_project(project_id)

                    for name in names:
                        st.session_state.chats.pop(name, None)
                        st.session_state.chat_projects.pop(name, None)

                    st.session_state.projects = [
                        p for p in st.session_state.projects
                        if p["id"] != project_id
                    ]

                    if not st.session_state.projects:
                        st.session_state.projects = [
                            {"id": "default", "name": "General"}
                        ]

                    st.session_state.active_project = "default"

                    if not chats_in_project("default"):
                        new_chat("default")

                    st.session_state.active_chat = chats_in_project("default")[0]
                    save_all()
                    st.rerun()

    st.divider()
    st.caption("✨ NOVA AI V4 • Gemini + OpenAI")

# ------------------- HOME -------------------

st.markdown('<div class="nova-title">✨ NOVA AI</div>', unsafe_allow_html=True)
st.markdown("### Your All-in-One AI Assistant")

st.markdown("""
<div class="nova-card">
<h2>🌈 Welcome to NOVA AI</h2>
<p class="nova-small">Ask anything, get more done!</p>
</div>
""", unsafe_allow_html=True)

# Navigation cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="nova-card">
    <h3>💬 AI Chat</h3>
    <p>Smart & helpful conversations</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="nova-card">
    <h3>📄 PDF Assistant</h3>
    <p>Read, summarize and analyze PDFs</p>
    </div>
    """, unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="nova-card">
    <h3>✍️ Writing Studio</h3>
    <p>Create content with AI help</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="nova-card">
    <h3>🧠 My Notes</h3>
    <p>Save and organize your ideas</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------- MAIN FEATURE NAV -------------------

section = st.selectbox(
    "Open feature",
    [
        "💬 AI Chat",
        "📄 PDF Assistant",
        "✍️ Writing Studio",
        "🧠 My Notes",
        "🧮 Calculator"
    ],
    key="nova_feature_select"
)

# ------------------- AI CHAT -------------------

if section == "💬 AI Chat":

    st.markdown("## 💬 AI Chat")

    active_chat = st.session_state.active_chat

    if active_chat not in st.session_state.chats:
        new_chat(st.session_state.active_project)
        st.rerun()

    history = st.session_state.chats[active_chat]

    if not history:
        st.info(f"Chatting inside: {project_name(st.session_state.active_project)}")

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask NOVA AI anything...")

    if prompt:
        history.append({
            "role": "user",
            "content": prompt
        })
        save_all()

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer, provider = ask_ai(prompt, history[:-1])

            st.markdown(answer)
            st.caption(f"Powered by {provider}")

        history.append({
            "role": "assistant",
            "content": answer
        })

        # Auto-name first chat based on prompt
        if active_chat.startswith("New Chat") and len(history) == 2:
            new_name = prompt[:35]

            if new_name not in st.session_state.chats:
                st.session_state.chats[new_name] = history
                st.session_state.chat_projects[new_name] = (
                    st.session_state.chat_projects.pop(active_chat, "default")
                )
                del st.session_state.chats[active_chat]
                st.session_state.active_chat = new_name

        save_all()
        st.rerun()

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("🗑️ Delete Chat"):
            st.session_state.chats.pop(active_chat, None)
            st.session_state.chat_projects.pop(active_chat, None)

            remaining = chats_in_project(st.session_state.active_project)

            if remaining:
                st.session_state.active_chat = remaining[0]
            else:
                new_chat(st.session_state.active_project)

            save_all()
            st.rerun()

    with col_b:
        if st.button("✏️ Rename Chat"):
            st.session_state.rename_chat_mode = True

    if st.session_state.get("rename_chat_mode", False):
        rename_chat_input = st.text_input(
            "New chat name",
            key="rename_chat_input"
        )

        if st.button("Save Chat Name"):
            if rename_chat_input.strip():
                old_name = active_chat
                new_name = rename_chat_input.strip()

                if new_name not in st.session_state.chats:
                    st.session_state.chats[new_name] = (
                        st.session_state.chats.pop(old_name)
                    )
                    st.session_state.chat_projects[new_name] = (
                        st.session_state.chat_projects.pop(old_name, "default")
                    )
                    st.session_state.active_chat = new_name
                    save_all()

                st.session_state.rename_chat_mode = False
                st.rerun()

# ------------------- PDF -------------------

elif section == "📄 PDF Assistant":

    st.markdown("## 📄 PDF Assistant")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:
        try:
            doc = fitz.open(stream=pdf.read(), filetype="pdf")
            text_content = "\n".join(
                page.get_text() for page in doc
            )

            if text_content.strip():
                pdf_action = st.radio(
                    "PDF action",
                    ["Ask Question", "Summary", "Quiz"]
                )

                if pdf_action == "Ask Question":
                    question = st.text_input("Ask about this PDF")

                    if st.button("Ask PDF"):
                        prompt = (
                            "Answer based on this PDF. If the answer is "
                            "not present, say so.\n\n"
                            + text_content[:100000]
                            + "\n\nQuestion: "
                            + question
                        )

                        with st.spinner("Reading PDF..."):
                            answer, provider = ask_ai(prompt)

                        st.markdown(answer)
                        st.caption(provider)

                elif pdf_action == "Summary":
                    if st.button("Generate Summary"):
                        prompt = (
                            "Summarize this PDF clearly:\n\n"
                            + text_content[:100000]
                        )

                        with st.spinner("Summarizing..."):
                            answer, provider = ask_ai(prompt)

                        st.markdown(answer)
                        st.caption(provider)

                elif pdf_action == "Quiz":
                    count = st.slider("Quiz questions", 3, 20, 5)

                    if st.button("Create Quiz"):
                        prompt = (
                            f"Create {count} multiple choice questions "
                            "from this PDF and provide answer key.\n\n"
                            + text_content[:100000]
                        )

                        with st.spinner("Creating quiz..."):
                            answer, provider = ask_ai(prompt)

                        st.markdown(answer)
                        st.caption(provider)

            else:
                st.warning("PDF text could not be extracted.")

        except Exception as e:
            st.error(f"PDF error: {e}")

# ------------------- WRITING STUDIO -------------------

elif section == "✍️ Writing Studio":

    st.markdown("## ✍️ Writing Studio")

    writing_type = st.selectbox(
        "Content type",
        [
            "Email",
            "Application",
            "Resume / Bio-data",
            "Essay",
            "Story",
            "Social Media Caption",
            "Letter",
            "Improve Text",
            "Code Helper",
            "Custom"
        ]
    )

    details = st.text_area("What should NOVA create?")

    if st.button("✨ Generate"):
        if details.strip():
            prompt = (
                f"Create a {writing_type} based on these instructions:\n"
                + details
            )

            with st.spinner("Writing..."):
                answer, provider = ask_ai(prompt)

            st.markdown(answer)
            st.caption(provider)

            st.download_button(
                "Download text",
                answer,
                file_name="nova_content.txt"
            )
        else:
            st.warning("Enter your instructions.")

# ------------------- NOTES -------------------

elif section == "🧠 My Notes":

    st.markdown("## 🧠 My Notes")

   