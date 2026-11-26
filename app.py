
import streamlit as st
import fitz
import json
from datetime import datetime
from google import genai
from openai import OpenAI

st.set_page_config(page_title="NOVA AI V2", page_icon="✨", layout="wide")

# ---------------- CONFIG ----------------
st.title("✨ NOVA AI")
st.caption("Your All-in-One AI Assistant")

gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

openai_client = None
if st.secrets.get("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

# ---------------- STATE ----------------
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Chat 1"

if "notes" not in st.session_state:
    st.session_state.notes = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

# ---------------- AI ENGINE ----------------
def ask_ai(prompt, history=None):
    history = history or []

    conversation = ""
    for item in history[-12:]:
        conversation += f"\n{item['role']}: {item['content']}\n"

    full_prompt = (
        "You are NOVA AI, a helpful, friendly and capable assistant. "
        "Answer clearly. Use the user's language.\n\n"
        + conversation
        + "\nUser: "
        + prompt
    )

    errors = []

    for model in GEMINI_MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model,
                contents=full_prompt
            )
            if response.text:
                return response.text, f"Gemini ({model})"
        except Exception as e:
            errors.append(str(e))

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are NOVA AI, a helpful assistant."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            answer = response.choices[0].message.content
            if answer:
                return answer, "OpenAI fallback"
        except Exception as e:
            errors.append(str(e))

    return "AI se response nahi mil paaya. API keys ya model availability check karein.", "Error"

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("✨ NOVA Menu")

    section = st.radio(
        "Choose a feature",
        [
            "💬 AI Chat",
            "📄 PDF Assistant",
            "✍️ Writing Studio",
            "🧠 My Notes",
            "🧮 Calculator",
        ],
        key="nova_v2_menu"
    )

    st.divider()
    st.caption("NOVA AI • Version 2")

# ---------------- CHAT ----------------
if section == "💬 AI Chat":
    st.subheader("💬 AI Chat")

    col1, col2 = st.columns([3, 1])

    with col1:
        chat_names = list(st.session_state.chats.keys())
        st.session_state.active_chat = st.selectbox(
            "Your conversations",
            chat_names,
            index=chat_names.index(st.session_state.active_chat)
            if st.session_state.active_chat in chat_names else 0
        )

    with col2:
        if st.button("➕ New Chat", use_container_width=True):
            new_name = f"Chat {len(st.session_state.chats) + 1}"
            st.session_state.chats[new_name] = []
            st.session_state.active_chat = new_name
            st.rerun()

    history = st.session_state.chats[st.session_state.active_chat]

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Message NOVA AI...")

    if prompt:
        history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                answer, provider = ask_ai(prompt, history[:-1])
            st.markdown(answer)
            st.caption(f"Powered by {provider}")

        history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.button("🗑️ Delete this conversation"):
        del st.session_state.chats[st.session_state.active_chat]
        if not st.session_state.chats:
            st.session_state.chats = {"Chat 1": []}
        st.session_state.active_chat = list(st.session_state.chats.keys())[0]
        st.rerun()

# ---------------- PDF ASSISTANT ----------------
elif section == "📄 PDF Assistant":
    st.subheader("📄 PDF Smart Assistant")

    pdf = st.file_uploader("Upload a PDF", type=["pdf"])

    if pdf:
        if pdf.name != st.session_state.pdf_name:
            try:
                doc = fitz.open(stream=pdf.read(), filetype="pdf")
                st.session_state.pdf_text = "\n".join(
                    page.get_text() for page in doc
                )
                st.session_state.pdf_name = pdf.name
            except Exception as e:
                st.error(f"PDF error: {e}")

        if st.session_state.pdf_text:
            st.success(f"Loaded: {pdf.name}")

            pdf_action = st.radio(
                "Choose what NOVA should do",
                ["Ask a question", "Summarize PDF", "Create Quiz"],
                horizontal=True,
                key="nova_pdf_action"
            )

            if pdf_action == "Ask a question":
                question = st.text_input("Your question about the PDF")

                if st.button("🔍 Ask PDF", key="ask_pdf"):
                    if question.strip():
                        prompt = (
                            "Answer based on the PDF text. If the answer isn't "
                            "in the document, say so.\n\nPDF:\n"
                            + st.session_state.pdf_text[:100000]
                            + "\n\nQuestion:\n" + question
                        )
                        with st.spinner("Reading PDF..."):
                            answer, provider = ask_ai(prompt)
                        st.markdown("### Answer")
                        st.markdown(answer)
                        st.caption(provider)

            elif pdf_action == "Summarize PDF":
                summary_length = st.selectbox(
                    "Summary length",
                    ["Short", "Detailed", "Bullet points"]
                )

                if st.button("📝 Generate Summary", key="pdf_summary"):
                    prompt = (
                        f"Create a {summary_length} summary of this PDF.\n\n"
                        + st.session_state.pdf_text[:100000]
                    )
                    with st.spinner("Summarizing PDF..."):
                        answer, provider = ask_ai(prompt)
                    st.markdown(answer)
                    st.caption(provider)

            elif pdf_action == "Create Quiz":
                quiz_count = st.slider("Number of questions", 3, 20, 5)

                if st.button("🎯 Create Quiz", key="pdf_quiz"):
                    prompt = (
                        f"Create {quiz_count} multiple-choice quiz questions "
                        "based on this PDF. Include 4 options per question and "
                        "an answer key at the end.\n\n"
                        + st.session_state.pdf_text[:100000]
                    )
                    with st.spinner("Creating quiz..."):
                        answer, provider = ask_ai(prompt)
                    st.markdown(answer)
                    st.caption(provider)

    else:
        st.info("Upload a PDF to get started.")

