
import os, io, json, requests, math
import streamlit as st
import streamlit.components.v1 as components
from google import genai

st.set_page_config(page_title="NOVA AI", page_icon="🦋", layout="wide")

# ---------- NOVA ENTRY SPLASH ----------
components.html("""
<div id="novaIntro">
  <div class="butterflies"></div>
  <div class="introText">
    <div class="novaLogo">🦋 NOVA AI</div>
    <div class="novaSub">Your AI Companion</div>
  </div>
</div>
<style>
#novaIntro{
 position:fixed; inset:0; z-index:999999;
 background:linear-gradient(135deg,#080b20,#25104b,#103552);
 display:flex; justify-content:center; align-items:center;
 animation:introFade 1s ease-in-out forwards;
 pointer-events:none;
}
.introText{ text-align:center; color:white; }
.novaLogo{font-size:48px;font-weight:900;text-shadow:0 0 25px #b78aff;}
.novaSub{font-size:18px;letter-spacing:4px;margin-top:10px;}
.butterflies:before{
 content:"🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋";
 position:absolute;top:15%;left:0;width:100%;
 font-size:28px;word-spacing:25px;
 animation:fly1 8s linear infinite;
}
.butterflies:after{
 content:"🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋 🦋";
 position:absolute;bottom:18%;left:0;width:100%;
 font-size:25px;word-spacing:30px;
 animation:fly2 7s linear infinite;
}
@keyframes introFade{
 0%{opacity:1;}
 70%{opacity:1;}
 100%{opacity:0;visibility:hidden;}
}
@keyframes fly1{
 0%{transform:translateX(-15%) translateY(0);}
 50%{transform:translateX(15%) translateY(40px);}
 100%{transform:translateX(-15%) translateY(0);}
}
@keyframes fly2{
 0%{transform:translateX(15%) translateY(0);}
 50%{transform:translateX(-15%) translateY(-40px);}
 100%{transform:translateX(15%) translateY(0);}
}
</style>
""",height=0)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp{
 background:linear-gradient(135deg,#080b20,#17123b 55%,#102744);
 color:#f7f7ff;
}
[data-testid="stSidebar"]{background:#10152b;}
div.stButton>button{
 border-radius:14px;min-height:44px;font-weight:600;
}
</style>
""",unsafe_allow_html=True)

st.title("🦋 NOVA AI")
st.caption("Your AI companion for learning, creating and exploring.")

# ---------- API ----------
api_key=os.getenv("GEMINI_API_KEY","")
if not api_key:
    api_key=st.sidebar.text_input("Gemini API Key",type="password")

gc=genai.Client(api_key=api_key) if api_key else None
model_name="gemini-2.5-flash"

# ---------- SESSION ----------
defaults={
 "feedback_log":[],"nova_notes":[],"chat_history":[],
 "pdf_answer":"","writing_answer":"","calc_answer":"",
 "search_answer":"","search_results":[],
 "translation_answer":"","study_answer":"",
 "website_answer":"","code_answer":"",
 "generated_image_bytes":None,"nova_voice_answer":"",
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- SPEAKER AND FEEDBACK ----------
def answer_controls(text,key,lang="auto"):
    safe_text=json.dumps(str(text))
    safe_lang=json.dumps(lang)
    c1,c2,c3,c4=st.columns(4)

    with c1:
        components.html(f"""
        <button onclick="speakNOVA()"
        style="width:100%;height:48px;border-radius:12px;
        background:#6d28d9;color:white;border:0;font-size:20px">
        🔊
        </button>
        <script>
        const novatxt={safe_text};
        const novalang={safe_lang};
        function speakNOVA(){{
          const s=window.parent.speechSynthesis;
          if(!s)return;
          s.cancel();
          let u=new window.parent.SpeechSynthesisUtterance(novatxt);
          u.rate=0.95;
          if(novalang!=="auto")u.lang=novalang;
          s.speak(u);
        }}
        </script>
        """,height=55)

    with c2:
        components.html("""
        <button onclick="window.parent.speechSynthesis.cancel()"
        style="width:100%;height:48px;border-radius:12px;
        background:#b91c1c;color:white;border:0;font-size:20px">
        ❌
        </button>
        """,height=55)

    with c3:
        if st.button("👍",key=f"{key}_like",use_container_width=True):
            st.session_state.feedback_log.append(
                {"feature":key,"rating":"positive"}
            )
            st.toast("Thanks for feedback 👍")

    with c4:
        if st.button("👎",key=f"{key}_dislike",use_container_width=True):
            st.session_state.feedback_log.append(
                {"feature":key,"rating":"negative"}
            )
            st.toast("Feedback noted 👎")

# ---------- AI HELPER ----------
def ask_gemini(prompt,model=None):
    if gc is None:
        st.error("GEMINI_API_KEY is missing.")
        return None
    try:
        response=gc.models.generate_content(
            model=model or model_name,
            contents=prompt
        )
        return response.text or "NOVA could not create a response."
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return None

# ---------- NAVIGATION ----------
features=[
 "💬 AI Chat","📄 PDF Assistant","✍️ Writing Studio",
 "📝 My Notes","🧮 Calculator","🌻 NOVA Voice",
 "🔎 AI Web Search","🌐 Translator","📚 AI Study Mode",
 "🌍 Website Reader","💻 Coding Lab","🎨 AI Image Generator"
]
feature=st.sidebar.radio("Choose a feature",features)

# ---------- AI CHAT ----------
if feature=="💬 AI Chat":
    st.header("💬 NOVA AI Chat")
    for i,(q,a) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.markdown(a)
            answer_controls(a,f"chat{i}")

    question=st.chat_input("Ask NOVA anything...")
    if question:
        answer=ask_gemini(question)
        if answer:
            st.session_state.chat_history.append((question,answer))
            st.rerun()

# ---------- PDF ----------
elif feature=="📄 PDF Assistant":
    st.header("📄 PDF Assistant")
    pdf=st.file_uploader("Upload PDF",type=["pdf"])
    prompt=st.text_input("Ask about the PDF")

    if pdf and prompt and st.button("Ask about PDF"):
        try:
            import fitz
            doc=fitz.open(stream=pdf.read(),filetype="pdf")
            text="\n".join(p.get_text() for p in doc)
            answer=ask_gemini(
                "Answer using this PDF content:\n"+
                text[:100000]+"\nQuestion:"+prompt
            )
            if answer:
                st.session_state.pdf_answer=answer
        except Exception as e:
            st.error(f"PDF error: {e}")

    if st.session_state.pdf_answer:
        st.markdown(st.session_state.pdf_answer)
        answer_controls(st.session_state.pdf_answer,"pdfanswer")

# ---------- WRITING STUDIO ----------
elif feature=="✍️ Writing Studio":
    st.header("✍️ NOVA Writing Studio")
    kind=st.selectbox(
        "Writing type",
        ["Email","Essay","Story","Social media post",
         "Letter","Resume / CV","Other"]
    )
    tone=st.selectbox(
        "Tone",["Friendly","Professional","Formal",
                 "Creative","Simple","Persuasive"]
    )
    prompt=st.text_area("What should NOVA write?")

    if st.button("Create writing") and prompt:
        answer=ask_gemini(f"Create {kind} in a {tone} tone:\n{prompt}")
        if answer:
            st.session_state.writing_answer=answer

    if st.session_state.writing_answer:
        st.markdown(st.session_state.writing_answer)
        answer_controls(st.session_state.writing_answer,"writing")

# ---------- NOTES ----------
elif feature=="📝 My Notes":
    st.header("📝 My Notes")
    note=st.text_area("Write a note")

    if st.button("Save note") and note.strip():
        st.session_state.nova_notes.append(note)
        st.success("Note saved")

    for i,n in enumerate(st.session_state.nova_notes):
        with st.expander(f"Note {i+1}"):
            st.write(n)
            answer_controls(n,f"note{i}")

# ---------- CALCULATOR ----------
elif feature=="🧮 Calculator":
    st.header("🧮 Calculator")
    expr=st.text_input("Arithmetic expression")

    if st.button("Calculate"):
        try:
            if not expr or any(
                c not in "0123456789+-*/(). %"
                for c in expr
            ):
                raise ValueError("Only basic arithmetic allowed.")
            result=eval(expr,{"__builtins__":{}},{})
            st.session_state.calc_answer=f"{expr} = {result}"
        except Exception as e:
            st.error(str(e))

    if st.session_state.calc_answer:
        st.write(st.session_state.calc_answer)
        answer_controls(st.session_state.calc_answer,"calculator")

# ---------- NOVA VOICE ----------
elif feature=="🌻 NOVA Voice":
    st.header("🌻 NOVA Voice")
    st.markdown("### 🎙️ NOVA Voice Assistant")

    language_options={
        "Auto detect":"auto","Hindi":"hi-IN","English":"en-US",
        "Urdu":"ur-PK","Punjabi":"pa-IN","Bengali":"bn-IN",
        "Tamil":"ta-IN","Telugu":"te-IN","Marathi":"mr-IN",
        "Gujarati":"gu-IN","Kannada":"kn-IN",
        "Malayalam":"ml-IN","Spanish":"es-ES","French":"fr-FR",
        "German":"de-DE","Arabic":"ar-SA","Chinese":"zh-CN",
        "Japanese":"ja-JP","Korean":"ko-KR",
        "Portuguese":"pt-BR","Russian":"ru-RU",
        "Italian":"it-IT","Turkish":"tr-TR","Nepali":"ne-NP"
    }
    voice_lang_label=st.selectbox(
        "Language",list(language_options.keys())
    )
    voice_lang=language_options[voice_lang_label]

    st.markdown("""
    <style>
    div.stButton>button{
       min-height:75px!important;
       font-size:25px!important;
    }
    </style>
    """,unsafe_allow_html=True)

    audio=st.audio_input("🎙️ Record your question")
    if audio:
        st.audio(audio)

    if st.button("▶️ START NOVA",type="primary",
                 use_container_width=True) and audio:
        if gc:
            try:
                audio_part=genai.types.Part.from_bytes(
                    data=audio.getvalue(),
                    mime_type=audio.type or "audio/wav"
                )
                instruction=(
                    "Answer in the language spoken in the recording."
                    if voice_lang=="auto"
                    else f"Answer in {voice_lang_label}."
                )
                response=gc.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        audio_part,
                        "Understand this audio and answer conversationally. "
                        +instruction
                    ]
                )
                st.session_state.nova_voice_answer=response.text
                st.session_state.nova_voice_lang=voice_lang
            except Exception as e:
                st.error(f"Voice error: {e}")
        else:
            st.error("Gemini API key is missing.")

    if st.button("⏹ STOP NOVA",use_container_width=True):
        st.session_state.nova_voice_answer=""
        components.html(
            "<script>window.parent.speechSynthesis.cancel();</script>",
            height=0
        )

    if st.session_state.nova_voice_answer:
        st.markdown("### 💬 NOVA Response")
        st.write(st.session_state.nova_voice_answer)
        answer_controls(
            st.session_state.nova_voice_answer,
            "voiceanswer",
            st.session_state.get("nova_voice_lang","auto")
        )

    st.warning(
        "This version uses recording and submission, "
        "not continuous real-time conversation."
    )

# ---------- WEB SEARCH ----------
elif feature=="🔎 AI Web Search":
    st.header("🔎 AI Web Search")
    query=st.text_input("Search the web")
    tavily_key=os.getenv("TAVILY_API_KEY","")

    if st.button("Search and summarize") and query:
        if tavily_key:
            try:
                r=requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key":tavily_key,
                        "query":query,
                        "search_depth":"basic"
                    },
                    timeout=25
                )
                r.raise_for_status()
                results=r.json().get("results",[])
                source_text="\n".join(
                    f"{x.get('title','')}\n{x.get('url','')}\n"
                    f"{x.get('content','')}"
                    for x in results
                )
                answer=ask_gemini(
                    "Summarize these search results:\n"+source_text
                )
                st.session_state.search_answer=answer
                st.session_state.search_results=results
            except Exception as e:
                st.error(f"Search error: {e}")
        else:
            st.warning("TAVILY_API_KEY is missing.")

    if st.session_state.search_answer:
        st.markdown(st.session_state.search_answer)
        answer_controls(st.session_state.search_answer,"search")
        for item in st.session_state.get("search_results",[]):
            st.markdown(
                f"- [{item.get('title','Source')}]"
                f"({item.get('url','')})"
            )

# ---------- TRANSLATOR ----------
elif feature=="🌐 Translator":
    st.header("🌐 NOVA Translator")
    target=st.selectbox(
        "Translate to",
        ["Hindi","English","Urdu","Punjabi","Bengali",
         "Tamil","Telugu","Marathi","Gujarati","Kannada",
         "Malayalam","Spanish","French","German","Arabic",
         "Chinese","Japanese","Korean","Portuguese",
         "Russian","Italian","Turkish","Nepali","Other"]
    )
    text_in=st.text_area("Text to translate")

    if st.button("Translate") and text_in:
        answer=ask_gemini(
            f"Translate to {target}. Return translation only:\n{text_in}"
        )
        if answer:
            st.session_state.translation_answer=answer

    if st.session_state.translation_answer:
        st.markdown(st.session_state.translation_answer)
        answer_controls(st.session_state.translation_answer,"translate")

# ---------- STUDY MODE ----------
elif feature=="📚 AI Study Mode":
    st.header("📚 AI Study Mode")
    topic=st.text_area("Topic or question")
    level=st.selectbox(
        "Learning level",
        ["Beginner","School","High school","College","Advanced"]
    )
    action=st.selectbox(
        "Study tool",
        ["Explain","Quiz me","Make flashcards",
         "Summarize","Create study plan"]
    )

    if st.button("Start studying") and topic:
        answer=ask_gemini(
            f"{action} about {topic} for a {level} learner."
        )
        if answer:
            st.session_state.study_answer=answer

    if st.session_state.study_answer:
        st.markdown(st.session_state.study_answer)
        answer_controls(st.session_state.study_answer,"study")

# ---------- WEBSITE READER ----------
elif feature=="🌍 Website Reader":
    st.header("🌍 Website Reader")
    url=st.text_input("Website URL")

    if st.button("Read website") and url:
        try:
            from bs4 import BeautifulSoup
            if not url.startswith(("http://","https://")):
                raise ValueError("URL must start with http:// or https://")
            resp=requests.get(
                url,headers={"User-Agent":"Mozilla/5.0"},timeout=20
            )
            resp.raise_for_status()
            soup=BeautifulSoup(resp.text,"html.parser")
            for tag in soup(["script","style","noscript"]):
                tag.decompose()
            text=soup.get_text(" ",strip=True)[:50000]
            answer=ask_gemini(
                "Summarize this website simply:\n"+text
            )
            if answer:
                st.session_state.website_answer=answer
        except Exception as e:
            st.error(f"Website error: {e}")

    if st.session_state.website_answer:
        st.markdown(st.session_state.website_answer)
        answer_controls(st.session_state.website_answer,"website")

# ---------- CODING LAB ----------
elif feature=="💻 Coding Lab":
    st.header("💻 NOVA Coding Lab")
    language=st.selectbox(
        "Programming language",
        ["Python","JavaScript","HTML/CSS","Java","C++","SQL","Other"]
    )
    task=st.text_area("Describe your coding task")
    mode=st.selectbox(
        "Mode",["Write code","Explain code","Debug code","Improve code"]
    )

    if st.button("Run NOVA Coding Lab") and task:
        answer=ask_gemini(f"{mode} in {language}:\n{task}")
        if answer:
            st.session_state.code_answer=answer

    if st.session_state.code_answer:
        st.markdown(st.session_state.code_answer)
        answer_controls(st.session_state.code_answer,"coding")

# ---------- IMAGE GENERATOR ----------
elif feature=="🎨 AI Image Generator":
    st.header("🎨 NOVA AI Image Generator")
    prompt=st.text_area("Describe the image")
    style=st.selectbox(
        "Style",
        ["Photorealistic","Anime","Digital art","3D render",
         "Watercolor","Fantasy","Cinematic","Logo"]
    )
    aspect=st.selectbox("Aspect ratio",["1:1","16:9","9:16","4:3","3:4"])

    if st.button("🎨 Generate Image",type="primary"):
        if not prompt.strip():
            st.warning("Describe your image first.")
        elif gc:
            try:
                with st.spinner("Creating image..."):
                    response=gc.models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=(
                            f"Generate an image. Style: {style}. "
                            f"Aspect ratio: {aspect}. Prompt: {prompt}"
                        )
                    )
                image_bytes=None
                for part in response.parts:
                    if getattr(part,"inline_data",None):
                        img=part.as_image()
                        buf=io.BytesIO()
                        img.save(buf,format="PNG")
                        image_bytes=buf.getvalue()
                        break

                if image_bytes:
                    st.session_state.generated_image_bytes=image_bytes
                else:
                    st.error("No image data returned.")
            except Exception as e:
                st.error(f"Image generation error: {e}")

    if st.session_state.generated_image_bytes:
        st.image(
            st.session_state.generated_image_bytes,
            caption="✨ Created by NOVA",
            use_container_width=True
        )
        st.download_button(
            "⬇️ Download image",
            data=st.session_state.generated_image_bytes,
            file_name="nova_image.png",
            mime="image/png"
        )

# ---------- FEEDBACK SUMMARY ----------
with st.sidebar.expander("Feedback activity"):
    st.write(f"{len(st.session_state.feedback_log)} feedback reactions")
    if st.session_state.feedback_log:
        st.json(st.session_state.feedback_log)

st.sidebar.caption("NOVA AI • created by nadeem haider 😊")
