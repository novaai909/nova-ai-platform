import streamlit as st, fitz, uuid
from datetime import datetime
from google import genai
from supabase import create_client
import streamlit.components.v1 as components
import json

st.set_page_config(page_title='NOVA AI',page_icon='✨',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 10% 5%,#23104a 0%,transparent 28%),radial-gradient(circle at 90% 20%,#071c4c 0%,transparent 30%),#080816;color:#f5f3ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#100b29,#080817,#10132b);border-right:1px solid #6d28d9}
.nova-card{background:linear-gradient(135deg,#241044,#101e55);border:1px solid #8b5cf6;border-radius:18px;padding:18px;margin:8px 0}
.nova-hero{text-align:center;padding:10px 0 22px}.nova-infinity{font-size:clamp(85px,22vw,150px);background:linear-gradient(90deg,#ff36d1,#8b5cf6,#22d3ee,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 18px #a855f7);animation:glow 3s infinite}
.nova-brand{font-family:cursive;font-size:clamp(42px,10vw,72px);font-weight:900;background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.nova-tag{color:white;font-size:clamp(22px,6vw,32px)}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 12px #a855f7)}50%{filter:drop-shadow(0 0 30px #22d3ee)}}

/* NOVA restored entry + hero layout */
.nova-hero{display:flex;flex-direction:column;align-items:center;text-align:center;padding:26px 0 28px;gap:6px}
.nova-infinity{display:block;font-size:clamp(120px,32vw,210px);line-height:.92;margin:0 0 10px;letter-spacing:-8px}
.nova-brand{display:block;font-family:'Brush Script MT',cursive;font-size:clamp(54px,13vw,88px);font-weight:900;line-height:1.08;margin:0}
.nova-tag{display:block;font-family:'Brush Script MT',cursive;font-size:clamp(25px,7vw,40px);line-height:1.2;margin-top:8px}
.nova-splash{position:fixed;inset:0;z-index:999999;background:radial-gradient(circle at 50% 45%,#27105c 0%,#10102b 48%,#050611 100%);display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden;animation:splashout 1.25s ease 7.1s forwards;pointer-events:none}
.splash-logo{font-size:clamp(130px,38vw,230px);line-height:1;opacity:0;display:block;background:linear-gradient(90deg,#ff00cc,#7c3aed,#00e5ff,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 24px #a855f7);animation:logo-grow-spin 2.3s ease-out forwards,logo-glow 2.4s ease-in-out infinite,gradient-shift 5s linear infinite}
.splash-name{font-family:'Brush Script MT',cursive;font-size:clamp(62px,16vw,100px);font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,#ff00cc,#00e5ff,#a855f7,#00ff88,#ff00cc);background-size:400%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;opacity:0;animation:appear 1.6s ease 1.8s forwards,shine 4s linear infinite,brand-glow 2.5s ease-in-out infinite}
.splash-welcome{color:white;font-family:'Brush Script MT',cursive;font-size:clamp(30px,8vw,44px);letter-spacing:1px;text-align:center;opacity:0;text-shadow:0 0 12px white;animation:appear 1.5s ease 3s forwards}
.bfly{position:absolute;font-size:clamp(32px,8vw,48px);will-change:transform;animation:flypath 5.5s ease-in-out infinite;filter:drop-shadow(0 0 7px currentColor)}
.bfly:nth-child(odd){animation-name:flypath2}.bfly:nth-child(3n){animation-name:flypath3}.bfly:nth-child(4n){animation-name:flypath4}.bfly:nth-child(5n){animation-name:flypath5}
@keyframes logo-grow-spin{0%{opacity:0;transform:scale(.12) rotate(0)}65%{opacity:1;transform:scale(1.25) rotate(300deg)}100%{opacity:1;transform:scale(1) rotate(360deg)}}
@keyframes logo-glow{0%,100%{filter:drop-shadow(0 0 12px #a855f7)}50%{filter:drop-shadow(0 0 36px #22d3ee)}}
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
</style>''',unsafe_allow_html=True)
try: gc=genai.Client(api_key=st.secrets['GEMINI_API_KEY'])
except Exception: st.error('Gemini setup error: check GEMINI_API_KEY');st.stop()
try: db=create_client(st.secrets['SUPABASE_URL'],st.secrets['SUPABASE_KEY'])
except Exception: st.error('Supabase setup error: check SUPABASE_URL and SUPABASE_KEY');st.stop()
STORE='nova_main'; PM='__nova_projects__'; CM='__nova_chat_projects__'
def load():
 try:
  r=db.table('nova_storage').select('*').eq('id',STORE).execute()
  if r.data:return r.data[0].get('chats') or {},r.data[0].get('notes') or []
 except Exception as e:st.error('Load error: '+str(e))
 return {},[]
def save():
 d=dict(st.session_state.chats);d[PM]=st.session_state.projects;d[CM]=st.session_state.chat_projects
 try:db.table('nova_storage').upsert({'id':STORE,'chats':d,'notes':st.session_state.notes}).execute();return True
 except Exception as e:st.error('Save error: '+str(e));return False
if not st.session_state.get('init'):
 chats,notes=load();projects=chats.pop(PM,[{'id':'default','name':'General'}]);mapping=chats.pop(CM,{})
 if not isinstance(projects,list) or not projects:projects=[{'id':'default','name':'General'}]
 if not isinstance(mapping,dict):mapping={}
 if not chats:chats={'Chat 1':[]}
 for t in chats:mapping.setdefault(t,'default')
 st.session_state.chats=chats;st.session_state.notes=notes if isinstance(notes,list) else [];st.session_state.projects=projects;st.session_state.chat_projects=mapping;st.session_state.active_chat=next(iter(chats));st.session_state.active_project=mapping.get(st.session_state.active_chat,'default');st.session_state.init=True
def chats_in(pid):return [t for t in st.session_state.chats if st.session_state.chat_projects.get(t,'default')==pid]
def newchat(pid):
 name='New Chat';i=2
 while name in st.session_state.chats:name=f'New Chat {i}';i+=1
 st.session_state.chats[name]=[];st.session_state.chat_projects[name]=pid;st.session_state.active_chat=name;st.session_state.active_project=pid;save()
def ai(prompt,history=None):
 context='\n'.join(m.get('role','')+': '+m.get('content','') for m in (history or [])[-10:])
 q='You are NOVA AI, a helpful multilingual assistant. Answer the user naturally.\n'+context+'\nUser: '+prompt
 gemini_errors=[]
 for model in ['gemini-2.5-flash','gemini-2.0-flash','gemini-2.5-flash-lite']:
  try:
   x=gc.models.generate_content(model=model,contents=q);txt=getattr(x,'text','')
   if txt and txt.strip():return txt,'Gemini • '+model
  except Exception as e:gemini_errors.append(str(e)[:180])
 # Backup provider: Groq, if a key has been added in Streamlit Secrets.
 groq_key=st.secrets.get('GROQ_API_KEY')
 if groq_key:
  try:
   from openai import OpenAI
   groq_client=OpenAI(api_key=groq_key,base_url='https://api.groq.com/openai/v1')
   gr=groq_client.chat.completions.create(model='openai/gpt-oss-20b',messages=[{'role':'user','content':q}],max_tokens=2048)
   txt=gr.choices[0].message.content
   if txt and txt.strip():return txt,'Groq backup • openai/gpt-oss-20b'
  except Exception as e:
   groq_error=str(e)[:220]
   return 'Gemini is unavailable and Groq backup also failed: '+groq_error,'Providers unavailable'
 return 'Gemini quota/service unavailable. Add GROQ_API_KEY in Streamlit Secrets to enable the automatic backup AI.','Gemini unavailable • no Groq key'
with st.sidebar:
 st.title('✨ NOVA AI')
 if st.button('➕ New Chat',use_container_width=True):newchat(st.session_state.active_project);st.rerun()
 search=st.text_input('🔎 Search chats');nav=st.radio('Navigation',['📚 Library','🎨 Customize','📁 Projects','🖥️ Remote','🔲 Explore'],label_visibility='collapsed')
 st.markdown('### 🌈 Projects')
 for p in st.session_state.projects:
  pid=p.get('id','default')
  if st.button('📁 '+p.get('name','Project'),key='p_'+pid):
   st.session_state.active_project=pid;items=chats_in(pid)
   if items:st.session_state.active_chat=items[0]
   else:newchat(pid)
   st.rerun()
  for t in chats_in(pid):
   if search and search.lower() not in t.lower():continue
   if st.button('↳ 💬 '+t,key='c_'+t):st.session_state.active_chat=t;st.session_state.active_project=pid;st.rerun()
 with st.expander('➕ New Project'):
  pname=st.text_input('Project name')
  if st.button('Create project') and pname.strip():
   id=str(uuid.uuid4())[:8];st.session_state.projects.append({'id':id,'name':pname.strip()});newchat(id);st.rerun()
 with st.expander('⚙️ Manage Projects'):
  chosen=st.selectbox('Select',st.session_state.projects,format_func=lambda p:p['name']);rename=st.text_input('Rename to')
  if st.button('Rename') and rename.strip():chosen['name']=rename.strip();save();st.rerun()
  if chosen['id']!='default' and st.button('Delete project'):
   pid=chosen['id']
   for t in chats_in(pid):st.session_state.chats.pop(t,None);st.session_state.chat_projects.pop(t,None)
   st.session_state.projects=[p for p in st.session_state.projects if p['id']!=pid];st.session_state.active_project='default';save();st.rerun()
# One-time animated entry screen restored (per Streamlit session)
if not st.session_state.get('splash_seen', False):
 butterflies=[]
 for i in range(28):
  left=(i*37+11)%94; top=(i*53+7)%88; hue=(i*47)%360
  delay=(i*0.23)%3.8; duration=4.4+(i%6)*0.55
  butterflies.append(f'<div class="bfly" style="left:{left}%;top:{top}%;color:hsl({hue},95%,70%);animation-delay:{delay}s;animation-duration:{duration}s">🦋</div>')
 st.markdown('<div class="nova-splash">'+''.join(butterflies)+'<div class="splash-logo">∞</div><div class="splash-name">NOVA AI</div><div class="splash-welcome">Welcome to NOVA AI</div></div>',unsafe_allow_html=True)
 st.session_state.splash_seen=True
st.markdown('<div class="nova-hero"><div class="nova-infinity">∞</div><div class="nova-brand">NOVA AI</div><div class="nova-tag">Welcome to NOVA AI</div></div><div class="nova-card"><h2>🌈 Welcome to NOVA</h2><p>Chat, work with PDFs, write, and keep notes.</p></div>',unsafe_allow_html=True)
feature=st.selectbox('Open feature',['💬 AI Chat','📄 PDF Assistant','✍️ Writing Studio','🧠 My Notes','🧮 Calculator','🌻 NOVA Voice'])
if feature=='🌻 NOVA Voice':
 st.markdown('## 🌻 NOVA Voice')
 st.info('Continuous turn-by-turn voice: tap Start once, speak naturally, NOVA replies aloud, then automatically listens again. Gemini speech first; browser speech synthesis fallback. Browser speech recognition requires browser support and microphone permission. Keep this app private because the key is used inside this voice panel.')
 key=st.secrets['GEMINI_API_KEY']
 html=r'''<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>
body{margin:0;background:#080817;color:white;font-family:Arial}.box{background:radial-gradient(circle,#26105b,#080817);border:1px solid #9060ed;border-radius:24px;padding:15px;text-align:center}.sun{font-size:112px;animation:bloom 3.2s ease-in-out infinite;filter:drop-shadow(0 0 22px #ffb52e);transform-origin:center}@keyframes bloom{0%,100%{transform:scale(.78) rotate(-3deg);filter:drop-shadow(0 0 10px orange)}50%{transform:scale(1.12) rotate(3deg);filter:drop-shadow(0 0 28px #ffd54a)}}.orbit{position:absolute;left:50%;top:50%;width:205px;height:125px;margin-left:-102px;margin-top:-62px;pointer-events:none}.butter{position:absolute;font-size:31px;animation:orbitfly 6.5s ease-in-out infinite;filter:drop-shadow(0 0 8px #ffb347)}@keyframes orbitfly{0%{left:0%;top:42%;transform:rotate(-20deg)}25%{left:42%;top:0%;transform:rotate(20deg)}50%{left:84%;top:48%;transform:rotate(-10deg)}75%{left:43%;top:95%;transform:rotate(25deg)}100%{left:0%;top:42%;transform:rotate(-20deg)}}button,select{background:#251144;color:white;border:1px solid #9b72ed;border-radius:12px;padding:12px;margin:5px;font-size:16px}#status{padding:12px;color:#d7baff}#log{text-align:left;white-space:pre-wrap;max-height:230px;overflow:auto;background:#100b29;border-radius:12px;padding:10px}</style></head><body><div class="box"><div style="height:190px;position:relative;display:flex;align-items:center;justify-content:center"><div class="sun">🌻</div><div class="orbit"><span class="butter">🦋</span><span class="butter" style="animation-delay:2.1s">🦋</span><span class="butter" style="animation-delay:4.2s">🦋</span></div></div><h1 style="color:#e4a6ff">NOVA VOICE</h1><p>Hindi • British English • Multilingual</p><select id="lang"><option value="hi-IN">Hindi</option><option value="en-GB">British English</option><option value="en-US">English (US)</option></select><br><button id="on">🎙 Start voice session</button><button id="off">⏹ End session</button><div id="status">Tap start, then talk naturally.</div><div id="log"></div></div>
<script>
const KEY=KEYHERE;const SR=window.SpeechRecognition||window.webkitSpeechRecognition;let running=false,listening=false,busy=false,recognizer=null,lang='hi-IN',playback=null;const status=document.getElementById('status'),log=document.getElementById('log');
function stopAudio(){try{speechSynthesis.cancel()}catch(e){}if(playback){try{playback.pause();playback.src=''}catch(e){}playback=null}}
function browserSpeak(text){return new Promise(resolve=>{try{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(text);u.lang=lang;u.onend=resolve;u.onerror=resolve;speechSynthesis.speak(u)}catch(e){resolve()}})}
async function geminiSpeak(text){let r=await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key='+KEY,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'Speak naturally in '+lang+'. Reply text: '+text}]}],generationConfig:{responseModalities:['AUDIO'],speechConfig:{voiceConfig:{prebuiltVoiceConfig:{voiceName:'Kore'}}}}})});if(!r.ok)throw Error('Gemini TTS status '+r.status);let j=await r.json(),b=j.candidates?.[0]?.content?.parts?.find(p=>p.inlineData)?.inlineData?.data;if(!b)throw Error('No audio data');let bytes=Uint8Array.from(atob(b),c=>c.charCodeAt(0)),wav=new ArrayBuffer(44+bytes.length),v=new DataView(wav);function put(o,t){for(let i=0;i<t.length;i++)v.setUint8(o+i,t.charCodeAt(i))}put(0,'RIFF');v.setUint32(4,36+bytes.length,true);put(8,'WAVE');put(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);put(36,'data');v.setUint32(40,bytes.length,true);new Uint8Array(wav,44).set(bytes);playback=new Audio(URL.createObjectURL(new Blob([wav],{type:'audio/wav'})));await playback.play();await new Promise(resolve=>{playback.onended=resolve;playback.onerror=resolve});playback=null}
async function speak(text){status.textContent='NOVA is speaking…';try{await geminiSpeak(text)}catch(e){status.textContent='Gemini speech unavailable/quota: switching to browser voice';await browserSpeak(text)}if(running)status.textContent='Listening for your next message…'}
async function ask(text){if(!running)return;busy=true;try{status.textContent='NOVA is thinking…';let answer='';for(let m of ['gemini-2.5-flash','gemini-2.0-flash','gemini-2.5-flash-lite']){try{let r=await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+m+':generateContent?key='+KEY,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{parts:[{text:'You are NOVA, a friendly multilingual voice assistant. Answer briefly and conversationally in the same language as the user. '+text}]}]})});if(r.ok){let j=await r.json();answer=j.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('');if(answer)break}}catch(e){}}if(!answer){status.textContent='Gemini AI quota/service unavailable. Browser speech can speak text but cannot create an AI reply on its own.';return}log.textContent+='You: '+text+'\nNOVA: '+answer+'\n\n';await speak(answer)}finally{busy=false;if(running)queueListen()}}
function queueListen(){if(running&&!busy&&!recognizer)setTimeout(startListening,700)}
function startListening(){if(!running||busy||recognizer)return;if(!SR){status.textContent='Speech recognition is unsupported here. Try Chrome on Android.';running=false;return}recognizer=new SR();recognizer.lang=lang;recognizer.continuous=false;recognizer.interimResults=false;recognizer.maxAlternatives=1;recognizer.onresult=e=>{let heard=e.results?.[0]?.[0]?.transcript?.trim();if(heard&&running){status.textContent='Heard: '+heard;ask(heard)}};recognizer.onerror=e=>{recognizer=null;if(e.error==='not-allowed'||e.error==='service-not-allowed'){running=false;status.textContent='Microphone permission denied. Allow microphone access and try again.'}else if(running){status.textContent='Listening reconnect…';queueListen()}};recognizer.onend=()=>{recognizer=null;queueListen()};try{recognizer.start();status.textContent='Listening… speak now'}catch(e){recognizer=null;queueListen()}}
document.getElementById('on').onclick=()=>{if(running)return;lang=document.getElementById('lang').value;running=true;status.textContent='Voice session started';startListening()};document.getElementById('off').onclick=()=>{running=false;busy=false;if(recognizer){try{recognizer.abort()}catch(e){}recognizer=null}stopAudio();status.textContent='Session ended'};document.getElementById('lang').onchange=e=>{lang=e.target.value;if(running&&!busy){if(recognizer){try{recognizer.abort()}catch(x){}recognizer=null}startListening()}};
</script></body></html>'''.replace('KEYHERE',repr(key))
 components.html(html,height=590,scrolling=False)
elif feature=='💬 AI Chat':
 active=st.session_state.active_chat;history=st.session_state.chats.setdefault(active,[]);st.caption('Project: '+next((p['name'] for p in st.session_state.projects if p['id']==st.session_state.active_project),'General'))
 for idx,m in enumerate(history):
  with st.chat_message(m.get('role','assistant')):
   st.markdown(m.get('content',''));st.caption(m.get('provider',''))
   if m.get('role')=='assistant' and m.get('content','').strip():
    speech_text=json.dumps(m.get('content',''))
    speak_html='''<button id="speakBtn" style="background:#251144;color:white;border:1px solid #9b72ed;border-radius:12px;padding:9px 14px;font-size:15px;cursor:pointer">🔊 Listen to NOVA's answer</button><button id="stopBtn" style="background:#20172b;color:white;border:1px solid #9b72ed;border-radius:12px;padding:9px 14px;font-size:15px;cursor:pointer">⏹ Stop audio</button><script>const txt=TEXT;function langFor(t){return /[\u0900-\u097F]/.test(t)?'hi-IN':'en-GB'}document.getElementById('speakBtn').onclick=()=>{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(txt);u.lang=langFor(txt);u.rate=1;u.pitch=1;speechSynthesis.speak(u)};document.getElementById('stopBtn').onclick=()=>speechSynthesis.cancel();</script>'''.replace('TEXT',speech_text)
    components.html(speak_html,height=55)
 prompt=st.chat_input('Ask NOVA AI anything…')
 if prompt:
  history.append({'role':'user','content':prompt});save()
  with st.chat_message('user'):st.markdown(prompt)
  with st.chat_message('assistant'):
   with st.spinner('Thinking…'):answer,provider=ai(prompt,history[:-1])
   st.markdown(answer);st.caption(provider)
  history.append({'role':'assistant','content':answer,'provider':provider});save();st.rerun()
 with st.expander('Manage this chat'):
  if st.button('Delete chat'):
   st.session_state.chats.pop(active,None);st.session_state.chat_projects.pop(active,None);remain=chats_in(st.session_state.active_project)
   if remain:st.session_state.active_chat=remain[0]
   else:newchat(st.session_state.active_project)
   save();st.rerun()
  newname=st.text_input('Rename chat')
  if st.button('Save chat name') and newname.strip() and newname not in st.session_state.chats:
   st.session_state.chats[newname]=st.session_state.chats.pop(active);st.session_state.chat_projects[newname]=st.session_state.chat_projects.pop(active,st.session_state.active_project);st.session_state.active_chat=newname;save();st.rerun()
elif feature=='📄 PDF Assistant':
 pdf=st.file_uploader('Upload PDF',type=['pdf'])
 if pdf:
  try:
   doc=fitz.open(stream=pdf.getvalue(),filetype='pdf');text='\n'.join(p.get_text() for p in doc)
   task=st.radio('PDF task',['Ask Question','Summary','Quiz'])
   if not text.strip():st.warning('No selectable text detected (scanned PDF).')
   elif task=='Ask Question':
    q=st.text_input('Question about PDF')
    if st.button('Ask PDF') and q.strip():st.markdown(ai('Answer only from this PDF: '+text[:80000]+'\nQuestion: '+q)[0])
   elif task=='Summary':
    if st.button('Summarize'):st.markdown(ai('Summarize this PDF: '+text[:80000])[0])
   else:
    count=st.slider('Questions',3,15,5)
    if st.button('Create quiz'):st.markdown(ai(f'Create {count} MCQs with answer key from this PDF: '+text[:80000])[0])
  except Exception as e:st.error('PDF error: '+str(e))
elif feature=='✍️ Writing Studio':
 kind=st.selectbox('Writing type',['Email','Application','Resume','Essay','Story','Social caption','Letter','Improve text','Code help','Custom']);prompt=st.text_area('Instructions')
 if st.button('Generate writing'):
  if prompt.strip():answer,provider=ai('Write '+kind+'. '+prompt);st.markdown(answer);st.caption(provider);st.download_button('Download',answer,file_name='nova_draft.txt')
  else:st.warning('Enter instructions first.')
elif feature=='🧠 My Notes':
 with st.form('notes'):
  title=st.text_input('Note title');body=st.text_area('Note content');submit=st.form_submit_button('Save note')
 if submit:
  if title.strip() and body.strip():st.session_state.notes.append({'title':title,'content':body,'date':datetime.now().strftime('%d-%m-%Y %H:%M')});save();st.rerun()
  else:st.warning('Fill in both fields.')
 for i,n in enumerate(st.session_state.notes):
  with st.expander('📌 '+n.get('title','Untitled')):
   st.write(n.get('content',''));st.caption(n.get('date',''));st.download_button('Download note',n.get('content',''),file_name=f'note_{i+1}.txt',key='ndl'+str(i))
   if st.button('Delete note',key='ndel'+str(i)):st.session_state.notes.pop(i);save();st.rerun()
elif feature=='🧮 Calculator':
 a=st.number_input('First number',value=0.0);op=st.selectbox('Operation',['+','-','×','÷','%']);b=st.number_input('Second number',value=1.0)
 if st.button('Calculate'):
  if op=='÷' and b==0:st.error('Cannot divide by zero')
  else:st.success('Result: '+str(a+b if op=='+' else a-b if op=='-' else a*b if op=='×' else a/b if op=='÷' else a*b/100))
if nav=='📚 Library':st.sidebar.info('Chat history and Notes are stored in your library.')
elif nav=='🎨 Customize':st.sidebar.info('Neon theme active.')
elif nav=='📁 Projects':st.sidebar.info('Manage projects in sidebar.')
elif nav=='🖥️ Remote':st.sidebar.info('Remote feature placeholder.')
elif nav=='🔲 Explore':st.sidebar.info('More features can be added.')
st.divider();st.markdown('<center>✨ <b>NOVA AI</b> • Gemini • Browser voice fallback</center>',unsafe_allow_html=True)
