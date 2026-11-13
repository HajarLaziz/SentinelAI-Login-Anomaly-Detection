import plotly.express as px
import streamlit as st
from src.ui import header, resources, filters, chart, table, activity, section, COLORS, context_strip

def render():
    if not st.session_state.get('_single_dashboard'):
        header('Vue de sécurité','Historique des authentifications et connexions suspectes. Données simulées.')
    data,bundle = resources()
    st.caption(f'Historique au {data.timestamp.max():%d/%m/%Y} · {data.user_id.nunique()} utilisateurs fictifs')
    frame = filters(data,'overview')
    if frame.empty:
        st.info('Aucun événement ne correspond aux filtres.')
    else:
        values = [('Événements',len(frame)),('Normaux',int((frame.prediction==0).sum())),('Suspects',int(frame.prediction.sum())),('Taux suspect',f'{frame.prediction.mean():.1%}'),('Utilisateurs',frame.user_id.nunique()),('Échecs',int((frame.login_success==0).sum()))]
        for col,(label,value) in zip(st.columns(6),values):
            col.metric(label,value)
        section('02','Habitudes de connexion','Volume et signaux observés sur la sélection.')
        left,right = st.columns(2)
        with left:
            hourly = frame.groupby(['login_hour','status']).size().reset_index(name='Événements')
            chart(px.bar(hourly,x='login_hour',y='Événements',color='status',title='À quelles heures se connecte-t-on ?',barmode='stack'),accent='violet')
        with right:
            sample = frame.sample(min(len(frame),2000),random_state=42)
            scatter = px.scatter(sample,x='attempts_10min',y='failed_attempts',color='status',symbol='new_ip',opacity=.65,title='Fréquence et échecs récents',hover_data=['user_id','timestamp'])
            chart(scatter,accent='rose')
        left,middle,right = st.columns([1.3,1,1])
        with left:
            activity(frame)
        with middle:
            scores = px.histogram(frame,x='anomaly_score',nbins=35,title='Distribution des scores')
            scores.add_vline(x=0,line_dash='dash',line_color='#9a563b',annotation_text='Seuil',annotation_position='top right')
            chart(scores,accent='blue')
        with right:
            donut = px.pie(frame,names='status',hole=.76,title='Décisions du modèle')
            donut.update_traces(textinfo='none')
            donut.add_annotation(text=f'<b>{frame.prediction.mean():.1%}</b><br><span style="font-size:13px">suspects</span>',x=.5,y=.5,showarrow=False,font=dict(size=27,color='#493322'))
            chart(donut,accent='turquoise')
        section('03','Connexions à vérifier','Les 100 connexions suspectes les plus récentes dans votre sélection.')
        table(frame[frame.prediction==1].sort_values('timestamp',ascending=False).head(100)[['event_id','user_id','timestamp','source_ip','failed_attempts','anomaly_score','severity']],'recent')
