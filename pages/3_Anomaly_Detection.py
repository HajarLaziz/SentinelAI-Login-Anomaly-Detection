from datetime import timedelta
from uuid import uuid4
import pandas as pd
import streamlit as st
from src.ui import header,resources,table
from src.predict import assess_event,predict,contributing_factors
from src.preprocessing import read_upload

header('Détection IA','Évaluer une connexion dans son contexte historique.')
data,bundle = resources()
a,b,c = st.columns(3)
a.metric('Algorithme','Isolation Forest')
b.metric('Arbres',bundle['n_estimators'])
c.metric('Contamination',f'{bundle["contamination"]:.0%}',help='Proportion utilisée pour fixer le seuil sur les données d’entraînement.')
st.caption('Le score est −decision_function : positif = suspect. Le percentile mesure un rang relatif, jamais une probabilité d’attaque.')
manual,upload,scored = st.tabs(['Évaluer une connexion','Importer un CSV','Historique évalué'])
with manual:
    with st.form('manual_event'):
        a,b = st.columns(2)
        user = a.text_input('Identifiant utilisateur',value='USR-0001',max_chars=128)
        ip = b.text_input('Adresse IP',value='192.0.2.42',max_chars=45)
        day = a.date_input('Date',value=(data.timestamp.max()+timedelta(days=1)).date())
        hour = b.time_input('Heure',value=pd.Timestamp('14:00').time())
        device = a.selectbox('Type de terminal',['desktop','mobile','tablet','unknown'])
        success = b.checkbox('Authentification réussie',value=True)
        submit = st.form_submit_button('Analyser la connexion',type='primary')
    if submit:
        try:
            event = dict(event_id='MAN-'+uuid4().hex[:12],user_id=user.strip(),timestamp=pd.Timestamp.combine(day,hour),source_ip=ip.strip(),device_type=device,login_success=int(success))
            result = assess_event(event,data,bundle)
            row = result.iloc[0]
            if row.prediction:
                st.warning('Connexion suspecte — Cette connexion diffère des habitudes d’authentification usuelles.')
            else:
                st.success('Connexion normale selon le modèle — ce résultat ne garantit pas son innocuité.')
            a,b,c = st.columns(3)
            a.metric('Score d’anomalie',f'{row.anomaly_score:.4f}')
            b.metric('Percentile historique',f'{row.relative_percentile:.1f}',help='Rang dans les scores d’entraînement, de 0 à 100. Non calibré en probabilité.')
            c.metric('Contexte disponible',f'{row.history_events} événements')
            if row.history_events == 0:
                st.info('Aucun historique antérieur pour ce compte. IP et terminal sont inconnus dans ce contexte ; leur nouveauté réelle ne peut pas être établie.')
            st.write(row.recommendation)
            st.caption('Indicateurs descriptifs fondés sur des règles, pas une explication causale du modèle :')
            st.write(' · '.join(contributing_factors(row)) or 'Aucun signal simple isolé.')
            table(result,'manual')
        except (ValueError,TypeError) as exc:
            st.error(str(exc))
with upload:
    st.info('CSV fictif uniquement, 10 Mo maximum. Colonnes : event_id, user_id, timestamp, source_ip, device_type, login_success. Les variables sont recalculées depuis le seul historique du fichier, sans fusion avec le jeu local.')
    file = st.file_uploader('Journal synthétique',type=['csv'])
    if file is not None:
        try:
            with st.spinner('Validation et calcul du contexte…'):
                imported = read_upload(file.getvalue())
                result = predict(imported,bundle)
            st.success(f'{len(result)} événements · {result.prediction.sum()} suspects')
            table(result,'import')
        except ValueError as exc:
            st.error(str(exc))
with scored:
    st.caption('Les événements d’entraînement et de test sont présentés ici. L’évaluation indépendante utilise uniquement le test.')
    table(data.sort_values('anomaly_score',ascending=False),'scored')
