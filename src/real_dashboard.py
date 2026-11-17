"""Single-screen dashboard backed exclusively by the downloaded LANL subset."""
import json
from uuid import uuid4
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from src import lanl
from src.ui import chart, section
from src.preprocessing import safe_csv

LABELS={'event_id':'Événement source','user_id':'Compte anonymisé','source_host':'Machine source',
        'destination_host':'Machine destination','relative_time':'Instant relatif','relative_hour':'Heure relative',
        'failed_attempts':'Échecs / 10 min','attempts_10min':'Tentatives / 10 min','new_source':'Source nouvelle',
        'new_destination':'Destination nouvelle','anomaly_score':'Score d’anomalie',
        'redteam_label':'Annotation red team','status':'Décision','outcome':'Résultat',
        'relative_percentile':'Percentile historique','history_events':'Événements antérieurs'}

@st.cache_resource
def bundle_cached(version): return joblib.load(lanl.MODEL)

@st.cache_data
def resources(data_version,model_version):
    frame=pd.read_csv(lanl.DATA/'login_logs.csv')
    return lanl.predict(frame,bundle_cached(model_version))

def table(frame,key,limit=1000):
    columns=[c for c in ['event_id','user_id','relative_time','source_host','destination_host','outcome',
        'failed_attempts','attempts_10min','new_source','new_destination','anomaly_score','status','redteam_label'] if c in frame]
    st.dataframe(frame[columns].head(limit),hide_index=True,width='stretch',column_config=LABELS)
    if len(frame)>limit: st.caption(f'{limit:,} lignes affichées ; export complet de la sélection.')
    st.download_button('Exporter CSV',safe_csv(frame),f'lanl_{key}.csv','text/csv',key=key+'_csv')

def filters(data):
    with st.expander('Filtrer les connexions'):
        a,b,c=st.columns(3)
        user=a.multiselect('Comptes',sorted(data.user_id.unique()))
        status=b.selectbox('Décision',['Toutes','Habituel','À vérifier'])
        outcome=c.selectbox('Résultat',['Tous','Success','Fail'])
    out=data.tail(st.session_state['real_limit'])
    out=out[out.relative_hour.between(*st.session_state['real_hours'])]
    out=out[out.relative_percentile>=st.session_state['real_percentile']]
    if user: out=out[out.user_id.isin(user)]
    if status!='Toutes':out=out[out.status==status]
    if outcome!='Tous':out=out[(out.outcome=='Success') if outcome=='Success' else (out.outcome!='Success')]
    return out

def performance(data,bundle):
    st.subheader('Évaluation sur le troisième jour relatif')
    test=data[data.time>=lanl.CUTOFF]
    result=lanl.evaluate(test,bundle)
    st.info('Les annotations LANL identifient des actions red team connues. Un événement non annoté n’est pas une preuve de comportement normal. Les métriques ci-dessous sont relatives à ces annotations partielles.')
    st.caption(f'{len(test):,} événements de test · {test.redteam_label.sum()} annotés red team · aucun entraînement sur ce jour.')
    score=result['Isolation Forest']
    cols=st.columns(4)
    for col,key,title in zip(cols,['precision','recall','f1','false_positive_rate'],['Précision / annotations','Rappel red team','F1 / annotations','Alertes parmi non annotés']):
        col.metric(title,f'{score[key]:.3f}' if score[key] is not None else 'Non disponible')
    if test.redteam_label.nunique()<2:
        st.warning('Une seule classe annotée dans ce test : ROC-AUC et PR-AUC non calculables.')
    a,b=st.columns(2)
    with a: chart(px.imshow(score['confusion_matrix'],x=['Habituel','À vérifier'],y=['Non annoté','Red team'],text_auto=True,title='Décisions et annotations'),accent='indigo')
    with b:
        comp=pd.DataFrame(result).T[['precision','recall','f1']].reset_index().melt(id_vars='index')
        chart(px.bar(comp,x='variable',y='value',color='index',barmode='group',title='Forêt et règles sur le même test'),accent='turquoise')
    st.dataframe(pd.DataFrame(result).T.drop(columns='confusion_matrix'),width='stretch')
    chart(px.histogram(test,x='anomaly_score',color=test.redteam_label.map({0:'Non annoté',1:'Red team'}),barmode='overlay',nbins=60,title='Distribution des scores de test'),accent='rose')
    st.caption('ROC-AUC, AP et PR-AUC sont fondées sur le score continu, jamais sur une probabilité calibrée. La contamination de 1 % a été fixée avant cette évaluation, sans optimisation sur le test.')
    with st.expander('Configuration et provenance'):
        st.json({k:bundle[k] for k in ['dataset','scope','features','training_rows','train_end','contamination','n_estimators']})
        st.markdown('[Source officielle LANL](https://csr.lanl.gov/data/cyber1/) · DOI : 10.17021/1179829')

