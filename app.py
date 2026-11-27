
import streamlit as st
import uuid, ast, fitz, hashlib, json
import streamlit.components.v1 as components
from google import genai, types
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="NOVA AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
.stApp{
    background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),
    radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816;
    color:#f5f3ff
}
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#100b29,#080817,#10132b);
    border-right:1px solid #6d28d9
}
.nova-hero{text-align:center;padding:12px 0 22px}
.nova-infinity{
    display:inline-block;font-size:clamp(85px,22vw,150px);line-height:1.05;
    background:linear-gradient(90deg,#ff36d1,#8b5cf6,#22d3ee,#00ff88,#ff36d1);
    background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
    animation:glow 3s ease-in-out infinite,gradient 6s linear infinite;
    filter:drop-shadow(0 0 15px #a855f7)
}
.nova-brand{
    font-family:cursive;font-size:clamp(42px,10vw,72px);font-weight:900;letter-spacing:2px;
    background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899,#00ff88,#a855f7);
    background-size:300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
    animation:gradient 6s linear infinite,glow 3s ease-in-out infinite
}
.nova-tag{
    color:white;font-family:cursive;font-size:clamp(22px,6vw,32px);
    text-shadow:0 0 10px #a855f7
}
.nova-splash{
    position:fixed;inset:0;z-index:999999;
    background:radial-gradient(circle at center,#26105b,#10102b 42%,#050611);
    display:flex;align-items:center;justify-content:center;flex-direction:column;
    overflow:hidden;animation:out 1s ease 6s forwards;pointer-events:none
}
.splash-logo{
    font-size:clamp(90px,25vw,170px);line-height:1;opacity:0;
    display:inline-block;background:linear-gradient(90deg,#ff00cc,#7c3aed,#00e5ff,#00ff88,#ff00cc);
    background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 22px #a855f7);
    animation:spin-grow 2.3s ease-out forwards,glow 2.4s ease-in-out infinite,gradient 5s linear infinite
}
.splash-name{
    font-family:cursive;font-size:clamp(48px,12vw,85px);font-weight:900;letter-spacing:2px;
    background:linear-gradient(90deg,#ff00cc,#00e5ff,#a855f7,#00ff88,#ff00cc);
    background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
    opacity:0;animation:appear 1.6s ease 1.8s forwards,gradient 4s linear infinite,glow 3s ease-in-out infinite
}
.splash-welcome{
    color:white;font-family:cursive;font-size:clamp(23px,6vw,36px);
    letter-spacing:1px;text-align:center;opacity:0;text-shadow:0 0 12px white;
    animation:appear 1.5s ease 2.8s forwards
}
.bfly{
    position:absolute;font-size:clamp(23px,5vw,36px);
    animation:fly 5.5s ease-in-out infinite;
    filter:drop-shadow(0 0 5px currentColor)
}
.bfly:nth-child(odd){animation-name:fly2}
.bfly:nth-child(3n){animation-name:fly3}
.bfly:nth-child(4n){animation-name:fly4}
.bfly:nth-child(5n){animation-name:fly5}

@keyframes spin-grow{
    0%{opacity:0;transform:scale(.12) rotate(0)}
    65%{opacity:1;transform:scale(1.35) rotate(300deg)}
    100%{opacity:1;transform:scale(1) rotate(360deg)}
}
@keyframes glow{
    0%,100%{filter:drop-shadow(0 0 10px #a855f7)}
    50%{filter:drop-shadow(0 0 30px #22d3ee)}
}
@keyframes gradient{0%{background-position:0% 50%}100%{background-position:100% 50%}}
@keyframes appear{to{opacity:1;transform:translateY(0)}from{opacity:0;transform:translateY(25px)}}
@keyframes fly{
    0%{transform:translate(-8vw,10vh) rotate(-15deg)}
    25%{transform:translate(24vw,-24vh) rotate(25deg)}
    50%{transform:translate(45vw,12vh) rotate(-30deg)}
    75%{transform:translate(-28vw,-18vh) rotate(18deg)}
    100%{transform:translate(-8vw,10vh) rotate(-15deg)}
}
@keyframes fly2{
    0%{transform:translate(8vw,25vh) rotate(20deg)}
    25%{transform:translate(-35vw,-20vh) rotate(-25deg)}
    50%{transform:translate(-15vw,-45vh) rotate(35deg)}
    75%{transform:translate(35vw,-10vh) rotate(-18deg)}
    100%{transform:translate(8vw,25vh) rotate(20deg)}
}
@keyframes fly3{
    0%{transform:translate(15vw,-20vh) rotate(5deg)}
    25%{transform:translate(-40vw,5vh) rotate(35deg)}
    50%{transform:translate(-20vw,35vh) rotate(-25deg)}
    75%{transform:translate(40vw,25vh) rotate(20deg)}
    100%{transform:translate(15vw,-20vh) rotate(5deg)}
}
@keyframes fly4{
    0%{transform:translate(-25vw,-30vh) rotate(-30deg)}
    25%{transform:translate(35vw,10vh) rotate(20deg)}
    50%{transform:translate(10vw,40vh) rotate(-10deg)}
    75%{transform:translate(-40vw,5vh) rotate(30deg)}
    100%{transform:translate(-25vw,-30vh) rotate(-30deg)}
}
@keyframes fly5{
    0%{transform:translate(0,35vh) rotate(15deg)}
    25%{transform:translate(38vw,-35vh) rotate(-20deg)}
    50%{transform:translate(-35vw,-15vh) rotate(30deg)}
    75%{transform:translate(-10vw,30vh) rotate(-25deg)}
    100%{transform:translate(0,35vh) rotate(15deg)}
}
@keyframes out{to{opacity:0;visibility:hidden}}

/* NOVA Voice Animation */
.voice-flower-stage{
    position:relative;height:520px;width:100%;overflow:hidden;
    border-radius:25px;
    background:radial-gradient(circle,#183c28 0%,#080816 70%);
    display:flex;align-items:center;justify-content:center;
    border:1px solid #6338a8;
}
.voice-butterfly{
    position:absolute;font-size:28px;
    animation:butterfly-flight 7s ease-in-out infinite alternate;
    filter:drop-shadow(0 0 8px #ffb7ff)
}
.voice-butterfly:nth-child(odd){animation-duration:5s}
.voice-butterfly:nth-child(3n){animation-duration:8s}
.voice-butterfly:nth-child(4n){animation-duration:6s}
.voice-sunflower{
    position:relative;z-index:2;font-size:120px;
    animation:flower-open 4s ease-in-out infinite alternate;
    filter:drop-shadow(0 0 20px #ffd700);
    transform-origin:center
}
@keyframes flower-open{
    0%{transform:scale(.55) rotate(-15deg);filter:drop-shadow(0 0 5px #ff9800)}
    100%{transform:scale(1.2) rotate(12deg);filter:drop-shadow(0 0 30px #ffd700)}
}
@keyframes butterfly-flight{
    0%{transform:translate(0,0) rotate(0deg)}
    25%{transform:translate(80px,-110px) rotate(25deg)}
    50%{transform:translate(-100px,80px) rotate(-25deg)}
    75%{transform:translate(120px,100px) rotate(15deg)}
    100%{transform:translate(-70px,-120px) rotate(-15deg)}
}
</style>
""", unsafe_allow_html=True)

# API and database initialization
try:
    gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception:
    st.error("Setup error: Secrets check karein: GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY.")
    st.stop()

try:
    openai_client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    ) if st.secrets.get("OPENAI_API_KEY") else None
except Exception:
    openai_client = None

STORE = "nova_main"
META = "__nova_projects__"
CMETA = "__nova_chat_projects__"

def load():
    try:
        r = supabase.table("nova_storage").select("*").eq("id", STORE).execute()
        if r.data:
            return r.data[0].get("chats") or {}, r.data[0].get("notes") or []
    except Exception as e:
        st.warning(f"Storage read issue: {e}")
    return {}, []

def save():
    packed = dict(st.session_state.chats)
    packed[META] = st.session_state.projects
    packed[CMETA] = st.session_state.chat_projects
    try:
        supabase.table("nova_storage").upsert({
            "id": STORE,
            "chats": packed,
            "notes": st.session_state.notes
        }).execute()
    except Exception as e:
        st.error(f"Save issue: {e}")

def init():
    if st.session_state.get("ready"):
        return

    chats, notes = load()
    chats = chats if isinstance(chats, dict) else {}
    projects = chats.pop(META, [{"id":"default","name":"General"}])
    mapping = chats.pop(CMETA, {})

    if not isinstance(projects, list) or not projects:
        projects = [{"id":"default","name":"General"}]

    if not isinstance(mapping, dict):
        mapping = {}

    if not chats:
        chats = {"Chat 1":[]}

    for t in chats:
        mapping.setdefault(t, "default")

    st.session_state.chats = chats
    st.session_state.projects = projects
    st.session_state.chat_projects = mapping
    st.session_state.notes = notes if isinstance(notes, list) else []
    st.session_state.active_chat = next(iter(chats))
    st.session_state.active_project = mapping.get(
        st.session_state.active_chat, "default"
    )
    st.session_state.ready = True

init()

def chats_in(pid):
    return [
        t for t in st.session_state.chats
        if st.session_state.chat_projects.get(t, "default") == pid
    ]

def create_chat(pid):
    title = "New Chat"
    n = 2
    while title in st.session_state.chats:
        title = f"New Chat {n}"
        n += 1

    st.session_state.chats[title] = []
    st.session_state.chat_projects[title] = pid
    st.session_state.active_chat = title
    st.session_state.active_project = pid
    save()

def create_project(name):
    if name.strip():
        pid = str(uuid.uuid4())[:8]
        st.session_state.projects.append({
            "id":pid,
            "name":name.strip()
        })
        create_chat(pid)

def ask(prompt, history=None):
    history = history or []
    previous = "\n".join(
        f"{m['role']}: {m['content']}" for m in history[-12:]
    )
    full = (
        "You are NOVA AI, a helpful assistant. Answer in the user's language.\n"
        + previous + "\nUser: " + prompt
    )

    errors = []

    for model in ["gemini-3.8-flash", "gemini-3.5-flash"]:
        try:
            result = gemini.models.generate_content(
                model=model,
                contents=full
            )
            if result.text:
                return result.text, "Gemini • " + model
        except Exception as e:
            errors.append(model + ": " + str(e)[:120])

    if openai_client:
        try:
            result = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role":"user","content":full}]
            )
            answer = result.choices[0].message.content
            if answer:
                return answer, "OpenAI fallback"
        except Exception as e:
            errors.append("OpenAI: " + str(e)[:120])

    return (
        "NOVA couldn't connect to its AI providers. Check your Gemini API key, "
        "model access and quota. OpenAI fallback also requires active credits.",
        "Connection error"
    )

# Sidebar
with st.sidebar:
    st.markdown("# ✨ NOVA AI")

    if st.button("➕ New Chat", use_container_width=True):
        create_chat(st.session_state.active_project)
        st.rerun()

    search = st.text_input("🔎 Search chats")

    feature = st.selectbox(
        "Feature",
        ["💬 AI Chat","📄 PDF Assistant","✍️ Writing Studio","🧠 My Notes","🧮 Calculator"]
    )

    st.divider()
    st.markdown("### 📁 Projects")

    for p in st.session_state.projects:
        pid = p["id"]

        if st.button("📁 " + p["name"], key="p_"+pid, use_container_width=True):
            st.session_state.active_project = pid
            listed = chats_in(pid)
            if listed:
                st.session_state.active_chat = listed[0]
            else:
                create_chat(pid)
            st.rerun()

        for title in chats_in(pid):
            if search and search.lower() not in title.lower():
                continue

            if st.button("↳ "+title, key="t_"+title):
                st.session_state.active_chat = title
                st.session_state.active_project = pid
                st.rerun()

    with st.expander("➕ New project"):
        name = st.text_input("Project name", key="project_name")
        if st.button("Create project"):
            create_project(name)
            st.rerun()

    with st.expander("⚙️ Chat management"):
        old = st.selectbox(
            "Chat to rename/delete",
            list(st.session_state.chats),
            key="manage_chat"
        )
        rename = st.text_input("New chat title", key="new_title")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("Rename"):
                if rename.strip() and rename.strip() != old and rename.strip() not in st.session_state.chats:
                    st.session_state.chats[rename.strip()] = st.session_state.chats.pop(old)
                    st.session_state.chat_projects[rename.strip()] = st.session_state.chat_projects.pop(old, "default")

                    if st.session_state.active_chat == old:
                        st.session_state.active_chat = rename.strip()

                    save()
                    st.rerun()

        with c2:
            if st.button("Delete"):
                if len(st.session_state.chats) > 1:
                    st.session_state.chats.pop(old)
                    st.session_state.chat_projects.pop(old, None)

                    if st.session_state.active_chat == old:
                        st.session_state.active_chat = next(iter(st.session_state.chats))
                        st.session_state.active_project = st.session_state.chat_projects.get(
                            st.session_state.active_chat, "default"
                        )

                    save()
                    st.rerun()

    st.caption("Gemini first • OpenAI fallback")

# One-time splash
if not st.session_state.get("splash_seen", False):
    butterflies = []

    for i in range(26):
        x = (i*37+11) % 94
        y = (i*53+7) % 88
        hue = (i*47) % 360
        delay = (i*.23) % 3.8
        duration = 4.4+(i%6)*.55

        butterflies.append(
            f'<div class="bfly" style="left:{x}%;top:{y}%;'
            f'color:hsl({hue},95%,70%);animation-delay:{delay}s;'
            f'animation-duration:{duration}s">🦋</div>'
        )

    st.markdown(
        f'<div class="nova-splash">'
        f'{"".join(butterflies)}'
        f'<div class="splash-logo">∞</div>'
        f'<div class="splash-name">NOVA AI</div>'
        f'<div class="splash-welcome">Welcome to NOVA AI</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.session_state.splash_seen = True

st.markdown(
    '<div class="nova-hero">'
    '<div class="nova-infinity">∞</div>'
    '<div class="nova-brand">NOVA AI</div>'
    '<div class="nova-tag">Welcome to NOVA AI</div>'
    '</div>',
    unsafe_allow_html=True
)
# Features
if feature == "💬 AI Chat":
    title = st.session_state.active_chat
    st.markdown("### 💬 " + title)

    history = st.session_state.chats.get(title, [])

    # Voice input
    st.markdown("### 🎙️ Talk to NOVA")

    voice_audio = st.audio_input("🎤 Record your voice")

    if voice_audio is not None:
        audio_bytes = voice_audio.getvalue()
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()

        if st.session_state.get("last_voice_hash") != audio_hash:
            st.session_state.last_voice_hash = audio_hash

            with st.spinner("NOVA is listening..."):
                try:
                    audio_mime = getattr(
                        voice_audio,
                        "type",
                        None
                    ) or "audio/wav"

                    audio_part = types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=audio_mime
                    )

                    transcription = gemini.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[
                            audio_part,
                            "Transcribe the spoken audio accurately. "
                            "Return only the spoken words."
                        ]
                    )

                    spoken_text = (
                        transcription.text.strip()
                        if transcription.text
                        else ""
                    )

                    if spoken_text:
                        history.append({
                            "role":"user",
                            "content":spoken_text
                        })

                        with st.chat_message("user"):
                            st.markdown("🎙️ " + spoken_text)

                        with st.chat_message("assistant"):
                            with st.spinner("NOVA is thinking..."):
                                answer, provider = ask(
                                    spoken_text,
                                    history[:-1]
                                )

                            st.markdown(answer)
                            st.caption(provider)

                        history.append({
                            "role":"assistant",
                            "content":answer
                        })

                        st.session_state.chats[title] = history

                        if title.startswith("New Chat") and len(history) == 2:
                            auto = spoken_text.strip()[:40] or title

                            if auto not in st.session_state.chats:
                                st.session_state.chats[auto] = (
                                    st.session_state.chats.pop(title)
                                )

                                st.session_state.chat_projects[auto] = (
                                    st.session_state.chat_projects.pop(
                                        title, "default"
                                    )
                                )

                                st.session_state.active_chat = auto

                        save()
                        st.rerun()

                    else:
                        st.warning("No speech detected. Please try again.")

                except Exception as e:
                    st.error(f"Voice error: {e}")

    # Existing chat history
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Text chat
    prompt = st.chat_input("Ask NOVA anything...")

    if prompt:
        history.append({
            "role":"user",
            "content":prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer, provider = ask(prompt, history[:-1])

            st.markdown(answer)
            st.caption(provider)

        history.append({
            "role":"assistant",
            "content":answer
        })

        st.session_state.chats[title] = history

        if title.startswith("New Chat") and len(history) == 2:
            auto = prompt.strip()[:40] or title

            if auto not in st.session_state.chats:
                st.session_state.chats[auto] = (
                    st.session_state.chats.pop(title)
                )

                st.session_state.chat_projects[auto] = (
                    st.session_state.chat_projects.pop(
                        title, "default"
                    )
                )

                st.session_state.active_chat = auto

        save()
        st.rerun()

    # Flower animation and voice reply
    if history and history[-1]["role"] == "assistant":
        voice_text = history[-1]["content"]

        voice_html = '<div class="voice-flower-stage">'

        for i in range(26):
            x = (i*37+11) % 94
            y = (i*53+7) % 88
            delay = (i*.23) % 4

            voice_html += (
                f'<div class="voice-butterfly" '
                f'style="left:{x}%;top:{y}%;animation-delay:{delay}s">'
                f'🦋</div>'
            )

        voice_html += '<div class="voice-sunflower">🌻</div></div>'

        components.html(
            voice_html,
            height=540,
            scrolling=False
        )

        speech_text = json.dumps(voice_text).replace(
            "</", "<\\/"
        )

        components.html(
            f"""
            <button onclick='speakNOVA()'
            style="padding:14px 22px;border-radius:16px;
            background:linear-gradient(90deg,#9333ea,#06b6d4);
            color:white;border:none;font-size:18px;
            font-weight:bold;cursor:pointer;width:100%;">
            🔊 Speak NOVA Answer
            </button>

            <button onclick='stopNOVA()'
            style="padding:12px 22px;border-radius:16px;
            background:#1f2937;color:white;border:none;
            font-size:16px;cursor:pointer;width:100%;margin-top:8px;">
            ⏹️ Stop Voice
            </button>

            <script>
            const novaText = {speech_text};

            function speakNOVA(){{
                window.speechSynthesis.cancel();

                const speech = new SpeechSynthesisUtterance(novaText);
                speech.lang = "en-US";
                speech.rate = 1;
                speech.pitch = 1;

                window.speechSynthesis.speak(speech);
            }}

            function stopNOVA(){{
                window.speechSynthesis.cancel();
            }}
            </script>
            """,
            height=120
        )

elif feature == "📄 PDF Assistant":
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded:
        document = fitz.open(
            stream=uploaded.read(),
            filetype="pdf"
        )

        pdftext = "\n".join(
            page.get_text() for page in document
        )

        st.success(f"PDF loaded: {len(document)} pages")

        question = st.text_input("Ask about the PDF")

        if st.button("Ask NOVA") and question:
            answer, provider = ask(
                "Answer using this document:\n"
                + pdftext[:30000]
                + "\nQuestion: "
                + question
            )

            st.markdown(answer)
            st.caption(provider)

elif feature == "✍️ Writing Studio":
    task = st.selectbox(
        "Task",
        ["Write","Rewrite","Summarize","Translate","Email","Ideas"]
    )

    text = st.text_area("Text or instructions", height=200)

    tone = st.selectbox(
        "Tone",
        ["Friendly","Professional","Creative","Simple","Formal"]
    )

    if st.button("Generate") and text:
        answer, provider = ask(
            f"{task} this in a {tone} tone:\n{text}"
        )

        st.markdown(answer)
        st.caption(provider)

elif feature == "🧠 My Notes":
    note = st.text_area("Write a note", key="note")

    if st.button("Save note") and note.strip():
        st.session_state.notes.append({
            "id":str(uuid.uuid4()),
            "text":note.strip()
        })

        save()
        st.rerun()

    st.markdown("### Saved notes")

    for n in list(st.session_state.notes):
        with st.container(border=True):
            st.write(n.get("text", ""))

            if st.button(
                "🗑️ Delete note",
                key="del_"+n.get("id", "")
            ):
                st.session_state.notes = [
                    x for x in st.session_state.notes
                    if x.get("id") != n.get("id")
                ]

                save()
                st.rerun()

elif feature == "🧮 Calculator":
    expr = st.text_input("Calculation (e.g. 2*(3+4))")

    if st.button("Calculate"):
        try:
            tree = ast.parse(expr, mode="eval")

            allowed = (
                ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Load
            )

            if all(isinstance(n, allowed) for n in ast.walk(tree)):
                result = eval(
                    compile(tree, "<calc>", "eval"),
                    {"__builtins__":{}},
                    {}
                )

                st.success("Result: " + str(result))

            else:
                st.error("Unsupported calculation.")

        except Exception:
            st.error("Invalid calculation.")