# ---------------- WRITING STUDIO ----------------
elif section == "✍️ Writing Studio":
    st.subheader("✍️ AI Writing Studio")

    writing_type = st.selectbox(
        "What do you want to create?",
        [
            "Email",
            "Application",
            "Resume / Bio-data",
            "Essay",
            "Story",
            "Social Media Caption",
            "Letter",
            "Improve my writing",
            "Code Helper",
            "Custom",
        ]
    )

    writing_details = st.text_area(
        "Tell NOVA what to write",
        placeholder="Topic, details, tone, language etc..."
    )

    if st.button("✨ Create", key="writing_create"):
        if writing_details.strip():
            prompt = (
                f"Act as a writing assistant. Writing type: {writing_type}.\n"
                "Create the requested content. Use a suitable format and language.\n\n"
                + writing_details
            )
            with st.spinner("Creating..."):
                answer, provider = ask_ai(prompt)
            st.markdown("### Your Result")
            st.markdown(answer)
            st.caption(provider)
            st.download_button(
                "⬇️ Download text",
                data=answer,
                file_name="nova_writing.txt",
                mime="text/plain"
            )
        else:
            st.warning("Please enter your details.")

# ---------------- NOTES ----------------
elif section == "🧠 My Notes":
    st.subheader("🧠 My Notes")

    with st.form("nova_note_form"):
        note_title = st.text_input("Note title")
        note_content = st.text_area("Write your note")
        save_note = st.form_submit_button("💾 Save Note")

    if save_note:
        if note_title.strip() and note_content.strip():
            st.session_state.notes.append({
                "title": note_title,
                "content": note_content,
                "date": datetime.now().strftime("%d-%m-%Y %H:%M")
            })
            st.success("Note saved!")
            st.rerun()
        else:
            st.warning("Enter both title and note.")

    st.divider()

    if st.session_state.notes:
        for i, note in enumerate(st.session_state.notes):
            with st.expander(f"📌 {note['title']} — {note['date']}"):
                st.write(note["content"])

                st.download_button(
                    "⬇️ Download note",
                    note["content"],
                    file_name=f"note_{i+1}.txt",
                    mime="text/plain",
                    key=f"note_download_{i}"
                )

                if st.button("🗑️ Delete note", key=f"note_delete_{i}"):
                    st.session_state.notes.pop(i)
                    st.rerun()

        all_notes = "\n\n".join(
            f"{n['title']}\n{n['content']}" for n in st.session_state.notes
        )

        st.download_button(
            "⬇️ Download all notes",
            all_notes,
            file_name="nova_all_notes.txt",
            mime="text/plain"
        )
    else:
        st.info("You haven't saved any notes yet.")

# ---------------- CALCULATOR ----------------
elif section == "🧮 Calculator":
    st.subheader("🧮 Calculator")

    a = st.number_input("First number", value=0.0, key="calc_a")
    operation = st.selectbox("Operation", ["+", "-", "×", "÷", "%"])
    b = st.number_input("Second number", value=1.0, key="calc_b")

    if st.button("🟰 Calculate"):
        if operation == "+":
            result = a + b
        elif operation == "-":
            result = a - b
        elif operation == "×":
            result = a * b
        elif operation == "÷":
            if b == 0:
                result = None
                st.error("Cannot divide by zero.")
            else:
                result = a / b
        elif operation == "%":
            result = (a * b) / 100

        if result is not None:
            st.success(f"Result: {result}")

# ---------------- FOOTER ----------------
st.divider()
st.caption("✨ NOVA AI V2 • Made with Streamlit")
