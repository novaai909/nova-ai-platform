import streamlit as st
import fitz
import uuid
from datetime import datetime
from google import genai
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816;color:#f5f3ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#100b29,#080817,#10132b);border-right:1px solid #6d28d9}
.nova-card{background:linear-gradient(135deg,#241044,#101e55);border:1px solid #8b5cf6;border-radius:18px;padding:18px;margin:8px 0;box-shadow:0 0 12px #32115c}
.nova-hero{text-align:center;padding:10px 0 22px}
.nova-infinity{display:inline-block;font-size:clamp(85px,22vw,150px);line-height:1.05;background:linear-gradient(90deg,#ff36d1,#8b5cf6,#22d3ee,#00ff88,#ff36d1);background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:infinity-glow 3s ease-in-out infinite,gradient-shift 6s linear infinite;filter:drop-shadow(0 0 15px #a855f7)}
.nova-brand{font-family:cursive;font-size:clamp(42px,10vw,72px);font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899,#00ff88,#a855f7);background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shine 4s ease infinite,brand-glow 2.5s ease-in-out infinite}
.nova-tag{color:white;font-family:cursive;font-size:clamp(22px,6vw,32px);letter-spacing:1px;text-shadow:0 0 10px #a855f7}
.nova-splash{position:fixed;inset:0;z-index:999999;background:radial-gradient(circle at center,#26105b 0%,#10102b 42%,#050611 100%);display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden;animation:splashout 1.2s ease 6.5s forwards;pointer-events:none}
.splash-logo{font-size:clamp(90px,25vw,170px);line-height:1;opacity:0;display:inline-block;background:linear-gradient(90deg,#ff00cc,#7c3aed,#00e5ff,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 22px #a855f7);animation:logo-grow-spin 2.3s ease-out forwards,logo-glow 2.4s ease-in-out infinite,gradient-shift 5s linear infinite}
.splash-name{font-family:cursive;font-size:clamp(48px,12vw,85px);font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,#ff00cc,#00e5ff,#a855f7,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;opacity:0;animation:appear 1.6s ease 1.8s forwards,shine 4s linear infinite,brand-glow 2.5s ease-in-out infinite}
.splash-welcome{color:white;font-family:cursive;font-size:clamp(23px,6vw,36px);letter-spacing:1px;text-align:center;opacity:0;text-shadow:0 0 12px white;animation:appear 1.5s ease 2.8s forwards}
.bfly{position:absolute;font-size:clamp(23px,5vw,36px);will-change:transform;animation:flypath 5.5s ease-in-out infinite;filter:drop-shadow(0 0 5px currentColor)}
.bfly:nth-child(odd){animation-name:flypath2}.bfly:nth-child(3n){animation-name:flypath3}.bfly:nth-child(4n){animation-name:flypath4}.bfly:nth-child(5n){animation-name:flypath5}
@keyframes logo-grow-spin{0%{opacity:0;transform:scale(.12) rotate(0deg)}65%{opacity:1;transform:scale(1.35) rotate(300deg)}100%{opacity:1;transform:scale(1) rotate(360deg)}}
@keyframes logo-glow{0%,100%{filter:drop-shadow(0 0 10px #a855f7)}50%{filter:drop-shadow(0 0 34px #22d3ee)}}
@keyframes infinity-glow{0%,100%{filter:drop-shadow(0 0 12px #a855f7)}50%{filter:drop-shadow(0 0 28px #22d3ee)}}
@keyframes gradient-shift{0%{background-position:0% 50%}100%{background-position:100% 50%}}
@keyframes shine{0%,100%{background-position:0%}50%{background-position:100%}}
@keyframes brand-glow{0%,100%{text-shadow:0 0 6px #a855f7}50%{text-shadow:0 0 22px #22d3ee}}
@keyframes appear{from{opacity:0;transform:translateY(25px)}to{opacity:1;transform:translateY(0)}}
@keyframes flypath{0%{transform:translate(-8vw,10vh) rotate(-15deg)}25%{transform:translate(24vw,-24vh) rotate(25deg)}50%{transform:translate(45vw,12vh) rotate(-30deg)}75%{transform:translate(-28vw,-18vh) rotate(18deg)}100%{transform:translate(-8vw,10vh) rotate(-15deg)}}
@keyframes flypath2{0%{transform:translate(8vw,25vh) rotate(20deg)}25%{transform:translate(-35vw,-20vh) rotate(-25deg)}50%{transform:translate(-15vw,-45vh) rotate(35deg)}75%{transform:translate(35vw,-10vh) rotate(-18deg)}100%{transform:translate(8vw,25vh) rotate(20deg)}}
@keyframes flypath3{0%{transform:translate(15vw,-20vh) rotate(5deg)}25%{transform:translate(-40vw,5vh) rotate(35deg)}50%{transform:translate(-20vw,35vh) rotate(-25deg)}75%{transform:translate(40vw,25vh) rotate(20deg)}100%{transform:translate(15vw,-20vh) rotate(5deg)}}
@keyframes flypath4{0%{transform:translate(-25vw,-30vh) rotate(-30deg)}25%{transform:translate(35vw,10vh) rotate(20deg)}50%{transform:translate(10vw,40vh) rotate(-10deg)}75%{transform:translate(-40vw,5vh) rotate(30deg)}100%{transform:translate(-25vw,-30vh) rotate(-30deg)}}
@keyframes flypath5{0%{transform:translate(0,35vh) rotate(15deg)}25%{transform:translate(38vw,-35vh) rotate(-20deg)}50%{transform:translate(-35vw,-15vh) rotate(30deg)}75%{transform:translate(-10vw,30vh) rotate(-25deg)}100%{transform:translate(0,35vh) rotate(15deg)}}
@keyframes splashout{to{opacity:0;visibility:hidden}}
</style>
""", unsafe_allow_html=True)

# ---------- API CLIENTS ----------
try:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Gemini setup error: please check GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()
openai_client = None
if st.secrets.get("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception:
        st.warning("OpenAI client could not initialize; check OPENAI_API_KEY.")
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Supabase setup error: check SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

# ---------- STORAGE ----------
STORE_ID = "nova_main"
PROJECTS_META = "__nova_projects__"
CHAT_PROJECT_META = "__nova_chat_projects__"

def load_data():
    try:
        res = supabase.table("nova_storage").select("*").eq("id", STORE_ID).execute()
        if res.data:
            row = res.data[0]
            return row.get("chats") or {}, row.get("notes") or []
    except Exception as e:
        st.error(f"Database load error: {e}")
    return {}, []

def save_data():
    packed = dict(st.session_state.chats)
    packed[PROJECTS_META] = st.session_state.projects
    packed[CHAT_PROJECT_META] = st.session_state.chat_projects
    try:
        supabase.table("nova_storage").upsert({"id":STORE_ID,"chats":packed,"notes":st.session_state.notes}).execute()
        return True
    except Exception as e:
        st.error(f"Database save error: {e}")
        return False

def initialize():
    if st.session_state.get("initialized"):
        return
    loaded, notes = load_data()
    loaded = loaded if isinstance(loaded,dict) else {}
    projects = loaded.pop(PROJECTS_META,[{"id":"default","name":"General"}])
    chat_projects = loaded.pop(CHAT_PROJECT_META,{})
    if not isinstance(projects,list) or not projects:
        projects = [{"id":"default","name":"General"}]
    if not isinstance(chat_projects,dict): chat_projects = {}
    if not loaded: loaded = {"Chat 1":[]}
    for title in loaded: chat_projects.setdefault(title,"default")
    st.session_state.chats = loaded
    st.session_state.projects = projects
    st.session_state.chat_projects = chat_projects
    st.session_state.notes = notes if isinstance(notes,list) else []
    st.session_state.active_chat = next(iter(loaded))
    st.session_state.active_project = chat_projects.get(st.session_state.active_chat,"default")
    st.session_state.initialized = True
initialize()

def project_label(pid):
    return next((p.get("name","Project") for p in st.session_state.projects if p.get("id")==pid),"General")
def project_chats(pid):
    return [t for t in st.session_state.chats if st.session_state.chat_projects.get(t,"default")==pid]
def new_chat(pid):
    title="New Chat"; n=2
    while title in st.session_state.chats:
        title=f"New Chat {n}"; n+=1
    st.session_state.chats[title]=[]; st.session_state.chat_projects[title]=pid
    st.session_state.active_chat=title; st.session_state.active_project=pid; save_data()
def new_project(name):
    name=name.strip()
    if name:
        pid=str(uuid.uuid4())[:8]
        st.session_state.projects.append({"id":pid,"name":name})
        new_chat(pid)

# ---------- GEMINI FIRST / OPENAI FALLBACK ----------
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]
def ask_ai(prompt, history=None):
    history = history or []
    prior = "\n".join(f"{m.get('role','')}: {m.get('content','')}" for m in history[-10:])
    combined = "You are NOVA AI, a helpful assistant. Respond accurately and in the user's language.\n\n" + prior + "\n\nUser: " + prompt
    failures=[]
    for model in GEMINI_MODELS:
        try:
            result=gemini_client.models.generate_content(model=model,contents=combined)
            answer=getattr(result,"text",None)
            if answer and answer.strip(): return answer, f"Gemini • {model}"
            failures.append(f"{model}: empty response")
        except Exception as e:
            failures.append(f"{model}: {str(e)[:160]}")
    if openai_client:
        try:
            result=openai_client.chat.completions.create(model="gpt-4.1-mini",messages=[{"role":"user","content":combined}])
            answer=result.choices[0].message.content
            if answer and answer.strip(): return answer,"OpenAI fallback • gpt-4.1-mini"
            failures.append("OpenAI: empty response")
        except Exception as e:
            failures.append(f"OpenAI: {str(e)[:200]}")
    return "NOVA could not answer. Errors: " + " | ".join(failures), "Providers failed"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("# ✨ NOVA AI")
    if st.button("➕ New Chat",key="sidebar_new",use_container_width=True):
        new_chat(st.session_state.active_project); st.rerun()
    search=st.text_input("🔎 Search chats",placeholder="Search chat titles",key="search_chats")
    st.divider()
    nav=st.radio("Navigation",["📚 Library","🎨 Customize","📁 Projects","🖥️ Remote","🔲 Explore"],label_visibility="collapsed")
    st.divider(); st.markdown("### 🌈 Projects")
    for proj in st.session_state.projects:
        pid=proj.get("id","default")
        if st.button("📁 "+proj.get("name","Project"),key=f"project_{pid}",use_container_width=True):
            st.session_state.active_project=pid
            found=project_chats(pid)
            if found: st.session_state.active_chat=found[0]
            else: new_chat(pid)
            st.rerun()
        for title in project_chats(pid):
            if search and search.lower() not in title.lower(): continue
            if st.button("↳ 💬 "+title,key=f"chat_{title}",use_container_width=True):
                st.session_state.active_chat=title; st.session_state.active_project=pid; st.rerun()
    with st.expander("➕ New Project"):
        p_name=st.text_input("Project name",key="project_name")
        if st.button("Create project",key="project_create"):
            new_project(p_name); st.rerun()
    with st.expander("⚙️ Manage Projects"):
        selected=st.selectbox("Choose project",st.session_state.projects,format_func=lambda p:p.get("name","Project"),key="manage_project")
        rename=st.text_input("New name",key="project_rename")
        if st.button("Rename project",key="rename_project") and rename.strip():
            selected["name"]=rename.strip(); save_data(); st.rerun()
        if selected.get("id")!="default" and st.button("Delete project and chats",key="project_delete"):
            pid=selected["id"]
            for t in project_chats(pid):
                st.session_state.chats.pop(t,None); st.session_state.chat_projects.pop(t,None)
            st.session_state.projects=[p for p in st.session_state.projects if p.get("id")!=pid]
            st.session_state.active_project="default"
            defaults=project_chats("default")
            if defaults: st.session_state.active_chat=defaults[0]
            else: new_chat("default")
            save_data(); st.rerun()
    st.caption("Gemini first • OpenAI fallback")

# ---------- SPLASH / HEADER ----------
if not st.session_state.get("splash_seen", False):
    butterflies = []
    # 26 colorful butterflies with varied positions, timings, and paths.
    for i in range(26):
        left = (i * 37 + 11) % 94
        top = (i * 53 + 7) % 88
        hue = (i * 47) % 360
        delay = (i * 0.23) % 3.8
        duration = 4.4 + (i % 6) * 0.55
        butterflies.append(
            f'<div class="bfly" style="left:{left}%;top:{top}%;color:hsl({hue},95%,70%);'
            f'filter:hue-rotate({hue}deg);animation-delay:{delay}s;animation-duration:{duration}s">🦋</div>'
        )
    butterfly_html = "".join(butterflies)
    st.markdown(f"""
    <div class="nova-splash">
      {butterfly_html}
      <div class="splash-logo">∞</div>
      <div class="splash-name">NOVA AI</div>
      <div class="splash-welcome">Welcome to NOVA AI</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.splash_seen = True

st.markdown("""
<div class="nova-hero">
  <div class="nova-infinity">∞</div>
  <div class="nova-brand">NOVA AI</div>
  <div class="nova-tag">Welcome to NOVA AI</div>
</div>
<div class="nova-card"><h2>🌈 Welcome to NOVA</h2><p>Chat, work with PDFs, write, and keep notes.</p></div>
""", unsafe_allow_html=True)
feature=st.selectbox("Open feature",["💬 AI Chat","📄 PDF Assistant","✍️ Writing Studio","🧠 My Notes","🧮 Calculator"],key="feature")

# ---------- CHAT ----------
if feature=="💬 AI Chat":
    st.markdown("## 💬 AI Chat")
    active=st.session_state.active_chat
    history=st.session_state.chats.setdefault(active,[])
    st.caption("Project: "+project_label(st.session_state.active_project))
    for m in history:
        with st.chat_message(m.get("role","assistant")):
            st.markdown(m.get("content",""))
            if m.get("provider"): st.caption(m["provider"])
    prompt=st.chat_input("Ask NOVA AI anything...")
    if prompt:
        history.append({"role":"user","content":prompt}); save_data()
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."): answer,provider=ask_ai(prompt,history[:-1])
            st.markdown(answer); st.caption(provider)
        history.append({"role":"assistant","content":answer,"provider":provider})
        if active.startswith("New Chat") and len(history)==2:
            base=prompt.replace("\n"," ").strip()[:40] or "Chat"; title=base; suffix=2
            while title in st.session_state.chats and title!=active:
                title=f"{base} ({suffix})"; suffix+=1
            if title!=active:
                st.session_state.chats[title]=history
                st.session_state.chat_projects[title]=st.session_state.chat_projects.pop(active,st.session_state.active_project)
                st.session_state.chats.pop(active,None); st.session_state.active_chat=title
        save_data(); st.rerun()
    c1,c2=st.columns(2)
    with c1:
        if st.button("🗑️ Delete Chat",key="delete_chat"):
            st.session_state.chats.pop(active,None); st.session_state.chat_projects.pop(active,None)
            remaining=project_chats(st.session_state.active_project)
            if remaining: st.session_state.active_chat=remaining[0]
            else: new_chat(st.session_state.active_project)
            save_data(); st.rerun()
    with c2:
        with st.expander("✏️ Rename Chat"):
            new_title=st.text_input("New chat title",key="chat_rename_input")
            if st.button("Save title",key="chat_rename_save") and new_title.strip() and new_title.strip() not in st.session_state.chats:
                st.session_state.chats[new_title.strip()]=st.session_state.chats.pop(active)
                st.session_state.chat_projects[new_title.strip()]=st.session_state.chat_projects.pop(active,st.session_state.active_project)
                st.session_state.active_chat=new_title.strip(); save_data(); st.rerun()    with c2:
        with st.expander("✏️ Rename Chat"):
            new_title=st.text_input("New chat title",key="chat_rename_input")
            if st.button("Save title",key="chat_rename_save") and new_title.strip() and new_title.strip() not in st.session_state.chats:
                st.session_state.chats[new_title.strip()]=st.session_state.chats.pop(active)
                st.session_state.chat_projects[new_title.strip()]=st.session_state.chat_projects.pop(active,st.session_state.active_project)
                st.session_state.active_chat=new_title.strip(); save_data(); st.rerun()

# ---------- PDF ----------
elif feature=="📄 PDF Assistant":
    st.markdown("## 📄 PDF Assistant")
    pdf=st.file_uploader("Upload PDF",type=["pdf"],key="pdf_file")
    if pdf:
        try:
            doc=fitz.open(stream=pdf.getvalue(),filetype="pdf")
            extracted="\n".join(page.get_text() for page in doc)
            if not extracted.strip(): st.warning("No selectable text found in this PDF; it may be scanned.")
            else:
                task=st.radio("PDF task",["Ask Question","Summary","Quiz"],key="pdf_task")
                if task=="Ask Question":
                    q=st.text_input("Question about the PDF",key="pdf_question")
                    if st.button("Ask PDF",key="pdf_ask") and q.strip():
                        with st.spinner("Reading PDF..."): answer,provider=ask_ai("Answer based only on this PDF. If missing, say so.\n\n"+extracted[:80000]+"\n\nQuestion: "+q)
                        st.markdown(answer); st.caption(provider)
                elif task=="Summary":
                    if st.button("Summarize",key="pdf_summary"):
                        with st.spinner("Summarizing..."): answer,provider=ask_ai("Summarize this PDF:\n\n"+extracted[:80000])
                        st.markdown(answer); st.caption(provider)
                else:
                    count=st.slider("Quiz questions",3,15,5,key="quiz_count")
                    if st.button("Generate quiz",key="pdf_quiz"):
                        with st.spinner("Creating quiz..."): answer,provider=ask_ai(f"Create {count} multiple-choice quiz questions and answer key from this PDF:\n\n"+extracted[:80000])
                        st.markdown(answer); st.caption(provider)
        except Exception as e: st.error(f"PDF processing error: {e}")

# ---------- WRITING ----------
elif feature=="✍️ Writing Studio":
    st.markdown("## ✍️ Writing Studio")
    kind=st.selectbox("Writing type",["Email","Application","Bio-data / Resume","Essay","Story","Social caption","Letter","Improve text","Code help","Custom"],key="writing_kind")
    instructions=st.text_area("What should NOVA write?",key="writing_prompt")
    if st.button("✨ Generate",key="writing_generate"):
        if instructions.strip():
            with st.spinner("Writing..."): answer,provider=ask_ai(f"Write a {kind}. Instructions:\n{instructions}")
            st.markdown(answer); st.caption(provider)
            st.download_button("Download text",answer,file_name="nova_draft.txt",key="writing_download")
        else: st.warning("Enter instructions first.")

# ---------- NOTES ----------
elif feature=="🧠 My Notes":
    st.markdown("## 🧠 My Notes")
    with st.form("notes_form"):
        note_title=st.text_input("Note title")
        note_body=st.text_area("Note")
        submit=st.form_submit_button("💾 Save note")
    if submit:
        if note_title.strip() and note_body.strip():
            st.session_state.notes.append({"title":note_title.strip(),"content":note_body.strip(),"date":datetime.now().strftime("%d-%m-%Y %H:%M")})
            if save_data(): st.success("Note saved."); st.rerun()
        else: st.warning("Fill in title and note.")
    for i,n in enumerate(st.session_state.notes):
        with st.expander("📌 "+n.get("title","Untitled")):
            st.write(n.get("content","")); st.caption(n.get("date",""))
            st.download_button("Download note",n.get("content",""),file_name=f"note_{i+1}.txt",key=f"note_dl_{i}")
            if st.button("Delete note",key=f"note_del_{i}"):
                st.session_state.notes.pop(i); save_data(); st.rerun()

# ---------- CALCULATOR ----------
elif feature=="🧮 Calculator":
    st.markdown("## 🧮 Calculator")
    a=st.number_input("First number",value=0.0,key="calc_a")
    op=st.selectbox("Operation",["+","-","×","÷","%"],key="calc_op")
    b=st.number_input("Second number",value=1.0,key="calc_b")
    if st.button("Calculate",key="calc_btn"):
        result=(a+b if op=="+" else a-b if op=="-" else a*b if op=="×" else (None if b==0 else a/b) if op=="÷" else a*b/100)
        if op=="÷" and b==0: st.error("Cannot divide by zero.")
        else: st.success(f"Result: {result}")

# ---------- SIDEBAR NAV NOTES ----------
if nav=="📚 Library": st.sidebar.info("Use project chat history and Notes for saved content.")
elif nav=="🎨 Customize": st.sidebar.info("NOVA animated neon theme is active.")
elif nav=="📁 Projects": st.sidebar.info("Create and manage projects in the sidebar.")
elif nav=="🖥️ Remote": st.sidebar.info("Remote feature is not implemented yet.")
elif nav=="🔲 Explore": st.sidebar.info("More features can be added here.")
st.divider()
st.markdown("<center>✨ <b>NOVA AI</b> • Gemini-first • OpenAI fallback</center>",unsafe_allow_html=True)