def verify(data,bundle):
    manual,upload,replay=st.tabs(['Évaluer une saisie','Importer un CSV','Relire des événements réels'])
    with manual:
        st.caption('Saisie de démonstration, séparée du dataset collecté. Le modèle utilise seulement le passé du compte au temps relatif choisi. Périmètre : NTLM / Network / LogOn.')
        with st.form('real_manual'):
            a,b=st.columns(2)
            user=a.text_input('Compte anonymisé',value=str(data.user_id.iloc[0]))
            seconds=b.number_input('Temps relatif (secondes)',min_value=0,value=int(data.time.max())+1,step=1)
            source=a.text_input('Machine source',value=str(data.source_host.iloc[0]))
            destination=b.text_input('Machine destination',value=str(data.destination_host.iloc[0]))
            outcome=a.selectbox('Issue',['Success','Fail'])
            submitted=st.form_submit_button('Analyser la connexion',type='primary')
        if submitted:
            try:
                event=dict(event_id='MAN-'+uuid4().hex[:10],time=int(seconds),user_id=user.strip(),source_host=source.strip(),destination_host=destination.strip(),outcome=outcome)
                result=lanl.assess(event,data,bundle);row=result.iloc[0]
                (st.warning if row.prediction else st.success)(f'{row.status} · {row.recommendation}')
                a,b,c=st.columns(3);a.metric('Score',f'{row.anomaly_score:.4f}');b.metric('Percentile',f'{row.relative_percentile:.1f}');c.metric('Historique',int(row.history_events))
                if row.history_events==0:st.info('Compte sans historique : la nouveauté indique seulement une absence dans le contexte disponible.')
                table(result,'manual_real')
            except (ValueError,TypeError) as exc:st.error(str(exc))
    with upload:
        st.info('CSV de même schéma : event_id, time, user_id, source_host, destination_host, outcome. Temps en secondes relatives ; machines C… ; comptes U…@domaine. Contexte du fichier uniquement. 10 Mo maximum.')
        file=st.file_uploader('Journal à évaluer',type=['csv'])
        if file:
            try:
                with st.spinner('Validation du journal…'): result=lanl.predict(lanl.read_upload(file.getvalue()),bundle)
                table(result,'uploaded_real')
            except ValueError as exc:st.error(str(exc))
    with replay:
        st.subheader('Relecture du test réel')
        st.caption('Aucune connexion générée : chaque ligne ci-dessous est un événement du troisième jour LANL. Les scores utilisent son contexte chronologique pré-calculé, sans ajouter les clics à l’historique.')
        test=data[data.time>=lanl.CUTOFF]
        pool_name=st.selectbox('Événements à relire',['Tous','Échecs réels','Annotations red team'])
        pool=test if pool_name=='Tous' else test[test.outcome!='Success'] if pool_name=='Échecs réels' else test[test.redteam_label==1]
        a,b=st.columns(2)
        advance=a.button('Lire l’événement suivant',type='primary',disabled=pool.empty)
        reset=b.button('Réinitialiser la relecture')
        if 'real_replay_ids' not in st.session_state or reset:st.session_state['real_replay_ids']=[]
        if advance:
            remaining=pool[~pool.event_id.isin(st.session_state['real_replay_ids'])]
            if remaining.empty:st.info('Tous les événements de cette sélection ont été relus.')
            else:st.session_state['real_replay_ids'].append(remaining.iloc[0].event_id)
        if pool.empty:st.info('Aucun événement correspondant dans ce sous-ensemble.')
        ids=st.session_state['real_replay_ids']
        if ids:
            seen=data.set_index('event_id',drop=False).loc[ids].iloc[::-1]
            row=seen.iloc[0]
            st.write(f'{row.relative_time} · {row.user_id} · {row.source_host} → {row.destination_host}')
            a,b,c=st.columns(3);a.metric('Décision',row.status);b.metric('Score',f'{row.anomaly_score:.4f}');c.metric('Échecs / 10 min',int(row.failed_attempts))
            st.write(row.recommendation);table(seen,'replay_real')

