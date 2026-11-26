
# ===== NOVA AI PREMIUM INTRO ANIMATION =====

st.markdown("""
<style>
.nova-splash{
 position:fixed;
 inset:0;
 z-index:999999;
 background:radial-gradient(circle at center,#20104d,#070817 75%);
 display:flex;
 align-items:center;
 justify-content:center;
 flex-direction:column;
 overflow:hidden;
 animation:splash-out 1.5s ease 5.5s forwards;
 pointer-events:none;
}

.nova-logo-wrap{
 display:flex;
 align-items:center;
 flex-direction:column;
}

.nova-splash-infinity{
 font-size:30px;
 line-height:1.2;
 background:linear-gradient(90deg,#ff00cc,#7c3aed,#00e5ff,#00ff88,#ff00cc);
 background-size:300%;
 -webkit-background-clip:text;
 -webkit-text-fill-color:transparent;
 filter:drop-shadow(0 0 15px #a855f7);
 animation:logo-grow 2s ease forwards,
           logo-spin 4s linear 2s infinite,
           logo-glow 2s ease-in-out infinite;
}

.nova-splash-name{
 font-size:clamp(45px,10vw,75px);
 font-weight:900;
 letter-spacing:4px;
 background:linear-gradient(90deg,#ff00cc,#00e5ff,#a855f7,#00ff88,#ff00cc);
 background-size:400%;
 -webkit-background-clip:text;
 -webkit-text-fill-color:transparent;
 animation:name-appear 2s ease 1s forwards,
           name-shine 4s linear infinite,
           name-glow 2s ease-in-out infinite;
 opacity:0;
}

.nova-welcome{
 color:white;
 font-size:clamp(18px,5vw,28px);
 letter-spacing:2px;
 text-align:center;
 opacity:0;
 animation:welcome-appear 2s ease 2s forwards;
 text-shadow:0 0 12px white;
}

.nova-butterfly{
 position:absolute;
 font-size:35px;
 animation:butterfly-fly 5s ease-in-out infinite;
}

.nova-b1{left:8%;top:20%;filter:hue-rotate(0deg);animation-delay:0s}
.nova-b2{left:80%;top:15%;filter:hue-rotate(90deg);animation-delay:1s}
.nova-b3{left:15%;top:75%;filter:hue-rotate(180deg);animation-delay:2s}
.nova-b4{left:85%;top:70%;filter:hue-rotate(230deg);animation-delay:1.5s}
.nova-b5{left:45%;top:85%;filter:hue-rotate(300deg);animation-delay:.5s}
.nova-b6{left:50%;top:10%;filter:hue-rotate(140deg);animation-delay:2.5s}

@keyframes logo-grow{
 0%{transform:scale(.1)}
 70%{transform:scale(1.5)}
 100%{transform:scale(1)}
}

@keyframes logo-spin{
 from{transform:rotate(0deg)}
 to{transform:rotate(360deg)}
}

@keyframes logo-glow{
 0%,100%{filter:drop-shadow(0 0 10px #a855f7)}
 50%{filter:drop-shadow(0 0 30px #22d3ee)}
}

@keyframes name-appear{
 from{opacity:0;transform:translateY(30px)}
 to{opacity:1;transform:translateY(0)}
}

@keyframes name-shine{
 0%,100%{background-position:0%}
 50%{background-position:100%}
}

@keyframes name-glow{
 0%,100%{text-shadow:0 0 5px #a855f7}
 50%{text-shadow:0 0 20px #22d3ee}
}

@keyframes welcome-appear{
 from{opacity:0;transform:translateY(20px)}
 to{opacity:1;transform:translateY(0)}
}

@keyframes butterfly-fly{
 0%{transform:translate(0,0) rotate(0deg)}
 25%{transform:translate(35px,-45px) rotate(15deg)}
 50%{transform:translate(-30px,-80px) rotate(-15deg)}
 75%{transform:translate(20px,-35px) rotate(10deg)}
 100%{transform:translate(0,0) rotate(0deg)}
}

@keyframes splash-out{
 to{opacity:0;visibility:hidden}
}

</style>
""", unsafe_allow_html=True)

# Main NOVA logo
st.markdown("""
<div class="nova-hero">
  <div style="
    font-size:80px;
    background:linear-gradient(90deg,#a855f7,#22d3ee,#ec4899);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation:logo-spin 12s linear infinite,logo-glow 3s ease infinite;
    display:inline-block;
  ">∞</div>

  <div class="nova-brand">NOVA AI</div>

  <div style="
    color:white;
    font-size:20px;
    letter-spacing:2px;
    text-shadow:0 0 10px #a855f7;
  ">Welcome to NOVA AI</div>
</div>
""", unsafe_allow_html=True)

# Opening splash: show only once per Streamlit session
if not st.session_state.get("nova_splash_shown", False):

    st.markdown("""
    <div class="nova-splash">

      <div class="nova-butterfly nova-b1">🦋</div>
      <div class="nova-butterfly nova-b2">🦋</div>
      <div class="nova-butterfly nova-b3">🦋</div>
      <div class="nova-butterfly nova-b4">🦋</div>
      <div class="nova-butterfly nova-b5">🦋</div>
      <div class="nova-butterfly nova-b6">🦋</div>

      <div class="nova-logo-wrap">
        <div class="nova-splash-infinity">∞</div>
        <div class="nova-splash-name">NOVA AI</div>
        <div class="nova-welcome">Welcome to NOVA AI</div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    st.session_state.nova_splash_shown = True

# ===== END PREMIUM INTRO =====
