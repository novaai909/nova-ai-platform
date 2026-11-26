
import streamlit as st
import uuid
import ast
import fitz
from google import genai
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816;color:#f5f3ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#100b29,#080817,#10132b);border-right:1px solid #6d28d9}
.nova-hero{text-align:center;padding:12px 0 22px}
.nova-infinity{display:inline-block;font-size:clamp(85px,22vw,150px);line-height:1.05;background:linear-gradient(90deg,#ff36d1,#8b5cf6,#22d3ee,#00ff88,#ff36d1);background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glow 3s ease-in-out infinite,gradient 6s linear infinite;filter:drop-shadow(0 0 15px #a855f7)}
.nova-brand{font-family:cursive;font-size:clamp(42px,10vw,72px);font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899,#00ff88,#a855f7);background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:gradient 6s linear infinite,glow 3s ease-in-out infinite}
.nova-tag{color:white;font-family:cursive;font-size:clamp(22px,6vw,32px);text-shadow:0 0 10px #a855f7}
.nova-splash{position:fixed;inset:0;z-index:999999;background:radial-gradient(circle at center,#26105b,#10102b 42%,#050611);display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden;animation:out 1s ease 6s forwards;pointer-events:none}
.splash-logo{font-size:clamp(90px,25vw,170px);line-height:1;opacity:0;display:inline-block;background:linear-gradient(90deg,#ff00cc,#7c3aed,#00e5ff,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 22px #a855f7);animation:spin-grow 2.3s ease-out forwards,glow 2.4s ease-in-out infinite,gradient 5s linear infinite}
.splash-name{font-family:cursive;font-size:clamp(48px,12vw,85px);font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,#ff00cc,#00e5ff,#a855f7,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;opacity:0;animation:appear 1.6s ease 1.8s forwards,gradient 4s linear infinite,glow 3s ease-in-out infinite}
.splash-welcome{color:white;font-family:cursive;font-size:clamp(23px,6vw,36px);letter-spacing:1px;text-align:center;opacity:0;text-shadow:0 0 12px white;animation:appear 1.5s ease 2.8s forwards}
.bfly{position:absolute;font-size:clamp(23px,5vw,36px);animation:fly 5.5s ease-in-out infinite;filter:drop-shadow(0 0 5px currentColor)}
.bfly:nth-child(odd){animation-name:fly2}.bfly:nth-child(3n){animation-name:fly3}.bfly:nth-child(4n){animation-name:fly4}.bfly:nth-child(5n){animation-name:fly5}
@keyframes spin-grow{0%{opacity:0;transform:scale(.12) rotate(0)}65%{opacity:1;transform:scale(1.35) rotate(300deg)}100%{opacity:1;transform:scale(1) rotate(360deg)}}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 10px #a855f7)}50%{filter:drop-shadow(0 0 30px #22d3ee)}}
@keyframes gradient{0%{background-position:0% 50%}100%{background-position:100% 50%}}
@keyframes appear{to{opacity:1;transform:translateY(0)}from{opacity:0;transform:translateY(25px)}}
@keyframes fly{0%{transform:translate(-8vw,10vh) rotate(-15deg)}25%{transform:translate(24vw,-24vh) rotate(25deg)}50%{transform:translate(45vw,12vh) rotate(-30deg)}75%{transform:translate(-28vw,-18vh) rotate(18deg)}100%{transform:translate(-8vw,10vh) rotate(-15deg)}}
@keyframes fly2{0%{transform:translate(8vw,25vh) rotate(20deg)}25%{transform:translate(-35vw,-20vh) rotate(-25deg)}50%{transform:translate(-15vw,-45vh) rotate(35deg)}75%{transform:translate(35vw,-10vh) rotate(-18deg)}100%{transform:translate(8vw,25vh) rotate(20deg)}}
@keyframes fly3{0%{transform:translate(15vw,-20vh) rotate(5deg)}25%{transform:translate(-40vw,5vh) rotate(35deg)}50%{transform:translate(-20vw,35vh) rotate(-25deg)}75%{transform:translate(40vw,25vh) rotate(20deg)}100%{transform:translate(15vw,-20vh) rotate(5deg)}}
@keyframes fly4{0%{transform:translate(-25vw,-30vh) rotate(-30deg)}25%{transform:translate(35vw,10vh) rotate(20deg)}50%{transform:translate(10vw,40vh) rotate(-10deg)}75%{transform:translate(-40vw,5vh) rotate(30deg)}100%{transform:translate(-25vw,-30vh) rotate(-30deg)}}
@keyframes fly5{0%{transform:translate(0,35vh) rotate(15deg)}25%{transform:translate(38vw,-35vh) rotate(-20deg)}50%{transform:translate(-35vw,-15vh) rotate(30deg)}75%{transform:translate(-10vw,30vh) rotate(-25deg)}100%{transform:translate(0,35vh) rotate(15deg)}}
@keyframes out{to{opacity:0;visibility:hidden}}
</style>
""", unsafe_allow_html=True)

# API setup
try:
    gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Setup error: Streamlit Secrets mein GEMINI_API_KEY, SUPABASE_URL aur SUPABASE_KEY check karein.")
    st.stop()

try:
    openai_client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY","")) if st.secrets.get("OPENAI_API_KEY") else None
except Exception:
    openai_client = None

STORE_ID="nova_main"
PROJECT_META="__nova_projects__"
CHAT_PROJECT_META="__nova_chat_projects__"

def load_data():
    try:
        r=supabase.table("nova_storage").select("*").eq("id",STORE_ID).execute()
        if r.data:
            return r.data[0].get("chats") or {},r.data[0].get("notes") or []
    except Exception as e:
        st.error(f"Database load error: {e}")
    return {},[]

def save_data():
    data=dict(st.session_state.chats)
    data[PROJECT_META]=st.session_state.projects
    data[CHAT_PROJECT_META]=st.session_state.chat_projects
    try:
        supabase.table("nova_storage").upsert({"id":STORE_ID,"chats":data,"notes":st.session_state.notes}).execute()
    except Exception as e:
        st.error(f"Save error: {e}")

def init():
    if st.session_state.get("initialized"):
        return
    data,notes=load_data()
    data=data if isinstance(data,dict) else {}
    projects=data.pop(PROJECT_META,[{"id":"default","name":"General"}])
    chat_projects=data.pop(CHAT_PROJECT_META,{})
    if not projects:
        projects=[{"id":"default","name":"General"}]
    if not data:
        data={"Chat 1":[]}
    for t in data:
        chat_projects.setdefault(t,"default")
    st.session_state.chats=data
    st.session_state.projects=projects
    st.session_state.chat_projects=chat_projects
    st.session_state.notes=notes if isinstance(notes,list) else []
    st.session_state.active_chat=next(iter(data))
    st.session_state.active_project=chat_projects.get(st.session_state.active_chat,"default")
    st.session_state.initialized=True

init()

def chat_list(pid):
    return [t for t in st.session_state.chats if st.session_state.chat_projects.get(t,"default")==pid]

def new_chat(pid):
    name="New Chat"
    k=2
    while name in st.session_state.chats:
        name=f"New Chat {k}"
        k+=1
    st.session_state.chats[name]=[]
    st.session_state.chat_projects[name]=pid
    st.session_state.active_chat=name
    st.session_state.active_project=pid
    save_data()

def new_project(name):
    if name.strip():
        pid=str(uuid.uuid4())[:8]
        st.session_state.projects.append({"id":pid,"name":name.strip()})
        new_chat(pid)

def ask_ai(prompt,history=None):
    history=history or []
    prior="\n".join(f"{m['role']}: {m['content']}" for m in history[-12:])
    full="You are NOVA AI, a helpful assistant. Respond in the user's language.\n"+prior+"\nUser: "+prompt
    errors=[]
    for model in ["gemini-2.5-flash","gemini-2.0-flash","gemini-2.5-flash-lite"]:
        try:
            res=gemini.models.generate_content(model=model,contents=full)
            if res.text:
                return res.text,f"Gemini • {model}"
        except Exception as e:
            errors.append(str(e)[:140])
    if openai_client:
        try:
            res=openai_client.chat.completions.create(model="gpt-4.1-mini",messages=[{"role":"user","content":full}])
            return res.choices[0].message.content,"OpenAI fallback"
        except Exception as e:
            errors.append(str(e)[:140])
    return "AI request failed. Check API keys and quotas. "+" ".join(errors),"Error"

# Sidebar
with st.sidebar:
    st.markdown("# ✨ NOVA AI")
    if st.button("➕ New Chat",use_container_width=True):
        new_chat(st.session_state.active_project)
        st.rerun()

    search=st.text_input("🔎 Search chats",key="chat_search")
    st.divider()

    feature=st.selectbox("Open feature",["💬 AI Chat","📄 PDF Assistant","✍️ Writing Studio","🧠 My Notes","🧮 Calculator"])

    st.divider()
    st.markdown("### 📁 Projects")

    for p in st.session_state.projects:
        pid=p["id"]
        if st.button("📁 "+p["name"],key="project_"+pid,use_container_width=True):
            st.session_state.active_project=pid
            items=chat_list(pid)
            if items:
                st.session_state.active_chat=items[0]
            else:
                new_chat(pid)
            st.rerun()

        for title in chat_list(pid):
            if search and search.lower() not in title.lower():
                continue
            if st.button("↳ "+title,key="chat_"+title):
                st.session_state.active_chat=title
                st.session_state.active_project=pid
                st.rerun()

    with st.expander("➕ Create project"):
        pn=st.text_input("Project name",key="project_input")
        if st.button("Create",key="create_project"):
            new_project(pn)
            st.rerun()

    with st.expander("⚙️ Manage chats"):
        old=st.selectbox("Rename chat",list(st.session_state.chats),key="rename_pick")
        new_title=st.text_input("New chat name",key="rename_text")
        c1,c2=st.columns(2)

        with c1:
            if st.button("Rename",key="rename_chat"):
                if new_title.strip() and new_title.strip() not in st.session_state.chats:
                    st.session_state.chats[new_title.strip()]=st.session_state.chats.pop(old)
                    st.session_state.chat_projects[new_title.strip()]=st.session_state.chat_projects.pop(old,"default")
                    if st.session_state.active_chat==old:
                        st.session_state.active_chat=new_title.strip()
                    save_data()
                    st.rerun()

        with c2:
            if st.button("Delete chat",key="delete_chat"):
                if len(st.session_state.chats)>1:
                    st.session_state.chats.pop(old)
                    st.session_state.chat_projects.pop(old,None)
                    if st.session_state.active_chat==old:
                        st.session_state.active_chat=next(iter(st.session_state.chats))
                        st.session_state.active_project=st.session_state.chat_projects.get(st.session_state.active_chat,"default")
                    save_data()
                    st.rerun()

    st.caption("Gemini first • OpenAI fallback")

# Splash screen
if not st.session_state.get("splash_seen",False):
    b=[]
    for i in range(26):
        left=(i*37+11)%94
        top=(i*53+7)%88
        hue=(i*47)%360
        delay=(i*.23)%3.8
        duration=4.4+(i%6)*.55
        b.append(f'<div class="bfly" style="left:{left}%;top:{top}%;color:hsl({hue},95%,70%);animation-delay:{delay}s;animation-duration:{duration}s">🦋</div>')

    st.markdown(f'<div class="nova-splash">{"".join(b)}<div class="splash-logo">∞</div><div class="splash-name">NOVA AI</div><div class="splash-welcome">Welcome to NOVA AI</div></div>',unsafe_allow_html=True)
    st.session_state.splash_seen=True

st.markdown('<div class="nova-hero"><div class="nova-infinity">∞</div><div class="nova-brand">NOVA AI</div><div class="nova-tag">Welcome to NOVA AI</div></div>',unsafe_allow_html=True)

# Feature areas
if feature=="💬 AI Chat":
    active=st.session_state.active_chat
    st.markdown(f"### 💬 {active}")
    history=st.session_state.chats.get(active,[])

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt=st.chat_input("Ask NOVA anything...")

    if prompt:
        history.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer,provider=ask_ai(prompt,history[:-1])
            st.markdown(answer)
            st.caption(provider)

        history.append({"role":"assistant","content":answer})
        st.session_state.chats[active]=history

        if active.startswith("New Chat") and len(history)==2:
            title=prompt.strip()[:40] or active
            if title not in st.session_state.chats:
                st.session_state.chats[title]=st.session_state.chats.pop(active)
                st.session_state.chat_projects[title]=st.session_state.chat_projects.pop(active,"default")
                st.session_state.active_chat=title

        save_data()
        st.rerun()

elif feature=="📄 PDF Assistant":
    file=st.file_uploader("Upload PDF",type=["pdf"])
    if file:
        doc=fitz.open(stream=file.read(),filetype="pdf")
        text="\n".join(page.get_text() for page in doc)
        st.success(f"PDF loaded • {len(doc)} pages")
        st.text_area("Extracted text preview",text[:5000],height=180)
        q=st.text_input("Ask something about this PDF",key="pdf_question")
        if st.button("Ask NOVA about PDF") and q:
            answer,provider=ask_ai("Use this PDF content to answer:\n"+text[:30000]+"\n\nQuestion: "+q)
            st.markdown(answer)
            st.caption(provider)

elif feature=="✍️ Writing Studio":
    kind=st.selectbox("Writing task",["Write","Rewrite","Summarize","Translate","Email","Ideas"])
    source=st.text_area("Enter text or instructions",height=200)
    tone=st.selectbox("Tone",["Friendly","Professional","Creative","Simple","Formal"])
    if st.button("Generate writing") and source:
        ans,provider=ask_ai(f"{kind} the following in a {tone} tone:\n{source}")
        st.markdown(ans)
        st.caption(provider)

elif feature=="🧠 My Notes":
    note=st.text_area("Write a note",key="note_text")
    if st.button("Save note") and note.strip():
        st.session_state.notes.append({"id":str(uuid.uuid4()),"text":note.strip()})
        save_data()
        st.rerun()

    st.markdown("### Saved notes")
    for n in list(st.session_state.notes):
        with st.container(border=True):
            st.write(n.get("text",""))
            if st.button("🗑️ Delete",key="note_del_"+n.get("id",str(uuid.uuid4()))):
                st.session_state.notes=[x for x in st.session_state.notes if x.get("id")!=n.get("id")]
                save_data()
                st.rerun()

elif feature=="🧮 Calculator":
    expression=st.text_input("Enter calculation (e.g. 2*(3+4))")
    if st.button("Calculate"):
        try:
            tree=ast.parse(expression,mode="eval")
            allowed=(ast.Expression,ast.Constant,ast.BinOp,ast.UnaryOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Load)
            if all(isinstance(node,allowed) for node in ast.walk(tree)):
                result=eval(compile(tree,"<calc>","eval"),{"__builtins__":{}},{})
                st.success(f"Result: {result}")
            else:
                st.error("Unsupported expression.")
        except Exception:
            st.error("Invalid calculation.")
