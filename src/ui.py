"""Shared presentation components. No network or background polling."""
import pandas as pd
import plotly.express as px
import streamlit as st
from html import escape
from src.utils import ROOT, DATA, MODEL
from src.predict import load_model, predict
from src.preprocessing import safe_csv

COLORS = ['#ddd2f8','#bce3e5','#c8d9fa','#eccbdd','#d7ccef']
SERIES_OUTLINES = ['#7952d1','#078695','#3d70d4','#ba4c88','#6850ba']
CHART_ACCENTS = {'violet':0, 'turquoise':1, 'blue':2, 'rose':3, 'indigo':4}
px.defaults.color_discrete_sequence = COLORS
LABELS = {
    'event_id':'Événement','user_id':'Utilisateur','timestamp':'Date et heure',
    'source_ip':'Adresse IP','failed_attempts':'Échecs récents','attempts_10min':'Tentatives / 10 min',
    'login_hour':'Heure de connexion','day_of_week':'Jour de semaine','device_type':'Type de terminal',
    'new_ip':'Nouvelle IP','is_new_device':'Nouveau type de terminal','ip_changed':'Changement d’IP',
    'anomaly_score':'Score d’anomalie','status':'Statut','severity':'Niveau de vérification',
    'is_anomaly':'Scénario suspect','anomaly_type':'Scénario','prediction':'Décision (0 / 1)',
    'login_success':'Connexion réussie','relative_percentile':'Percentile historique',
    'recommendation':'Recommandation','history_events':'Événements antérieurs',
    'count':'Événements','jour':'Date','variable':'Mesure','value':'Valeur',
    'precision':'Précision','recall':'Rappel','accuracy':'Exactitude','f1':'Score F1',
    'false_positive_rate':'Taux de fausses alertes','false_positives':'Fausses alertes',
    'false_negatives':'Anomalies manquées','contamination':'Contamination',
}

def shell():
    st.markdown('<style>'+ (ROOT/'assets/style.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="nav-heading">Votre espace</div>',unsafe_allow_html=True)
        st.page_link('pages/1_Overview.py',label='Vue d’ensemble',icon=':material/grid_view:')
        st.page_link('pages/2_Login_Analysis.py',label='Connexions',icon=':material/query_stats:')
        st.markdown('<div class="nav-group">ANALYSER</div>',unsafe_allow_html=True)
        st.page_link('pages/3_Anomaly_Detection.py',label='Détecter une anomalie',icon=':material/fingerprint:')
        st.page_link('pages/4_Live_Simulation.py',label='Simuler une connexion',icon=':material/science:')
        st.page_link('pages/5_Model_Performance.py',label='Évaluer le modèle',icon=':material/donut_large:')
        st.markdown('<div class="nav-footer"><span class="context-dot"></span>Données simulées<br><span>Traitement local</span></div>',unsafe_allow_html=True)


def header(title, subtitle):
    st.title(title)
    st.caption(subtitle)

def context_strip(items):
    """A compact factual summary, with escaped content from the dataset."""
    content = ''.join(f'<span>{escape(str(item))}</span>' for item in items)
    st.markdown(f'<div class="context-strip">{content}</div>',unsafe_allow_html=True)

def section(number, title, description=''):
    st.markdown(f'<div class="section-heading"><div><h3>{escape(title)}</h3><p>{escape(description)}</p></div></div>',unsafe_allow_html=True)

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

def chart(fig, accent='violet'):
    # A stable palette per chart; additional series retain distinct colors.
    offset = CHART_ACCENTS[accent]
    fills = COLORS[offset:] + COLORS[:offset]
    outlines = SERIES_OUTLINES[offset:] + SERIES_OUTLINES[:offset]
    chart_outline = outlines[0]
    for index, trace in enumerate(fig.data):
        fill = fills[index % len(fills)]
        outline = outlines[index % len(outlines)]
        if trace.type in ('bar', 'histogram'):
            trace.update(marker=dict(color=fill,line=dict(color=outline,width=1.2)))
        elif trace.type == 'pie':
            trace.update(marker=dict(colors=fills,line=dict(color=chart_outline,width=1.3)))
        elif trace.type == 'scatter':
            trace.update(line=dict(color=outline,
                                   width=2,dash=['solid','dash','dot'][index % 3]),
                         marker=dict(color=fill,size=7,line=dict(color=outline,width=1.2)))
            if trace.stackgroup or (trace.fill and trace.fill != 'none'):
                trace.update(fillcolor=fill)
        elif trace.type == 'heatmap':
            trace.update(xgap=1,ygap=1)
    fig.update_coloraxes(colorscale=['#fafaff',fills[0],chart_outline])
    fig.update_layout(template='plotly_white', paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
                      colorway=fills, font=dict(family='Segoe UI, Arial',color='#60698a',size=16),
                      title=dict(font=dict(size=20,color='#202444'),x=.04,y=.94),
                      margin=dict(l=25,r=25,t=80,b=80),height=390,legend_title_text='',
                      legend=dict(orientation='h',y=-.22,x=0,xanchor='left',yanchor='top'))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#efedf6',zerolinecolor='#efedf6')
    # Translate visible labels without changing source data or exported column names.
    for axis in (fig.layout.xaxis, fig.layout.yaxis):
        if axis.title.text in LABELS:
            axis.title.text = LABELS[axis.title.text]
    for trace in fig.data:
        if trace.name in LABELS:
            trace.name = LABELS[trace.name]
    if any(trace.type == 'heatmap' for trace in fig.data):
        fig.update_layout(plot_bgcolor=chart_outline)
    st.plotly_chart(fig,use_container_width=True,theme=None,config={'displaylogo':False})

def filters(frame, key):
    with st.expander('Filtrer les connexions',expanded=False):
        period,accounts = st.columns(2)
        dates = period.date_input('Période',value=(frame.timestamp.min().date(),frame.timestamp.max().date()),key=key+'date')
        users = accounts.multiselect('Utilisateurs',sorted(frame.user_id.unique()),key=key+'user')
        status_col,ip_col,device_col = st.columns(3)
        status = status_col.selectbox('Statut',['Tous','Normal','Suspect'],key=key+'status')
        novelty = ip_col.selectbox('IP',['Toutes','Nouvelle','Connue'],key=key+'ip')
        device = device_col.selectbox('Terminal',['Tous']+sorted(frame.device_type.unique()),key=key+'device')
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
    columns = {name:label for name,label in LABELS.items() if name in frame.columns}
    if 'anomaly_score' in frame:
        columns['anomaly_score'] = st.column_config.NumberColumn('Score d’anomalie',format='%.4f')
    st.dataframe(frame,use_container_width=True,hide_index=True,row_height=42,column_config=columns)
    st.download_button('Exporter CSV',safe_csv(frame),file_name=f'connexions_{key}.csv',mime='text/csv',key=key+'download',icon=':material/download:')

def activity(frame):
    counts = frame.assign(jour=frame.timestamp.dt.floor('D')).groupby(['jour','status']).size().reset_index(name='Événements')
    chart(px.area(counts,x='jour',y='Événements',color='status',color_discrete_map={'Normal':COLORS[0],'Suspect':COLORS[1]},title='Activité des authentifications'),accent='violet')
