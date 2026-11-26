import streamlit as st
import fitz
import uuid
from datetime import datetime
from google import genai
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#100b29,#080817,#10132b);border-right:1px solid #6d28d9}
[data-testid="stSidebar"] *{color:#f5f3ff}
h1{background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
div.stButton>button{border:1px solid #7c3aed;border-radius:12px;background:linear-gradient(110deg,#321065,#102b78);color:white}
div.stButton>button:hover{border:1px solid #22d3ee;box-shadow:0 0 12px #8b5cf6;color:white}
.nova-card{background:linear-gradient(135deg,#241044,#101e55);border:1px solid #8b5cf6;border-radius:18px;padding:18px;margin:8px 0;box-shadow:0 0 12px #32115c}
</style>
""", unsafe_allow_html=True)

# API clients and Supabase connection
try:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Gemini client initialization failed: {e}")
    st.stop()

openai_client = None
if st.secrets.get("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception as e:
        st.warning(f"OpenAI client initialization failed: {e}")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Supabase connection failed: {e}")
    st.stop()

STORAGE_ID = "nova_main"
PROJECTS_KEY = "__nova_projects__"
CHAT_PROJECTS_KEY = "__nova_chat_projects__"


def load_storage():
    try:
        response = supabase.table("nova_storage").select("*").eq("id", STORAGE_ID).execute()
        if response.data:
            row = response.data[0]
            return row.get("chats") or {}, row.get("notes") or []
        return {}, []
    except Exception as exc:
        st.error(f"Supabase loading error: {exc}")
        return {}, []


def persist_storage():
    packed = dict(st.session_state.chats)
    packed[PROJECTS_KEY] = st.session_state.projects
    packed[CHAT_PROJECTS_KEY] = st.session_state.chat_projects
    try:
        supabase.table("nova_storage").upsert({
            "id": STORAGE_ID,
            "chats": packed,
            "notes": st.session_state.notes
        }).execute()
        return True
    except Exception as exc:
        st.error(f"Supabase saving error: {exc}")
        return False


def init_state():
    if st.session_state.get("nova_initialized"):
        return
    loaded_chats, loaded_notes = load_storage()
    if not isinstance(loaded_chats, dict):
        loaded_chats = {}
    projects = loaded_chats.get(PROJECTS_KEY, [])
    chat_projects = loaded_chats.get(CHAT_PROJECTS_KEY, {})
    visible_chats = {k: v for k, v in loaded_chats.items() if k not in (PROJECTS_KEY, CHAT_PROJECTS_KEY)}
    if not projects or not isinstance(projects, list):
        projects = [{"id": "default", "name": "General"}]
    if not isinstance(chat_projects, dict):
        chat_projects = {}
    if not visible_chats:
        visible_chats = {"Chat 1": []}
    for name in visible_chats:
        chat_projects.setdefault(name, "default")
    st.session_state.chats = visible_chats
    st.session_state.projects = projects
    st.session_state.chat_projects = chat_projects
    st.session_state.notes = loaded_notes if isinstance(loaded_notes, list) else []
    st.session_state.active_chat = next(iter(visible_chats))
    st.session_state.active_project = chat_projects.get(st.session_state.active_chat, "default")
    st.session_state.nova_initialized = True


init_state()


def get_project_name(pid):
    for p in st.session_state.projects:
        if p.get("id") == pid:
            return p.get("name", "Project")
    return "General"


def chats_for_project(pid):
    return [name for name in st.session_state.chats if st.session_state.chat_projects.get(name, "default") == pid]


def create_chat(pid):
    base = "New Chat"
    name = base
    n = 2
    while name in st.session_state.chats:
        name = f"{base} {n}"
        n += 1
    st.session_state.chats[name] = []
    st.session_state.chat_projects[name] = pid
    st.session_state.active_chat = name
    st.session_state.active_project = pid
    persist_storage()


def create_project(name):
    clean = name.strip()
    if not clean:
        return
    pid = str(uuid.uuid4())[:8]
    st.session_state.projects.append({"id": pid, "name": clean})
    create_chat(pid)


# Chat model fallback: try several Gemini models before OpenAI.
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite"]


def ask_ai(prompt, history=None):
    history = history or []
    errors = []
    history_text = "\n".join(f"{m.get('role','')}: {m.get('content','')}" for m in history[-12:])
    combined_prompt = ("You are NOVA AI, a friendly, helpful assistant. Answer accurately, clearly, and in the user's language.\n\n"
                      + history_text + "\n\nUser: " + prompt)
    for model in GEMINI_MODELS:
        try:
            result = gemini_client.models.generate_content(model=model, contents=combined_prompt)
            answer = getattr(result, "text", None)
            if answer and answer.strip():
                return answer, f"Gemini • {model}"
            errors.append(f"{model}: empty response")
        except Exception as exc:
            errors.append(f"{model}: {str(exc)[:180]}")
    if openai_client is not None:
        try:
            result = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": "You are NOVA AI, a friendly, helpful assistant."},
                          {"role": "user", "content": combined_prompt}],
            )
            answer = result.choices[0].message.content
            if answer and answer.strip():
                return answer, "OpenAI fallback • gpt-4.1-mini"
            errors.append("OpenAI: empty response")
        except Exception as exc:
            errors.append(f"OpenAI: {str(exc)[:250]}")
    return "NOVA AI couldn't generate a response. Details: " + " | ".join(errors), "All providers failed"

# Sidebar
with st.sidebar:
    st.markdown("# ✨ NOVA AI")
    if st.button("➕ New Chat", use_container_width=True, key="sidebar_new_chat"):
        create_chat(st.session_state.active_project)
        st.rerun()
    search = st.text_input("🔎 Search Chat", placeholder="Search chat titles", key="sidebar_search")
    st.divider()
    nav = st.radio("Sidebar navigation", ["📚 Library", "🎨 Customize", "📁 Projects", "🖥️ Remote", "🔲 Explore"], label_visibility="collapsed")
    st.divider()
    st.markdown("### 🌈 My Projects")
    for project in st.session_state.projects:
        pid = project.get("id", "default")
        if st.button(f"📁 {project.get('name','Project')}", use_container_width=True, key=f"project_select_{pid}"):
            st.session_state.active_project = pid
            found = chats_for_project(pid)
            if found:
                st.session_state.active_chat = found[0]
            else:
                create_chat(pid)
            st.rerun()
        for chat_title in chats_for_project(pid):
            if search and search.lower() not in chat_title.lower():
                continue
            if st.button(f"↳ 💬 {chat_title}", use_container_width=True, key=f"chat_select_{chat_title}"):
                st.session_state.active_project = pid
                st.session_state.active_chat = chat_title
                st.rerun()
    with st.expander("➕ New Project"):
        project_name_input = st.text_input("Project name", key="project_name_input")
        if st.button("Create Project", key="project_create_button"):
            if project_name_input.strip():
                create_project(project_name_input)
                st.rerun()
    with st.expander("⚙️ Manage Projects"):
        if st.session_state.projects:
            project_to_manage = st.selectbox("Choose project", st.session_state.projects, format_func=lambda p: p.get("name", "Project"), key="project_manage_select")
            rename_project_input = st.text_input("New project name", key="project_rename_input")
            if st.button("Rename project", key="project_rename_button") and rename_project_input.strip():
                project_to_manage["name"] = rename_project_input.strip()
                persist_storage()
                st.rerun()
            if project_to_manage.get("id") != "default" and st.button("Delete project and its chats", key="project_delete_button"):
                pid = project_to_manage.get("id")
                for title in chats_for_project(pid):
                    st.session_state.chats.pop(title, None)
                    st.session_state.chat_projects.pop(title, None)
                st.session_state.projects = [p for p in st.session_state.projects if p.get("id") != pid]
                if not st.session_state.projects:
                    st.session_state.projects = [{"id": "default", "name": "General"}]
                st.session_state.active_project = "default"
                default_chats = chats_for_project("default")
                if not default_chats:
                    create_chat("default")
                else:
                    st.session_state.active_chat = default_chats[0]
                persist_storage()
                st.rerun()
    st.caption("NOVA AI • Gemini-first, OpenAI fallback")

# Main
st.markdown("# ✨ NOVA AI")
st.markdown("### Your All-in-One AI Assistant")
st.markdown('<div class="nova-card"><h2>🌈 Welcome to NOVA</h2><p>Chat, work with PDFs, write, and keep notes.</p></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="nova-card"><h3>💬 AI Chat</h3><p>Conversations with Gemini-first fallback.</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="nova-card"><h3>📄 PDF Assistant</h3><p>Ask questions and summarize PDF files.</p></div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    st.markdown('<div class="nova-card"><h3>✍️ Writing Studio</h3><p>Draft and improve content.</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="nova-card"><h3>🧠 My Notes</h3><p>Save notes in the database.</p></div>', unsafe_allow_html=True)
feature = st.selectbox("Open feature", ["💬 AI Chat", "📄 PDF Assistant", "✍️ Writing Studio", "🧠 My Notes", "🧮 Calculator"], key="feature_select")

if feature == "💬 AI Chat":
    st.markdown("## 💬 AI Chat")
    active = st.session_state.active_chat
    if active not in st.session_state.chats:
        create_chat(st.session_state.active_project)
        st.rerun()
    history = st.session_state.chats[active]
    st.caption(f"Project: {get_project_name(st.session_state.active_project)}")
    for message in history:
        with st.chat_message(message.get("role", "assistant")):
            st.markdown(message.get("content", ""))
            if message.get("provider"):
                st.caption(message["provider"])
    prompt = st.chat_input("Ask NOVA AI anything...")
    if prompt:
        history.append({"role": "user", "content": prompt})
        persist_storage()
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer, provider = ask_ai(prompt, history[:-1])
            st.markdown(answer)
            st.caption(provider)
        history.append({"role": "assistant", "content": answer, "provider": provider})
        # Rename initial chat from prompt, without losing history
        if active.startswith("New Chat") and len(history) == 2:
            proposed = prompt.strip().replace("\n", " ")[:40] or "Chat"
            new_title = proposed
            suffix = 2
            while new_title in st.session_state.chats and new_title != active:
                new_title = f"{proposed} ({suffix})"
                suffix += 1
            if new_title != active:
                st.session_state.chats[new_title] = history
                st.session_state.chat_projects[new_title] = st.session_state.chat_projects.pop(active, st.session_state.active_project)
                st.session_state.chats.pop(active, None)
                st.session_state.active_chat = new_title
        persist_storage()
        st.rerun()
    col_delete, col_rename = st.columns(2)
    with col_delete:
        if st.button("🗑️ Delete Chat", key="delete_active_chat"):
            st.session_state.chats.pop(active, None)
            st.session_state.chat_projects.pop(active, None)
            remaining = chats_for_project(st.session_state.active_project)
            if remaining:
                st.session_state.active_chat = remaining[0]
            else:
                create_chat(st.session_state.active_project)
            persist_storage()
            st.rerun()
    with col_rename:
        with st.expander("✏️ Rename Chat"):
            rename_chat_input = st.text_input("New title", key="chat_rename_input")
            if st.button("Save chat name", key="chat_rename_save") and rename_chat_input.strip():
                if rename_chat_input.strip() not in st.session_state.chats:
                    st.session_state.chats[rename_chat_input.strip()] = st.session_state.chats.pop(active)
                    st.session_state.chat_projects[rename_chat_input.strip()] = st.session_state.chat_projects.pop(active, st.session_state.active_project)
                    st.session_state.active_chat = rename_chat_input.strip()
                    persist_storage()
                    st.rerun()

elif feature == "📄 PDF Assistant":
    st.markdown("## 📄 PDF Assistant")
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"], key="pdf_upload")
    if uploaded_pdf:
        try:
            document = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
            extracted = "\n".join(page.get_text() for page in document)
            if not extracted.strip():
                st.warning("No selectable text found in this PDF. It may be scanned.")
            else:
                action = st.radio("Choose", ["Ask Question", "Summary", "Quiz"], key="pdf_action")
                if action == "Ask Question":
                    question = st.text_input("Your question about the PDF", key="pdf_question")
                    if st.button("Ask PDF", key="pdf_ask_button") and question.strip():
                        with st.spinner("Reading PDF..."):
                            answer, provider = ask_ai("Use only this PDF content to answer. If it is not covered, say so.\n\n" + extracted[:90000] + "\n\nQuestion: " + question)
                        st.markdown(answer)
                        st.caption(provider)
                elif action == "Summary":
                    if st.button("Generate Summary", key="pdf_summary_button"):
                        with st.spinner("Summarizing..."):
                            answer, provider = ask_ai("Summarize this PDF clearly:\n\n" + extracted[:90000])
                        st.markdown(answer)
                        st.caption(provider)
                else:
                    count = st.slider("Questions", 3, 15, 5, key="pdf_quiz_count")
                    if st.button("Generate Quiz", key="pdf_quiz_button"):
                        with st.spinner("Creating quiz..."):
                            answer, provider = ask_ai(f"Create {count} multiple-choice questions from this PDF and put an answer key at the end:\n\n" + extracted[:90000])
                        st.markdown(answer)
                        st.caption(provider)
        except Exception as exc:
            st.error(f"PDF processing error: {exc}")

elif feature == "✍️ Writing Studio":
    st.markdown("## ✍️ Writing Studio")
    writing_type = st.selectbox("Type", ["Email", "Application", "Bio-data / Resume", "Essay", "Story", "Social caption", "Letter", "Improve text", "Code help", "Custom"], key="writing_type")
    instructions = st.text_area("What should NOVA write?", key="writing_instructions")
    if st.button("✨ Generate writing", key="writing_generate"):
        if instructions.strip():
            with st.spinner("Writing..."):
                answer, provider = ask_ai(f"Create {writing_type}. Instructions:\n{instructions}")
            st.markdown(answer)
            st.caption(provider)
            st.download_button("Download text", answer, file_name="nova_draft.txt", key="writing_download")
        else:
            st.warning("Please enter instructions.")

elif feature == "🧠 My Notes":
    st.markdown("## 🧠 My Notes")
    with st.form("notes_form"):
        title = st.text_input("Note title")
        content = st.text_area("Note")
        submitted = st.form_submit_button("💾 Save Note")
    if submitted:
        if title.strip() and content.strip():
            st.session_state.notes.append({"title": title.strip(), "content": content.strip(), "date": datetime.now().strftime("%d-%m-%Y %H:%M")})
            if persist_storage():
                st.success("Note saved!")
                st.rerun()
        else:
            st.warning("Fill in both title and note.")
    for index, note in enumerate(st.session_state.notes):
        with st.expander(f"📌 {note.get('title', 'Untitled')}"):
            st.write(note.get("content", ""))
            st.caption(note.get("date", ""))
            st.download_button("Download note", note.get("content", ""), file_name=f"note_{index+1}.txt", key=f"note_dl_{index}")
            if st.button("Delete note", key=f"note_del_{index}"):
                st.session_state.notes.pop(index)
                persist_storage()
                st.rerun()

elif feature == "🧮 Calculator":
    st.markdown("## 🧮 Calculator")
    num1 = st.number_input("First number", value=0.0, key="calc_num1")
    op = st.selectbox("Operation", ["+", "-", "×", "÷", "%"], key="calc_op")
    num2 = st.number_input("Second number", value=1.0, key="calc_num2")
    if st.button("Calculate", key="calc_button"):
        if op == "+": result = num1 + num2
        elif op == "-": result = num1 - num2
        elif op == "×": result = num1 * num2
        elif op == "÷": result = None if num2 == 0 else num1 / num2
        else: result = num1 * num2 / 100
        if op == "÷" and num2 == 0:
            st.error("Cannot divide by zero.")
        else:
            st.success(f"Result: {result}")

# Navigation placeholders/feedback
if nav == "📚 Library":
    st.sidebar.info("Library: use project chat history and Notes to access saved content.")
elif nav == "🎨 Customize":
    st.sidebar.info("NOVA's neon color theme is active.")
elif nav == "📁 Projects":
    st.sidebar.info("Create, select and manage projects in My Projects.")
elif nav == "🖥️ Remote":
    st.sidebar.info("Remote access is not implemented yet.")
elif nav == "🔲 Explore":
    st.sidebar.info("More NOVA features can be added here.")

st.divider()
st.markdown("<center>✨ <b>NOVA AI</b> • Gemini-first, OpenAI fallback</center>", unsafe_allow_html=True)
