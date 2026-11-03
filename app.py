import streamlit as st
from src.ui import shell

st.set_page_config(page_title='SentinelAI | Login Security',page_icon='🛡',layout='wide')
shell()
navigation = st.navigation([
    st.Page('pages/1_Overview.py',title='Vue de sécurité',default=True),
    st.Page('pages/2_Login_Analysis.py',title='Analyse des connexions'),
    st.Page('pages/3_Anomaly_Detection.py',title='Détection IA'),
    st.Page('pages/4_Live_Simulation.py',title='Simulation'),
    st.Page('pages/5_Model_Performance.py',title='Performance du modèle'),
])
navigation.run()
