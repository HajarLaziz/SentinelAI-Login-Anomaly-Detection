import streamlit as st
from src.ui import shell

st.set_page_config(page_title='Analyse des connexions',page_icon='◈',layout='wide')
shell()
navigation = st.navigation([
    st.Page('pages/1_Overview.py',title='Vue de sécurité',icon=':material/space_dashboard:',default=True),
    st.Page('pages/2_Login_Analysis.py',title='Analyse des connexions',icon=':material/query_stats:'),
    st.Page('pages/3_Anomaly_Detection.py',title='Détection des anomalies',icon=':material/fingerprint:'),
    st.Page('pages/4_Live_Simulation.py',title='Simulation',icon=':material/science:'),
    st.Page('pages/5_Model_Performance.py',title='Performance du modèle',icon=':material/donut_large:'),
])
navigation.run()
