import plotly.express as px
import streamlit as st
from src.ui import header,resources,filters,chart,table,activity

header('Analyse des connexions','Explorez les horaires, les terminaux et les signaux historiques.')
data,_ = resources()
frame = filters(data,'analytics')
search = st.text_input('Rechercher un événement, un utilisateur ou une IP')
if search:
    frame = frame[frame[['event_id','user_id','source_ip']].apply(lambda c:c.str.contains(search,case=False,regex=False)).any(axis=1)]
if frame.empty:
    st.info('Aucun résultat. Élargissez les filtres.')
else:
    activity(frame)
    for left,right in [(('login_hour','Heures de connexion'),('failed_attempts','Échecs antérieurs / 10 min')),
                       (('attempts_10min','Tentatives antérieures / 10 min'),('device_type','Types de terminaux')),
                       (('new_ip','Nouveauté IP (1 = nouvelle)'),('day_of_week','Jour de semaine (0 = lundi)'))]:
        a,b = st.columns(2)
        for col,(field,title) in [(a,left),(b,right)]:
            with col:
                chart(px.histogram(frame,x=field,title=title))
    top = frame.user_id.value_counts().head(12).rename_axis('Utilisateur').reset_index(name='Événements')
    chart(px.bar(top,x='Utilisateur',y='Événements',title='Utilisateurs les plus actifs'))
    numeric = ['failed_attempts','attempts_10min','new_ip','ip_changed','is_new_device']
    chart(px.imshow(frame[numeric].corr(),zmin=-1,zmax=1,color_continuous_scale='RdBu_r',title='Corrélations descriptives (sans causalité)'))
    st.caption(f'Valeurs manquantes : {int(frame.isna().sum().sum())} · ID dupliqués : {int(frame.event_id.duplicated().sum())}')
    table(frame,'analytics')
