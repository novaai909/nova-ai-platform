import streamlit as st
import uuid, json, ast, hashlib
import streamlit.components.v1 as components
import fitz

from google import genai
from google.genai import types
from openai import OpenAI

st.set_page_config(
    page_title="NOVA AI",
    page_icon="🦋",
    layout="wide"
)

# --------- SECRETS / CLIENTS ----------
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")

gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# --------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "feature" not in st.session_state:
    st.session_state.feature = "AI Chat"

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "notes" not in st.session_state:
    st.session_state.notes = ""

# --------- CSS ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#100d1c,#19152b,#21142b);
    color: white;
}
[data-testid="stSidebar"] {
    background: #171322;
}
.nova-title {
    font-size: 48px;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg,#ff4d6d,#a855f7,#00d4ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.nova-welcome {
    text-align: center;
    font-size: 23px;
    color: #f2d9ff;
    font-weight: 700;
}
.feature-name {
    color: #ff4545 !important;
    font-weight: 800 !important;
}
.voice-box {
    background: linear-gradient(135deg,#211936,#31204b);
    border: 1px solid #59416d;
    border-radius: 22px;
    padding: 16px;
}
div[data-testid="stChatInput"] {
    border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)

# --------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## 🦋 NOVA AI")

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")
    st.markdown("### Settings")

    st.selectbox(
        "AI Model",
        ["Gemini", "OpenAI fallback"],
        key="model_choice"
    )

    st.markdown("### Projects")
    st.markdown("### Chat History")

    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.caption(msg["content"][:45])

# --------- ENTRY ----------
st.markdown('<div class="nova-title">∞ NOVA AI</div>',
            unsafe_allow_html=True)

st.markdown(
    '<div class="nova-welcome">Welcome to NOVA AI 🦋</div>',
    unsafe_allow_html=True
)

st.write("")

# --------- FEATURES SINGLE ROW ----------
features = [
    "💬 AI Chat",
    "📄 PDF Assistant",
    "✍️ Writing Studio",
    "📝 Notes",
    "🧮 Calculator"
]

feature_cols = st.columns(5)

for i, name in enumerate(features):
    with feature_cols[i]:
        if st.button(name, key=f"feature_{i}",
                     use_container_width=True):
            st.session_state.feature = name.split(" ",1)[1]
            st.rerun()

st.markdown("""
<style>
div.stButton > button {
    border-radius: 14px;
    min-height: 43px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# --------- AI ----------
def ask_nova(prompt):
    try:
        if gemini:
            response = gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response.text:
                return response.text
    except Exception as e:
        st.warning(f"Gemini issue: {e}")

    try:
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI issue: {e}")

    return "NOVA AI could not respond. Please check your API keys."

# --------- CHAT ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.feature == "AI Chat":
    prompt = st.chat_input("Ask NOVA anything...")

    if prompt:
        st.session_state.messages.append(
            {"role":"user","content":prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer = ask_nova(prompt)
                st.markdown(answer)

        st.session_state.messages.append(
            {"role":"assistant","content":answer}
        )
# --------- OTHER FEATURES ----------
if st.session_state.feature == "PDF Assistant":
    st.subheader("📄 PDF Assistant")
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf:
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        pdf_text = "\n".join(page.get_text() for page in doc)

        question = st.text_input("Ask about your PDF")

        if st.button("Ask PDF"):
            answer = ask_nova(pdf_text[:15000] + "\n\nQuestion: " + question)
            st.write(answer)

if st.session_state.feature == "Writing Studio":
    st.subheader("✍️ Writing Studio")

    writing_type = st.selectbox(
        "Writing type",
        ["Email","Essay","Story","Social Media","Rewrite"]
    )

    writing_prompt = st.text_area("What should NOVA write?")

    if st.button("Write"):
        if writing_prompt:
            st.markdown(ask_nova(
                f"Write a {writing_type}: {writing_prompt}"
            ))

if st.session_state.feature == "Notes":
    st.subheader("📝 My Notes")

    st.session_state.notes = st.text_area(
        "Your notes",
        value=st.session_state.notes,
        height=250
    )

    st.download_button(
        "Download Notes",
        st.session_state.notes,
        file_name="nova_notes.txt"
    )

if st.session_state.feature == "Calculator":
    st.subheader("🧮 Calculator")

    calc_input = st.text_input("Enter calculation")

    def safe_calc(expression):
        allowed = (
            ast.Expression, ast.Constant, ast.BinOp,
            ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
            ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
            ast.USub, ast.UAdd
        )

        tree = ast.parse(expression, mode="eval")

        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError("Invalid expression")

        return eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}})

    if st.button("Calculate"):
        try:
            st.success(str(safe_calc(calc_input)))
        except Exception:
            st.error("Invalid calculation")

# --------- VOICE SECTION ----------
st.markdown("---")
st.markdown("### 🌻 NOVA Voice")

voice_col1, voice_col2 = st.columns([5,1])

with voice_col1:
    st.markdown("""
    <div class="voice-box">
        <div style="font-size:22px;text-align:center">
        🌻
        </div>
        <div style="text-align:center;color:#e8d8ff">
        Talk to NOVA AI
        </div>
    </div>
    """, unsafe_allow_html=True)

with voice_col2:
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#ff3864,#a855f7,#00cfff);
        border-radius:18px;
        padding:13px 5px;
        text-align:center;
        color:white;
        font-weight:bold;">
        ✦ NOVA
    </div>
    """, unsafe_allow_html=True)

voice_audio = st.audio_input("🎤 Record your voice")

if voice_audio:
    if not gemini:
        st.error("Gemini API key is missing.")
    else:
        try:
            audio_part = types.Part.from_bytes(
                data=voice_audio.getvalue(),
                mime_type=voice_audio.type or "audio/wav"
            )

            transcription = gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Transcribe the audio accurately. Return only the spoken words.",
                    audio_part
                ]
            )

            spoken_text = transcription.text.strip()

            st.markdown("#### You said:")
            st.write(spoken_text)

            with st.spinner("NOVA is thinking..."):
                voice_answer = ask_nova(spoken_text)

            st.markdown("#### 🌻 NOVA Answer")
            st.markdown(voice_answer)

            # Speech controls
            safe_text = json.dumps(voice_answer)

            components.html(f"""
            <div style="
                display:flex;
                gap:10px;
                justify-content:flex-end;
                flex-wrap:wrap;">
                <button onclick="speakNova()"
                style="
                border:none;
                border-radius:30px;
                padding:12px 18px;
                color:white;
                font-weight:bold;
                background:linear-gradient(90deg,#ff3864,#a855f7,#00cfff);
                cursor:pointer;">
                🔊 Speak NOVA Answer
                </button>

                <button onclick="stopNova()"
                style="
                border:none;
                border-radius:30px;
                padding:12px 18px;
                color:white;
                background:#393044;
                cursor:pointer;">
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
                    v.lang.startsWith("en") &&
                    /Google|Natural|Premium/i.test(v.name)
                );

                if(preferred) speech.voice = preferred;

                window.speechSynthesis.speak(speech);
            }}

            function stopNova() {{
                window.speechSynthesis.cancel();
            }}
            </script>
            """, height=75)

            st.session_state.messages.append(
                {"role":"user","content":spoken_text}
            )
            st.session_state.messages.append(
                {"role":"assistant","content":voice_answer}
            )

        except Exception as e:
            st.error(f"Voice error: {e}")

# --------- FOOTER ----------
st.markdown("""
<div style="
text-align:center;
padding:20px;
color:#b8a6d9;">
🦋 NOVA AI • Made with love 🌻
</div>
""", unsafe_allow_html=True)