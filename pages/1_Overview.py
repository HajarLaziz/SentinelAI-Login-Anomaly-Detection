import plotly.express as px
import streamlit as st
from src.ui import header, resources, filters, chart, table, activity, section, COLORS

header('Vue de sécurité','Historique des authentifications et connexions suspectes. Données simulées.')
data,bundle = resources()
st.markdown(f'''<div class="hero"><div class="hero-grid"><div><h2>Résumé des connexions</h2><div class="hero-foot"><span>Isolation Forest · modèle chargé</span><span>{len(data):,} événements fictifs</span><span>Historique au {data.timestamp.max():%d/%m/%Y}</span></div></div><div class="hero-art" aria-hidden="true"><span>◈</span></div></div></div>''',unsafe_allow_html=True)
frame = filters(data,'overview')
if frame.empty:
    st.info('Aucun événement ne correspond aux filtres.')
else:
    section('01','Indicateurs','Indicateurs calculés sur votre sélection actuelle.')
    cols = st.columns(6)
    values = [('Événements',len(frame)),('Normaux',int((frame.prediction==0).sum())),('Suspects',int(frame.prediction.sum())),('Taux suspect',f'{frame.prediction.mean():.1%}'),('Utilisateurs',frame.user_id.nunique()),('Échecs',int((frame.login_success==0).sum()))]
    for col,(label,value) in zip(cols,values):
        col.metric(label,value)
    section('02','Activité des connexions','Évolution de l’activité et répartition des décisions du modèle.')
    a,b = st.columns([1.8,1])
    with a:
        activity(frame)
    with b:
        donut = px.pie(frame,names='status',hole=.78,title='Décisions du modèle',color='status',color_discrete_map={'Normal':COLORS[0],'Suspect':COLORS[1]})
        donut.update_traces(textinfo='none',marker=dict(line=dict(color='white',width=4)))
        donut.add_annotation(text=f'<b>{frame.prediction.mean():.1%}</b><br><span style="font-size:15px">suspects</span>',x=.5,y=.5,showarrow=False,font=dict(size=25,color='#3e2c23'))
        chart(donut)
    section('03','Connexions à vérifier','Les 100 connexions suspectes les plus récentes dans votre sélection.')
    table(frame[frame.prediction==1].sort_values('timestamp',ascending=False).head(100)[['event_id','user_id','timestamp','source_ip','failed_attempts','anomaly_score','severity']],'recent')
    section('04','Explorer les habitudes','Horaires observés et scénarios du simulateur, distincts des prédictions du modèle.')
    a,b = st.columns(2)
    with a:
        chart(px.histogram(frame,x='login_hour',nbins=24,title='Activité par heure',labels={'login_hour':'Heure'}))
    with b:
        chart(px.histogram(frame[frame.is_anomaly==1],x='anomaly_type',title='Scénarios simulés',color_discrete_sequence=[COLORS[2]],labels={'anomaly_type':'Scénario'}))
