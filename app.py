import streamlit as st
import streamlit.components.v1 as components
import fitz
import json
import ast
import time
import uuid
from google import genai, types
from openai import OpenAI

st.set_page_config(
    page_title="NOVA AI",
    page_icon="🦋",
    layout="wide"
)

# ---------------- CONFIG ----------------
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")

gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

MODEL = "gemini-3.8-flash"

# ---------------- SESSION ----------------
defaults = {
    "messages": [],
    "notes": "",
    "feature": "AI Chat",
    "entry_done": False,
    "chat_id": str(uuid.uuid4()),
    "voice_answer": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg,#10091d,#1c1230,#100d20);
    color: #f8f4ff;
}
[data-testid="stSidebar"] {
    background: #170f26;
}
.nova-logo {
    text-align:center;
    font-size:55px;
    font-weight:900;
    color:#e879f9;
    text-shadow:0 0 8px #d946ef,0 0 25px #a855f7,0 0 45px #7c3aed;
    animation: glow 2s infinite alternate;
}
@keyframes glow {
    from {text-shadow:0 0 7px #c026d3,0 0 18px #9333ea;}
    to {text-shadow:0 0 20px #f0abfc,0 0 45px #a855f7,0 0 70px #7c3aed;}
}
.feature-label {
    color:#ff4040;
    font-weight:900;
}
.stButton button {
    border-radius:15px;
    font-weight:bold;
}
.voice-circle button {
    border-radius:50%;
}
.nova-card {
    background:linear-gradient(140deg,#211433,#33204a);
    border:1px solid #76529c;
    border-radius:20px;
    padding:15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- ENTRY ANIMATION ----------------
if not st.session_state.entry_done:
    components.html("""
    <div style="
        height:550px;
        background:radial-gradient(circle,#27113f,#10091d);
        overflow:hidden;
        position:relative;
        font-family:sans-serif;
        text-align:center;">
      <style>
      .butterfly {
        position:absolute;
        font-size:70px;
        animation: fly 5s linear infinite;
        opacity:0.95;
      }
      @keyframes fly {
        0% {transform:translate(-150px,500px) rotate(-20deg);}
        25% {transform:translate(25vw,300px) rotate(25deg);}
        50% {transform:translate(50vw,150px) rotate(-25deg);}
        75% {transform:translate(75vw,300px) rotate(20deg);}
        100% {transform:translate(110vw,-100px) rotate(-20deg);}
      }
      .entry-logo {
        position:absolute;
        top:38%;
        left:0;
        right:0;
        font-size:70px;
        font-weight:900;
        color:#e879f9;
        text-shadow:0 0 20px #d946ef,0 0 50px #a855f7;
        animation:bright 1.8s infinite alternate;
      }
      .entry-welcome {
        position:absolute;
        top:55%;
        left:0;
        right:0;
        color:white;
        font-size:25px;
        font-weight:bold;
      }
      @keyframes bright {
        from {opacity:.65;transform:scale(.96);}
        to {opacity:1;transform:scale(1.05);}
      }
      </style>
      <div class="butterfly" style="top:5%;animation-delay:0s;color:#ff59d6">🦋</div>
      <div class="butterfly" style="top:25%;animation-delay:-1s;color:#44ddff">🦋</div>
      <div class="butterfly" style="top:45%;animation-delay:-2s;color:#ffda44">🦋</div>
      <div class="butterfly" style="top:65%;animation-delay:-3s;color:#8cff80">🦋</div>
      <div class="butterfly" style="top:15%;animation-delay:-4s;color:#ff7a9a">🦋</div>
      <div class="butterfly" style="top:70%;animation-delay:-2.5s;color:#9b8cff">🦋</div>
      <div class="entry-logo">∞ NOVA AI</div>
      <div class="entry-welcome">Welcome to NOVA AI</div>
    </div>
    """, height=560)

    time.sleep(4.5)
    st.session_state.entry_done = True
    st.rerun()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🦋 NOVA AI")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.voice_answer = ""
        st.rerun()

    st.divider()
    st.subheader("Settings")
    st.selectbox("AI provider", ["Gemini", "OpenAI fallback"])

    st.divider()
    st.subheader("Chat History")
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.caption(msg["content"][:50])

# ---------------- MAIN HEADER ----------------
st.markdown('<div class="nova-logo">∞</div>', unsafe_allow_html=True)
st.markdown(
    "<h3 style='text-align:center;color:white;'>Welcome to NOVA AI</h3>",
    unsafe_allow_html=True
)

# ---------------- FEATURE ROW ----------------
feature_names = [
    "💬 AI Chat",
    "📄 PDF Assistant",
    "✍️ Writing Studio",
    "📝 Notes",
    "🧮 Calculator"
]

cols = st.columns(5)
for i, name in enumerate(feature_names):
    with cols[i]:
        if st.button(name, key=f"f_{i}", use_container_width=True):
            st.session_state.feature = name.split(" ", 1)[1]
            st.rerun()

# ---------------- AI FUNCTION ----------------
def ask_nova(prompt):
    if gemini:
        try:
            response = gemini.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            if response.text:
                return response.text
        except Exception as e:
            gemini_error = str(e)
        else:
            gemini_error = "Empty response"
    else:
        gemini_error = "Gemini API key missing"

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI error: {e}"

    return "Gemini error: " + gemini_error

# ---------------- CHAT ----------------
if st.session_state.feature == "AI Chat":
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask NOVA anything...")
    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer = ask_nova(prompt)
                st.markdown(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
# ---------------- PDF ASSISTANT ----------------
if st.session_state.feature == "PDF Assistant":
    st.subheader("📄 PDF Assistant")

    pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])

    if pdf_file:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        pdf_text = "\n".join(page.get_text() for page in doc)

        question = st.text_input("Ask something about the PDF")

        if st.button("Analyze PDF"):
            with st.spinner("Reading PDF..."):
                answer = ask_nova(
                    "Analyze this PDF and answer the question.\n\n"
                    + pdf_text[:40000]
                    + "\n\nQuestion: " + question
                )
            st.markdown(answer)

# ---------------- WRITING STUDIO ----------------
if st.session_state.feature == "Writing Studio":
    st.subheader("✍️ Writing Studio")

    writing_type = st.selectbox(
        "Select writing type",
        ["Email", "Essay", "Story", "Post", "Letter", "Rewrite"]
    )
    writing_prompt = st.text_area("Your writing instructions")

    if st.button("Generate Writing"):
        if writing_prompt:
            with st.spinner("Writing..."):
                st.markdown(
                    ask_nova(
                        f"Write a {writing_type}. "
                        + writing_prompt
                    )
                )

# ---------------- NOTES ----------------
if st.session_state.feature == "Notes":
    st.subheader("📝 Notes")

    st.session_state.notes = st.text_area(
        "Write and save your notes",
        value=st.session_state.notes,
        height=300
    )

    st.download_button(
        "Download notes",
        data=st.session_state.notes,
        file_name="nova_notes.txt"
    )

# ---------------- CALCULATOR ----------------
if st.session_state.feature == "Calculator":
    st.subheader("🧮 Calculator")

    expression = st.text_input("Enter calculation")

    def safe_calculate(expression):
        allowed = (
            ast.Expression, ast.Constant, ast.BinOp,
            ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
            ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
            ast.USub, ast.UAdd
        )

        tree = ast.parse(expression, mode="eval")

        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError("Unsupported expression")

        return eval(
            compile(tree, "<calculator>", "eval"),
            {"__builtins__": {}}
        )

    if st.button("Calculate"):
        try:
            st.success(str(safe_calculate(expression)))
        except Exception:
            st.error("Invalid calculation")

# ---------------- VOICE SECTION ----------------
st.divider()

st.markdown("### 🌻 NOVA Voice")

# Small voice launcher button near the chat area
voice_col1, voice_col2 = st.columns([9, 1])

with voice_col1:
    st.caption("Talk to NOVA AI")

with voice_col2:
    voice_open = st.button("🎙", key="voice_open")

if voice_open:
    st.session_state.voice_opened = True

if st.session_state.get("voice_opened", False):

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#24143c,#392252);
        border:1px solid #8b5cf6;
        border-radius:25px;
        padding:25px;
        text-align:center;">
        <div style="font-size:85px;
        animation:sunPulse 1.8s infinite alternate;">
        🌻
        </div>
        <div style="font-size:23px;
        font-weight:bold;color:#f3d9ff;">
        NOVA AI VOICE
        </div>
        <style>
        @keyframes sunPulse {
          from {transform:scale(.92);filter:brightness(.8);}
          to {transform:scale(1.08);filter:brightness(1.3);}
        }
        </style>
    </div>
    """, unsafe_allow_html=True)

    voice_audio = st.audio_input("Record your voice")

    if voice_audio and gemini:
        try:
            audio_part = types.Part.from_bytes(
                data=voice_audio.getvalue(),
                mime_type=voice_audio.type or "audio/wav"
            )

            with st.spinner("Listening..."):
                transcript_response = gemini.models.generate_content(
                    model=MODEL,
                    contents=[
                        "Transcribe this recording accurately. "
                        "Return only the spoken words.",
                        audio_part
                    ]
                )

            spoken_text = transcript_response.text.strip()

            st.markdown("#### You said:")
            st.write(spoken_text)

            with st.spinner("NOVA is thinking..."):
                voice_answer = ask_nova(spoken_text)

            st.session_state.voice_answer = voice_answer

            st.markdown("#### 🌻 NOVA Answer")
            st.markdown(voice_answer)

        except Exception as e:
            st.error(f"Voice error: {e}")

    elif voice_audio and not gemini:
        st.error("Gemini API key is missing.")

    if st.session_state.voice_answer:

        safe_text = json.dumps(
            st.session_state.voice_answer
        )

        components.html(f"""
        <div style="display:flex;justify-content:flex-end;
        gap:10px;flex-wrap:wrap;">
          <button onclick="speakNova()" style="
            background:linear-gradient(90deg,#ff3864,#a855f7,#00cfff);
            color:white;border:none;border-radius:30px;
            padding:13px 18px;font-weight:bold;">
            🔊 Speak NOVA Answer
          </button>

          <button onclick="stopNova()" style="
            background:#352343;color:white;
            border:1px solid #76529c;
            border-radius:30px;padding:13px 18px;">
            ⏹ Stop Voice
          </button>
        </div>

        <script>
        const novaText = {safe_text};

        function speakNova() {{
          window.speechSynthesis.cancel();

          const speech = new SpeechSynthesisUtterance(novaText);
          speech.rate = 0.85;
          speech.pitch = 1.0;
          speech.volume = 1.0;

          const voices = window.speechSynthesis.getVoices();

          const preferred = voices.find(v =>
            /Google|Natural/i.test(v.name)
          );

          if (preferred) speech.voice = preferred;

          window.speechSynthesis.speak(speech);
        }}

        function stopNova() {{
          window.speechSynthesis.cancel();
        }}
        </script>
        """, height=90)

    if st.button("Close Voice"):
        st.session_state.voice_opened = False
        st.session_state.voice_answer = ""
        st.rerun()

# ---------------- FOOTER ----------------
st.markdown("""
<div style="
text-align:center;
padding:25px;
color:#c8a9e8;">
🦋 NOVA AI • ∞ • 🌻
</div>
""", unsafe_allow_html=True)