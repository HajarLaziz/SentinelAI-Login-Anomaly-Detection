"""Single-screen dashboard; reusable views retain the original ML workflow."""
import streamlit as st
from src.ui import shell, resources, filters, table
from src.views import overview, detection, simulation, performance

st.set_page_config(page_title='Analyse des connexions', page_icon='🔒', layout='wide')
# Register only this dashboard, hiding Streamlit's legacy pages directory.
st.navigation([st.Page(lambda: None, title='Dashboard', default=True)], position='hidden')
st.session_state['_single_dashboard'] = True
shell()
data, bundle = resources()
st.markdown('<div class="hero"><div class="eyebrow">SURVEILLANCE DES AUTHENTIFICATIONS</div><h1>Chaque connexion, en perspective.</h1><p>Observez les habitudes, repérez les connexions inhabituelles et examinez les événements à vérifier.</p><span class="chip">Isolation Forest · modèle chargé</span><span class="chip">Données simulées · analyse locale</span></div>', unsafe_allow_html=True)
summary, explorer, quality, verification = st.tabs(['Vue d’ensemble', 'Explorer les connexions', 'Performance du modèle', 'Vérifier une connexion'])
with summary:
    overview.render()
with explorer:
    st.subheader('Journal des connexions')
    frame = filters(data, 'explorer')
    search = st.text_input('Rechercher un événement, un utilisateur ou une IP')
    if search:
        frame = frame[frame[['event_id','user_id','source_ip']].apply(lambda c: c.str.contains(search, case=False, regex=False)).any(axis=1)]
    st.caption(f'{len(frame):,} événements dans la sélection')
    if frame.empty:
        st.info('Aucun résultat. Élargissez les filtres.')
    table(frame, 'explorer')
with quality:
    performance.render()
with verification:
    detection.render()
    st.divider()
    simulation.render()
