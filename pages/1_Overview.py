import plotly.express as px
import streamlit as st
from src.ui import header, resources, filters, chart, table, activity

header('Vue de sécurité','Une lecture claire des comportements d’authentification. Toutes les données sont simulées.')
data,bundle = resources()
st.markdown(f'<div class="hero"><b>Modèle actif · Isolation Forest</b><p>{len(data):,} événements · {data.user_id.nunique()} utilisateurs fictifs · historique jusqu’au {data.timestamp.max():%d/%m/%Y %H:%M}</p></div>',unsafe_allow_html=True)
frame = filters(data,'overview')
if frame.empty:
    st.info('Aucun événement ne correspond aux filtres.')
else:
    cols = st.columns(6)
    values = [('Événements',len(frame)),('Normaux IA',int((frame.prediction==0).sum())),('Suspects IA',int(frame.prediction.sum())),('Taux suspect',f'{frame.prediction.mean():.1%}'),('Utilisateurs',frame.user_id.nunique()),('Échecs',int((frame.login_success==0).sum()))]
    for col,(label,value) in zip(cols,values):
        col.metric(label,value)
    activity(frame)
    a,b = st.columns(2)
    with a:
        chart(px.pie(frame,names='status',hole=.7,title='Décisions du modèle',color='status',color_discrete_map={'Normal':'#22d3ee','Suspect':'#f59e0b'}))
    with b:
        chart(px.histogram(frame,x='login_hour',nbins=24,title='Activité par heure'))
    st.subheader('Connexions à vérifier')
    table(frame[frame.prediction==1].sort_values('timestamp',ascending=False).head(100)[['event_id','user_id','timestamp','source_ip','failed_attempts','anomaly_score','severity']],'recent')
    chart(px.histogram(frame[frame.is_anomaly==1],x='anomaly_type',title='Scénarios simulés — vérité terrain, distincte des prédictions'))
