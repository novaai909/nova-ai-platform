import streamlit as st, fitz, uuid, json, requests
from datetime import datetime
from google import genai
from supabase import create_client
import streamlit.components.v1 as components

st.set_page_config(page_title='NOVA AI', page_icon='✨', layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816;color:#f5f3ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#100b29,#080817,#10132b);border-right:1px solid #6d28d9}
.nova-card{background:linear-gradient(135deg,#241044,#101e55);border:1px solid #8b5cf6;border-radius:18px;padding:18px;margin:8px 0}
.nova-hero{text-align:center;padding:20px 0}.nova-infinity{font-size:clamp(110px,30vw,200px);line-height:.9;background:linear-gradient(90deg,#ff36d1,#8b5cf6,#22d3ee,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 18px #a855f7)}
.nova-brand{font-family:cursive;font-size:clamp(50px,12vw,85px);font-weight:900;background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.nova-tag{color:white;font-family:cursive;font-size:clamp(25px,7vw,40px)}
.butterfly-stage{height:220px;position:relative;overflow:hidden}.butterfly{position:absolute;font-size:65px;animation:fly 5s ease-in-out infinite;filter:drop-shadow(0 0 18px #d946ef)}@keyframes fly{0%{left:-5%;top:65%;transform:rotate(-15deg)}25%{left:30%;top:10%;transform:rotate(15deg)}50%{left:65%;top:60%;transform:rotate(-10deg)}75%{left:85%;top:15%;transform:rotate(20deg)}100%{left:105%;top:55%;transform:rotate(-15deg)}}
.entry-panel{text-align:center;padding:25px;border:1px solid #a855f7;border-radius:25px;background:linear-gradient(135deg,#180c32,#071a45);box-shadow:0 0 30px #7c3aed55}
</style>''', unsafe_allow_html=True)

try: gc=genai.Client(api_key=st.secrets['GEMINI_API_KEY'])
except Exception: st.error('Gemini setup error: check GEMINI_API_KEY'); st.stop()
try: db=create_client(st.secrets['SUPABASE_URL'],st.secrets['SUPABASE_KEY'])
except Exception: st.error('Supabase setup error: check SUPABASE_URL and SUPABASE_KEY'); st.stop()

STORE='nova_main'; PM='__nova_projects__'; CM='__nova_chat_projects__'
def load_data():
    try:
        r=db.table('nova_storage').select('*').eq('id',STORE).execute()
        if r.data: return r.data[0].get('chats') or {},r.data[0].get('notes') or []
    except Exception as e: st.error('Load error: '+str(e))
    return {},[]
def save_data():
    payload=dict(st.session_state.chats); payload[PM]=st.session_state.projects; payload[CM]=st.session_state.chat_projects
    try: db.table('nova_storage').upsert({'id':STORE,'chats':payload,'notes':st.session_state.notes}).execute(); return True
    except Exception as e: st.error('Save error: '+str(e)); return False
if not st.session_state.get('init'):
    chats,notes=load_data(); projects=chats.pop(PM,[{'id':'default','name':'General'}]); mapping=chats.pop(CM,{})
    if not isinstance(projects,list) or not projects: projects=[{'id':'default','name':'General'}]
    if not isinstance(mapping,dict): mapping={}
    if not chats: chats={'Chat 1':[]}
    for t in chats: mapping.setdefault(t,'default')
    st.session_state.update(chats=chats,notes=notes if isinstance(notes,list) else [],projects=projects,chat_projects=mapping,active_chat=next(iter(chats)),active_project=mapping.get(next(iter(chats)),'default'),init=True)
def chats_in(pid): return [t for t in st.session_state.chats if st.session_state.chat_projects.get(t,'default')==pid]
def newchat(pid):
    name='New Chat'; n=2
    while name in st.session_state.chats: name=f'New Chat {n}'; n+=1
    st.session_state.chats[name]=[]; st.session_state.chat_projects[name]=pid; st.session_state.active_chat=name; st.session_state.active_project=pid; save_data()
def ai(prompt,history=None):
    context='\n'.join(m.get('role','')+': '+m.get('content','') for m in (history or [])[-10:])
    q='You are NOVA AI, a helpful multilingual assistant. Answer naturally.\n'+context+'\nUser: '+prompt
    for model in ['gemini-2.5-flash','gemini-2.0-flash','gemini-2.5-flash-lite']:
        try:
            out=gc.models.generate_content(model=model,contents=q); txt=getattr(out,'text','')
            if txt and txt.strip(): return txt,'Gemini • '+model
        except Exception: pass
    gkey=st.secrets.get('GROQ_API_KEY')
    if gkey:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=gkey,base_url='https://api.groq.com/openai/v1')
            out=client.chat.completions.create(model='openai/gpt-oss-20b',messages=[{'role':'user','content':q}],max_tokens=2048)
            txt=out.choices[0].message.content
            if txt: return txt,'Groq backup • openai/gpt-oss-20b'
        except Exception as e: return 'Gemini unavailable and Groq backup failed: '+str(e)[:200],'Providers unavailable'
    return 'AI service unavailable. Check your Gemini API key or add GROQ_API_KEY for backup.','AI unavailable'
def web_search(query,n=5):
    key=st.secrets.get('TAVILY_API_KEY')
    if not key: return None,'TAVILY_API_KEY missing in Streamlit Secrets.'
    try:
        r=requests.post('https://api.tavily.com/search',json={'api_key':key,'query':query,'search_depth':'advanced','max_results':n,'include_answer':True},timeout=25); r.raise_for_status(); return r.json(),None
    except Exception as e: return None,'Search error: '+str(e)

with st.sidebar:
    st.title('✨ NOVA AI')
    if st.button('➕ New Chat',use_container_width=True): newchat(st.session_state.active_project); st.rerun()
    chat_search=st.text_input('🔎 Search chats'); nav=st.radio('Navigation',['📚 Library','🎨 Customize','📁 Projects','🖥️ Remote','🔲 Explore'],label_visibility='collapsed')
    st.markdown('### 🌈 Projects')
    for p in st.session_state.projects:
        pid=p.get('id','default')
        if st.button('📁 '+p.get('name','Project'),key='p_'+pid):
            st.session_state.active_project=pid; items=chats_in(pid)
            if items: st.session_state.active_chat=items[0]
            else: newchat(pid)
            st.rerun()
        for t in chats_in(pid):
            if chat_search and chat_search.lower() not in t.lower(): continue
            if st.button('↳ 💬 '+t,key='c_'+t): st.session_state.active_chat=t; st.session_state.active_project=pid; st.rerun()
    with st.expander('➕ New Project'):
        pname=st.text_input('Project name')
        if st.button('Create project') and pname.strip():
            new_id=str(uuid.uuid4())[:8]; st.session_state.projects.append({'id':new_id,'name':pname.strip()}); newchat(new_id); st.rerun()
    with st.expander('⚙️ Manage Projects'):
        chosen=st.selectbox('Select project',st.session_state.projects,format_func=lambda p:p['name']); rename=st.text_input('Rename to')
        if st.button('Rename project') and rename.strip(): chosen['name']=rename.strip(); save_data(); st.rerun()
        if chosen['id']!='default' and st.button('Delete project'):
            pid=chosen['id']
            for t in chats_in(pid): st.session_state.chats.pop(t,None); st.session_state.chat_projects.pop(t,None)
            st.session_state.projects=[p for p in st.session_state.projects if p['id']!=pid]; st.session_state.active_project='default'; save_data(); st.rerun()

if not st.session_state.get('entered_nova',False):
    st.markdown('<div class="entry-panel"><div class="butterfly-stage"><div class="butterfly">🦋</div></div><div class="nova-infinity">∞</div><div class="nova-brand">NOVA AI</div><div class="nova-tag">✨ Welcome to your AI universe ✨</div><p>Chat • Search • Learn • Create</p></div>',unsafe_allow_html=True)
    if st.button('🚀 Enter NOVA AI',use_container_width=True): st.session_state.entered_nova=True; st.rerun()
    st.stop()
st.markdown('<div class="nova-hero"><div class="butterfly-stage"><div class="butterfly">🦋</div></div><div class="nova-infinity">∞</div><div class="nova-brand">NOVA AI</div><div class="nova-tag">Welcome to NOVA AI</div></div><div class="nova-card"><h2>🌈 Welcome to NOVA</h2><p>Chat, search the web, translate, study, work with PDFs, write and save notes.</p></div>',unsafe_allow_html=True)
feature=st.selectbox('Open feature',['💬 AI Chat','📄 PDF Assistant','✍️ Writing Studio','🧠 My Notes','🧮 Calculator','🌻 NOVA Voice','🌐 AI Web Search','🌍 Translator','🎓 AI Study Mode'],key='feature_selector')

if feature=='💬 AI Chat':
    active=st.session_state.active_chat; history=st.session_state.chats.setdefault(active,[]); st.caption('Project: '+next((p['name'] for p in st.session_state.projects if p['id']==st.session_state.active_project),'General'))
    for m in history:
        with st.chat_message(m.get('role','assistant')): st.markdown(m.get('content','')); st.caption(m.get('provider',''))
    prompt=st.chat_input('Ask NOVA AI anything…')
    if prompt:
        history.append({'role':'user','content':prompt}); save_data()
        with st.chat_message('user'): st.markdown(prompt)
        with st.chat_message('assistant'):
            with st.spinner('Thinking…'): answer,provider=ai(prompt,history[:-1])
            st.markdown(answer); st.caption(provider)
        history.append({'role':'assistant','content':answer,'provider':provider}); save_data(); st.rerun()
    with st.expander('Manage this chat'):
        if st.button('Delete chat'):
            st.session_state.chats.pop(active,None); st.session_state.chat_projects.pop(active,None); remaining=chats_in(st.session_state.active_project)
            if remaining: st.session_state.active_chat=remaining[0]
            else: newchat(st.session_state.active_project)
            save_data(); st.rerun()
        newname=st.text_input('Rename chat')
        if st.button('Save chat name') and newname.strip() and newname not in st.session_state.chats:
            st.session_state.chats[newname]=st.session_state.chats.pop(active); st.session_state.chat_projects[newname]=st.session_state.chat_projects.pop(active,st.session_state.active_project); st.session_state.active_chat=newname; save_data(); st.rerun()

elif feature=='📄 PDF Assistant':
    pdf=st.file_uploader('Upload PDF',type=['pdf'])
    if pdf:
        try:
            doc=fitz.open(stream=pdf.getvalue(),filetype='pdf'); text='\n'.join(p.get_text() for p in doc); task=st.radio('PDF task',['Ask Question','Summary','Quiz'])
            if not text.strip(): st.warning('No selectable text detected (scanned PDF).')
            elif task=='Ask Question':
                q=st.text_input('Question about PDF')
                if st.button('Ask PDF') and q.strip(): st.markdown(ai('Answer only from this PDF: '+text[:80000]+'\nQuestion: '+q)[0])
            elif task=='Summary':
                if st.button('Summarize PDF'): st.markdown(ai('Summarize this PDF: '+text[:80000])[0])
            else:
                count=st.slider('Questions',3,15,5)
                if st.button('Create PDF quiz'): st.markdown(ai(f'Create {count} MCQs with answer key from this PDF: '+text[:80000])[0])
        except Exception as e: st.error('PDF error: '+str(e))

elif feature=='✍️ Writing Studio':
    kind=st.selectbox('Writing type',['Email','Application','Resume','Essay','Story','Social caption','Letter','Improve text','Code help','Custom']); instructions=st.text_area('Instructions')
    if st.button('Generate writing'):
        if instructions.strip():
            answer,provider=ai('Write '+kind+'. '+instructions); st.markdown(answer); st.caption(provider); st.download_button('Download draft',answer,file_name='nova_draft.txt')
        else: st.warning('Enter instructions first.')

elif feature=='🧠 My Notes':
    with st.form('notes_form'):
        note_title=st.text_input('Note title'); note_body=st.text_area('Note content'); submitted=st.form_submit_button('Save note')
    if submitted:
        if note_title.strip() and note_body.strip(): st.session_state.notes.append({'title':note_title,'content':note_body,'date':datetime.now().strftime('%d-%m-%Y %H:%M')}); save_data(); st.rerun()
        else: st.warning('Fill in both fields.')
    for i,note in enumerate(st.session_state.notes):
        with st.expander('📌 '+note.get('title','Untitled')):
            st.write(note.get('content','')); st.caption(note.get('date','')); st.download_button('Download note',note.get('content',''),file_name=f'note_{i+1}.txt',key='note_download_'+str(i))
            if st.button('Delete note',key='note_delete_'+str(i)): st.session_state.notes.pop(i); save_data(); st.rerun()

elif feature=='🧮 Calculator':
    a=st.number_input('First number',value=0.0); op=st.selectbox('Operation',['+','-','×','÷','%']); b=st.number_input('Second number',value=1.0)
    if st.button('Calculate'):
        if op=='÷' and b==0: st.error('Cannot divide by zero')
        else: st.success('Result: '+str(a+b if op=='+' else a-b if op=='-' else a*b if op=='×' else a/b if op=='÷' else a*b/100))

elif feature=='🌐 AI Web Search':
    st.markdown('## 🌐 NOVA Web Search'); query=st.text_input('Search the web',placeholder='Latest information, news, research…'); n=st.slider('Search results',3,10,5)
    if st.button('🔍 Search web') and query.strip():
        with st.spinner('Searching…'): data,error=web_search(query.strip(),n)
        if error: st.error(error)
        else: st.session_state.web_results=data; st.session_state.web_query=query.strip()
    if st.session_state.get('web_results'):
        data=st.session_state.web_results; st.markdown('### Results: '+st.session_state.get('web_query',''))
        if data.get('answer'): st.info(data['answer'])
        for i,r in enumerate(data.get('results',[]),1):
            with st.container(border=True): st.markdown(f"**{i}. [{r.get('title','Result')}]({r.get('url','#')})**"); st.write(r.get('content','')); st.caption(r.get('url',''))
        results=data.get('results',[])
        if results:
            search_context='\n\n'.join('Title: '+r.get('title','')+'\nURL: '+r.get('url','')+'\nContent: '+r.get('content','') for r in results); follow=st.text_area('Ask NOVA about results (optional)')
            if st.button('🤖 Analyze search results'):
                with st.spinner('Analyzing…'): ans,prov=ai('Answer using these search results and cite URLs.\n'+search_context+'\nUser request: '+(follow.strip() or 'Summarize the results.'))
                st.markdown(ans); st.caption(prov)

elif feature=='🌍 Translator':
    st.markdown('## 🌍 NOVA Translator'); langs=['Hindi','English','Urdu','Punjabi','Bengali','Gujarati','Marathi','Tamil','Telugu','Kannada','Malayalam','French','Spanish','German','Arabic','Japanese','Chinese (Simplified)','Russian','Portuguese','Korean','Italian','Nepali']
    c1,c2=st.columns(2)
    with c1: source=st.selectbox('Translate from',['Auto-detect']+langs)
    with c2: target=st.selectbox('Translate to',langs,index=1)
    original=st.text_area('Text to translate',height=180)
    if st.button('🌐 Translate'):
        if not original.strip(): st.warning('Enter text first.')
        elif source==target: st.warning('Choose different languages.')
        else:
            with st.spinner('Translating…'): translation,provider=ai(f'Translate into {target} from {source}. Preserve tone, meaning and formatting. Output only translation.\n\n{original}')
            st.session_state.translation=translation; st.session_state.translation_provider=provider
    if st.session_state.get('translation'):
        st.markdown('### Translation'); st.text_area('Translated output',value=st.session_state.translation,height=180,key='translation_view'); st.caption(st.session_state.get('translation_provider','')); st.download_button('⬇️ Download translation',st.session_state.translation,file_name='nova_translation.txt')

elif feature=='🎓 AI Study Mode':
    st.markdown('## 🎓 NOVA Study Mode'); st.write('Explanation, revision notes, quizzes, flashcards and step-by-step learning.')
    material=st.text_area('Topic or study material',height=180,placeholder='Paste notes or enter a topic…'); level=st.selectbox('Learning level',['Beginner','School student','High school','College','Advanced']); task=st.selectbox('Study activity',['Explain topic','Revision notes','MCQ quiz','Flashcards','Step-by-step solution','Practice questions']); qty=st.slider('Question/card count',3,20,5) if task in ['MCQ quiz','Practice questions','Flashcards'] else 5
    if st.button('📖 Start study session'):
        if not material.strip(): st.warning('Enter a topic or paste material.')
        else:
            instructions={'Explain topic':f'Explain simply to a {level} student with examples and recap.','Revision notes':f'Create structured concise revision notes for {level}, headings, bullet points and recap.','MCQ quiz':f'Create {qty} MCQs with four choices, answer key and short explanations.','Flashcards':f'Create {qty} flashcards with front/back.','Step-by-step solution':f'Explain or solve step by step for {level}, checking the answer.','Practice questions':f'Create {qty} practice questions and answer key for {level}.'}
            with st.spinner('Preparing your study content…'): study,prov=ai(instructions[task]+'\nMaterial/topic:\n'+material)
            st.session_state.study_content=study; st.session_state.study_provider=prov
    if st.session_state.get('study_content'):
        st.markdown('### 📚 Study material'); st.markdown(st.session_state.study_content); st.caption(st.session_state.get('study_provider','')); st.download_button('⬇️ Download study material',st.session_state.study_content,file_name='nova_study_material.txt')

elif feature=='🌻 NOVA Voice':
    st.markdown('## 🌻 NOVA Voice'); st.info('Browser speech recognition and speech synthesis support varies. Microphone permission is required. This voice demo uses your Gemini API key in the browser.')
    key=st.secrets['GEMINI_API_KEY']
    voice_html='''<!doctype html><html><body style="background:#080817;color:white;font-family:Arial;text-align:center;padding:15px"><div style="font-size:90px">🌻🦋</div><h2>NOVA VOICE</h2><select id="lang"><option value="hi-IN">Hindi</option><option value="en-GB">British English</option><option value="en-US">English US</option></select><br><button id="start">🎙 Start</button><button id="stop">⏹ Stop</button><p id="status">Press Start and speak</p><div id="log" style="text-align:left;white-space:pre-wrap"></div><script>
const KEY=KEYHERE,SR=window.SpeechRecognition||window.webkitSpeechRecognition;let active=false,rec=null,lang='hi-IN';const status=document.getElementById('status'),log=document.getElementById('log');function speak(t){return new Promise(resolve=>{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t);u.lang=lang;u.onend=resolve;u.onerror=resolve;speechSynthesis.speak(u)})}async function ask(t){status.textContent='Thinking…';try{let r=await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key='+KEY,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'You are NOVA, a helpful conversational voice assistant. Answer briefly in the same language. '+t}]}]})});if(!r.ok)throw Error('API error');let j=await r.json(),a=j.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('')||'No response';log.textContent+='You: '+t+'\nNOVA: '+a+'\n\n';status.textContent='Speaking…';await speak(a)}catch(e){status.textContent='AI error: '+e.message}finally{if(active)listen()}}function listen(){if(!active||!SR)return;if(rec)return;rec=new SR();rec.lang=lang;rec.onresult=e=>{let t=e.results[0][0].transcript;if(t)ask(t)};rec.onerror=e=>{rec=null;status.textContent='Speech error: '+e.error};rec.onend=()=>{rec=null;if(active)setTimeout(listen,500)};try{rec.start();status.textContent='Listening…'}catch(e){rec=null}}document.getElementById('start').onclick=()=>{lang=document.getElementById('lang').value;if(!SR){status.textContent='Speech recognition unsupported. Try Chrome.';return}active=true;liste()};document.getElementById('stop').onclick=()=>{active=false;if(rec){rec.abort();rec=null}speechSynthesis.cancel();status.textContent='Stopped'};
</script></body></html>'''.replace('KEYHERE',json.dumps(key))
    components.html(voice_html,height=500,scrolling=False)

if nav=='📚 Library': st.sidebar.info('Chat history and Notes are stored in your library.')
elif nav=='🎨 Customize': st.sidebar.info('Neon theme active.')
elif nav=='📁 Projects': st.sidebar.info('Manage projects in the sidebar.')
elif nav=='🖥️ Remote': st.sidebar.info('Remote feature placeholder.')
elif nav=='🔲 Explore': st.sidebar.info('More features can be added.')
st.divider(); st.markdown('<center>✨ <b>NOVA AI</b> • Gemini • Web Search • Translator • Study Mode</center>',unsafe_allow_html=True)
