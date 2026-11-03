import pandas as pd
import streamlit as st
from src.ui import header,resources,table
from src.simulation import simulate
from src.preprocessing import RAW_COLUMNS

header('Laboratoire de simulation','Un clic, un scénario, une décision. Aucun trafic réel ni processus continu.')
data,bundle = resources()
if 'sim_results' not in st.session_state:
    st.session_state.sim_results = []
    st.session_state.sim_context = pd.DataFrame(columns=RAW_COLUMNS)
st.info('Le scénario suspect ajoute neuf échecs synthétiques au contexte des dix minutes précédentes, puis évalue la connexion suivante. Le modèle reste libre de sa décision.')
cols = st.columns(4)
normal = cols[0].button('Générer un événement normal',use_container_width=True)
suspect = cols[1].button('Générer un événement suspect',type='primary',use_container_width=True)
random = cols[2].button('Générer un événement aléatoire',use_container_width=True)
reset = cols[3].button('Réinitialiser la session',use_container_width=True)
if reset:
    st.session_state.sim_results = []
    st.session_state.sim_context = pd.DataFrame(columns=RAW_COLUMNS)
if normal or suspect or random:
    history = pd.concat([data[RAW_COLUMNS],st.session_state.sim_context],ignore_index=True)
    result,context = simulate(history,len(st.session_state.sim_results),'normal' if normal else 'suspect' if suspect else 'random',bundle)
    st.session_state.sim_results.append(result)
    st.session_state.sim_context = pd.concat([st.session_state.sim_context,context],ignore_index=True)
if st.session_state.sim_results:
    frame = pd.concat(st.session_state.sim_results,ignore_index=True)
    last = frame.iloc[-1]
    a,b,c,d = st.columns(4)
    a.metric('Décision IA',last.status)
    b.metric('Score',f'{last.anomaly_score:.4f}')
    c.metric('Tentatives / 10 min',last.attempts_10min)
    d.metric('Échecs / 10 min',last.failed_attempts)
    st.write(last.recommendation)
    st.caption(f'{last.timestamp} · {last.user_id} · {last.device_type} · IP {last.source_ip} · nouvelle dans le contexte : {bool(last.new_ip)}')
    table(frame.iloc[::-1],'simulation')
else:
    st.markdown('<div class="hero"><b>Votre session est prête.</b><p>Générez une connexion pour observer son contexte et sa classification.</p></div>',unsafe_allow_html=True)