def render():
    st.markdown('<style>'+(lanl.ROOT/'assets/style.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
    if not (lanl.DATA/'login_logs.csv').exists() or not lanl.MODEL.exists():
        st.error('Données réelles ou modèle absents. Exécutez python -m src.import_lanl puis python -m src.lanl. Aucun jeu synthétique n’est chargé en remplacement.')
        st.stop()
    version=lanl.MODEL.stat().st_mtime_ns;bundle=bundle_cached(version)
    data=resources((lanl.DATA/'login_logs.csv').stat().st_mtime_ns,version)
    manifest=json.loads((lanl.DATA/'prepared_manifest.json').read_text(encoding='utf-8'))
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><strong>LoginGuard AI</strong></div><div class="sidebar-subtitle">Authentifications réelles<br>LANL · données anonymisées</div>',unsafe_allow_html=True)
        st.markdown('<div class="sidebar-label">MODÈLE DE DÉTECTION</div>',unsafe_allow_html=True)
        st.selectbox('Modèle',['Isolation Forest'],disabled=True,label_visibility='collapsed')
        st.markdown('<div class="sidebar-label">HISTORIQUE AFFICHÉ</div>',unsafe_allow_html=True)
        st.slider('Nombre de connexions',100,len(data),len(data),key='real_limit')
        st.slider('Heures relatives',0,23,(0,23),key='real_hours')
        st.markdown('<div class="sidebar-label">FILTRE DES ALERTES</div>',unsafe_allow_html=True)
        st.slider('Percentile minimum',0,100,0,key='real_percentile',help='Filtre d’affichage, pas une probabilité ni un changement de seuil.')
        st.markdown('<div class="sidebar-note">Filtres : vue d’ensemble et explorateur.<br>Dates, IP et types de terminaux non publiés par la source.</div>',unsafe_allow_html=True)
        st.caption('Source : LANL · DOI 10.17021/1179829')
    st.markdown('<div class="hero"><div class="eyebrow">AUTHENTIFICATIONS RÉELLES · LANL</div><h1>LoginGuard AI</h1><p>Observer les connexions, examiner les alertes et relire des événements anonymisés d’un réseau d’entreprise.</p><span class="chip">Isolation Forest · modèle local</span><span class="chip">NTLM / Network / LogOn · 3 jours relatifs</span></div>',unsafe_allow_html=True)
    st.caption('La date réelle et le fuseau horaire ne sont pas publiés. J+0 désigne le début du jeu ; « heure relative » ne signifie pas heure locale. Aucun identifiant de machine n’est présenté comme une adresse IP.')
    summary,explorer,quality,verification=st.tabs(['Vue d’ensemble','Explorer les connexions','Performance du modèle','Vérifier une connexion'])
    with summary:
        frame=filters(data)
        if frame.empty:st.info('Aucun événement ne correspond aux filtres.')
        else:
            values=[('Événements',len(frame)),('Habituels',int((frame.prediction==0).sum())),('À vérifier',int(frame.prediction.sum())),('Taux d’alerte',f'{frame.prediction.mean():.1%}'),('Comptes',frame.user_id.nunique()),('Échecs',int((frame.outcome!='Success').sum()))]
            for col,(title,value) in zip(st.columns(6),values):col.metric(title,value)
            section('','Activité des connexions','Statut prédit par le modèle, distinct des annotations red team.')
            a,b=st.columns(2)
            with a:chart(px.histogram(frame,x='relative_hour',color='status',nbins=24,title='Connexions par heure relative',labels=LABELS),accent='violet')
            with b:chart(px.scatter(frame.sample(min(2000,len(frame)),random_state=42),x='attempts_10min',y='failed_attempts',color='status',opacity=.6,title='Tentatives et échecs récents',labels=LABELS),accent='rose')
            a,b,c=st.columns([1.3,1,1])
            with a:
                counts=frame.groupby(['relative_day','status']).size().reset_index(name='Événements')
                chart(px.bar(counts,x='relative_day',y='Événements',color='status',title='Activité par jour relatif',labels={'relative_day':'Jour relatif'}),accent='blue')
            with b:chart(px.histogram(frame,x='anomaly_score',nbins=40,title='Scores d’anomalie',labels=LABELS),accent='indigo')
            with c:chart(px.pie(frame,names='status',hole=.75,title='Décisions'),accent='turquoise')
            section('','Connexions à vérifier','100 alertes les plus récentes de la sélection.')
            table(frame[frame.prediction==1].tail(100).iloc[::-1],'recent_real')
    with explorer:
        st.subheader('Journal réel anonymisé')
        st.caption('Les réglages latéraux et les filtres de la vue d’ensemble s’appliquent à cet explorateur.')
        search=st.text_input('Rechercher un compte, une machine ou un événement')
        view=frame
        if search:view=view[view[['user_id','source_host','destination_host','event_id']].apply(lambda c:c.str.contains(search,case=False,regex=False)).any(axis=1)]
        st.caption(f'{len(view):,} événements sélectionnés')
        if view.empty:st.info('Aucun résultat.')
        table(view,'explorer_real')
        with st.expander('Provenance et sélection du dataset'):st.json(manifest)
    with quality:performance(data,bundle)
    with verification:verify(data,bundle)
