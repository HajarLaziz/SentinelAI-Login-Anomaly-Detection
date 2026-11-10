"""Shared presentation components. No network or background polling."""
import pandas as pd
import plotly.express as px
import streamlit as st
from html import escape
from src.utils import ROOT, DATA, MODEL
from src.predict import load_model, predict
from src.preprocessing import safe_csv

COLORS = ['#8b5e3c','#c58a4b','#ad8b6c','#b86f50','#d8b78e']
px.defaults.color_discrete_sequence = COLORS

def shell():
    st.markdown('<style>'+ (ROOT/'assets/style.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
    st.sidebar.caption('Données simulées · exécution locale')


def header(title, subtitle):
    st.title(title)
    st.caption(subtitle)

def section(number, title, description=''):
    st.markdown(f'<div class="section-heading"><span>{escape(number)}</span><div><h3>{escape(title)}</h3><p>{escape(description)}</p></div></div>',unsafe_allow_html=True)

@st.cache_resource
def model_cached(version):
    return load_model()

@st.cache_data
def data_cached(data_version, model_version):
    frame = pd.read_csv(DATA/'login_logs.csv',parse_dates=['timestamp'])
    return predict(frame,model_cached(model_version))

def resources():
    if not (DATA/'login_logs.csv').exists() or not MODEL.exists():
        with st.spinner('Préparation initiale des données et du modèle…'):
            from src.generate_data import main as generate
            from src.train_model import train
            generate()
            if not MODEL.exists():
                train(pd.read_csv(DATA/'train_logs.csv'))
    version = MODEL.stat().st_mtime_ns
    return data_cached((DATA/'login_logs.csv').stat().st_mtime_ns, version), model_cached(version)

def chart(fig):
    fig.update_layout(template='plotly_white', paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
                      colorway=COLORS, font=dict(family='Arial',color='#796453',size=15),
                      title=dict(font=dict(size=19,color='#3e2c23'),x=.04,y=.94),
                      margin=dict(l=25,r=25,t=65,b=65),height=350,legend_title_text='',
                      legend=dict(orientation='h',y=-.22,x=0,xanchor='left',yanchor='top'))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#eee3d6',zerolinecolor='#eee3d6')
    st.plotly_chart(fig,use_container_width=True,theme=None,config={'displaylogo':False})

def filters(frame, key):
    with st.expander('Affiner la vue',expanded=True):
        cols = st.columns([2,2,1,1,1])
        dates = cols[0].date_input('Période',value=(frame.timestamp.min().date(),frame.timestamp.max().date()),key=key+'date')
        users = cols[1].multiselect('Utilisateurs',sorted(frame.user_id.unique()),key=key+'user')
        status = cols[2].selectbox('Statut',['Tous','Normal','Suspect'],key=key+'status')
        novelty = cols[3].selectbox('IP',['Toutes','Nouvelle','Connue'],key=key+'ip')
        device = cols[4].selectbox('Terminal',['Tous']+sorted(frame.device_type.unique()),key=key+'device')
    out = frame.copy()
    if isinstance(dates,(tuple,list)) and len(dates)==2:
        out = out[out.timestamp.dt.date.between(*dates)]
    if users:
        out = out[out.user_id.isin(users)]
    if status != 'Tous':
        out = out[out.status==status]
    if novelty != 'Toutes':
        out = out[out.new_ip==int(novelty=='Nouvelle')]
    if device != 'Tous':
        out = out[out.device_type==device]
    return out

def table(frame,key):
    st.dataframe(frame,use_container_width=True,hide_index=True)
    st.download_button('Exporter CSV',safe_csv(frame),file_name=f'connexions_{key}.csv',mime='text/csv',key=key+'download',icon=':material/download:')

def activity(frame):
    counts = frame.assign(jour=frame.timestamp.dt.floor('D')).groupby(['jour','status']).size().reset_index(name='Événements')
    chart(px.area(counts,x='jour',y='Événements',color='status',color_discrete_map={'Normal':COLORS[0],'Suspect':COLORS[1]},title='Activité des authentifications'))
