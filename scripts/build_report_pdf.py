"""Rebuild the academic report using verified facts and real screenshots."""
from pathlib import Path
import json, math
from xml.sax.saxutils import escape
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Flowable, Preformatted
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'docs/rapport'; OUT=ROOT/'output/pdf'; OUT.mkdir(parents=True,exist_ok=True)
F=json.loads((ASSETS/'facts.json').read_text(encoding='utf-8'))
M=json.loads((ASSETS/'metrics.json').read_text(encoding='utf-8'))
for name,file in [('Serif','times.ttf'),('Serif-Bold','timesbd.ttf'),('Serif-Italic','timesi.ttf'),('Serif-BoldItalic','timesbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='Serif-Bold',italic='Serif-Italic',boldItalic='Serif-BoldItalic')
INK=HexColor('#30251e'); BROWN=HexColor('#795437'); GOLD=HexColor('#ba9163'); LIGHT=HexColor('#f5eee4'); LINE=HexColor('#d8c8b6'); MUTED=HexColor('#6e665d')
W,H=A4; CW=W-112
styles={
 'body':ParagraphStyle('body',fontName='Serif',fontSize=11,leading=15.5,spaceAfter=10,alignment=TA_JUSTIFY,textColor=INK),
 'h1':ParagraphStyle('h1',fontName='Serif-Bold',fontSize=23,leading=28,spaceAfter=18,textColor=BROWN),
 'h2':ParagraphStyle('h2',fontName='Serif-Bold',fontSize=13,leading=17,spaceBefore=12,spaceAfter=7,textColor=BROWN),
 'caption':ParagraphStyle('caption',fontName='Serif-Italic',fontSize=9.5,leading=12,spaceBefore=7,spaceAfter=14,alignment=TA_CENTER,textColor=MUTED),
 'small':ParagraphStyle('small',fontName='Serif',fontSize=9.4,leading=12.5,spaceAfter=5,textColor=INK),
 'table':ParagraphStyle('table',fontName='Serif',fontSize=9.5,leading=12,textColor=INK),
 'eq':ParagraphStyle('eq',fontName='Serif',fontSize=12,leading=20,alignment=TA_CENTER,spaceBefore=8,spaceAfter=10,textColor=INK),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8.3,leading=12,backColor=LIGHT,borderPadding=12,spaceBefore=8,spaceAfter=12),
}
S=[]; fig_num=0
class Report(BaseDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name=='h1':
            title=f.getPlainText(); key='sec'+str(self.page)
            self.canv.bookmarkPage(key); self.canv.addOutlineEntry(title,key,0)
            if title!='Table des matières': self.notify('TOCEntry',(0,title,self.page,key))
def footer(c,d):
    if d.page==1:return
    c.saveState();c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(56,H-43,W-56,H-43)
    c.setFont('Serif',9);c.setFillColor(MUTED);c.drawString(56,H-34,'LoginGuard AI | Détection des connexions anormales')
    c.drawRightString(W-56,H-34,'FSSM · Master S3')
    c.line(56,43,W-56,43);c.drawString(56,30,'Hajar Laziz · Jihane Hamouchi');c.drawRightString(W-56,30,str(d.page));c.restoreState()
def p(t):S.append(Paragraph(t,styles['body']))
def h(t):S.append(Paragraph(t,styles['h2']))
def page(t):
    if S:S.append(PageBreak())
    S.append(Paragraph(t,styles['h1']))
def eq(t):S.append(Paragraph(t,styles['eq']))
def code(t):S.append(Preformatted(t,styles['code']))
def table(headers,rows,widths=None):
    data=[[Paragraph('<b>'+escape(str(x))+'</b>',styles['table']) for x in headers]]+[[Paragraph(escape(str(x)),styles['table']) for x in row] for row in rows]
    t=Table(data,colWidths=widths or [CW/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEABOVE',(0,0),(-1,0),1,BROWN),('LINEBELOW',(0,0),(-1,0),.6,BROWN),('LINEBELOW',(0,-1),(-1,-1),.6,BROWN),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#fcfaf7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
    S.extend([t,Spacer(1,10)])
def caption(t):
    global fig_num
    fig_num+=1;S.append(Paragraph(f'Figure {fig_num} - {t}',styles['caption']))
def screenshot(file,title):
    from PIL import Image as PILImage
    path=ASSETS/'captures'/file;w,hh=PILImage.open(path).size
    if file=='01-accueil.jpg':
        S.append(Image(str(path),width=CW,height=CW*hh/w))
    else:
        S.append(ScreenDetail(path,w,hh))
    caption(title)
class ScreenDetail(Flowable):
    # Clip only the repeated sidebar in the PDF; preserve the original capture.
    def __init__(self,path,w,h):
        Flowable.__init__(self);self.path=str(path);self.iw=w;self.ih=h
        self.left=285;self.region=w-self.left-25;self.width=CW;self.height=CW*h/self.region
    def draw(self):
        c=self.canv;c.saveState();path=c.beginPath();path.rect(0,0,self.width,self.height);c.clipPath(path,stroke=0)
        scale=CW/self.region;c.drawImage(self.path,-self.left*scale,0,width=self.iw*scale,height=self.ih*scale)
        c.restoreState()
class Diagram(Flowable):
    def __init__(self,kind,height=300):Flowable.__init__(self);self.kind=kind;self.width=CW;self.height=height
    def draw(self):
        c=self.canv
        def box(x,y,w,hh,title,sub=''):
            c.setFillColor(LIGHT);c.setStrokeColor(LINE);c.roundRect(x,y,w,hh,6,fill=1,stroke=1)
            c.setFillColor(BROWN);c.setFont('Serif-Bold',11);c.drawCentredString(x+w/2,y+hh-21,title)
            c.setFillColor(INK);c.setFont('Serif',9)
            for i,line in enumerate(sub.split('|')):c.drawCentredString(x+w/2,y+hh-37-i*12,line)
        def arrow(x,y,xx,yy):
            c.setStrokeColor(BROWN);c.setFillColor(BROWN);c.setLineWidth(1);c.line(x,y,xx,yy)
            angle=math.atan2(yy-y,xx-x);path=c.beginPath();path.moveTo(xx,yy)
            path.lineTo(xx-7*math.cos(angle-.4),yy-7*math.sin(angle-.4));path.lineTo(xx-7*math.cos(angle+.4),yy-7*math.sin(angle+.4));path.close();c.drawPath(path,fill=1,stroke=0)
        if self.kind=='architecture':
            box(0,220,145,65,'Sources','Simulateur / saisie / CSV');box(170,220,145,65,'Prétraitement','Validation + historique');box(340,220,143,65,'Modèle local','Imputation + forêt')
            arrow(145,252,170,252);arrow(315,252,340,252)
            box(0,105,145,75,'Stockage local','data/*.csv|models/*.joblib');box(170,105,145,75,'Inférence','Score + décision|Percentile historique');box(340,105,143,75,'Évaluation','Test chronologique|Comparaison aux règles')
            arrow(411,220,411,180);arrow(315,142,340,142);arrow(242,220,242,180);arrow(72,220,72,180)
            box(100,0,283,65,'Dashboard Streamlit','Explorer · évaluer · vérifier · simuler');arrow(242,105,242,65)
        elif self.kind=='pipeline':
            labels=[('1. Événements chronologiques','12 000 lignes · caractéristiques causales'),('2. Découpage temporel','9 000 train / 3 000 test'),('3. Apprentissage sur le train','Médianes + 200 arbres · graine 42'),('4. Sauvegarde et rechargement','Pipeline Joblib + scores de référence'),('5. Inférence sur le test','Décision et score continu'),('6. Mesures et comparaison','Étiquettes utilisées seulement ici')]
            for i,(a,b) in enumerate(labels):
                y=300-i*59;box(80,y,323,48,a,b)
                if i<5:arrow(241,y,241,y-11)
        elif self.kind=='history':
            c.setFont('Serif-Bold',12);c.setFillColor(BROWN);c.drawString(10,195,'Événement à évaluer : t = 10 h 11')
            c.setFillColor(LIGHT);c.roundRect(75,60,330,95,6,fill=1,stroke=0)
            c.setFont('Serif',10);c.setFillColor(BROWN);c.drawCentredString(240,130,'Fenêtre de contexte : [10 h 01, 10 h 11[');arrow(20,85,465,85)
            for x,t,label,inside in [(35,'10:00','Échec exclu',False),(180,'10:05','Échec inclus',True),(330,'10:10','Succès inclus',True),(435,'10:11','Événement courant',False)]:
                c.setFillColor(BROWN if inside else GOLD);c.circle(x,85,5,fill=1,stroke=0);c.setFont('Serif-Bold',10);c.drawCentredString(x,60,t);c.setFont('Serif',9);c.drawCentredString(x,42,label)
            c.setFillColor(INK);c.setFont('Serif',11);c.drawCentredString(CW/2,10,'attempts_10min = 2     ·     failed_attempts = 1')
class Compare(Flowable):
    def __init__(self):Flowable.__init__(self);self.width=CW;self.height=210
    def draw(self):
        c=self.canv
        for i,(metric,label) in enumerate([('precision','Précision'),('recall','Rappel'),('f1','F1')]):
            y=160-i*55;c.setFillColor(INK);c.setFont('Serif-Bold',11);c.drawString(0,y+13,label)
            for k,(name,color) in enumerate([('Isolation Forest',BROWN),('Règles',GOLD)]):
                val=M[name][metric];c.setFillColor(color);c.roundRect(95,y-k*17,310*val,11,3,fill=1,stroke=0);c.setFont('Serif',9);c.drawString(100+310*val,y-k*17+2,f'{val:.3f}')
        for x,name,color in [(95,'Isolation Forest',BROWN),(260,'Règles',GOLD)]:
            c.setFillColor(color);c.rect(x,4,8,8,fill=1,stroke=0);c.setFont('Serif',10);c.drawString(x+14,5,name)
# Cover
S.append(Spacer(1,10));S.append(Image(str(ASSETS/'UCA-FSSM.png'),width=CW,height=CW*394/1220));S.append(Spacer(1,23))
cover=ParagraphStyle('cover',fontName='Serif',fontSize=13,leading=19,alignment=TA_CENTER,textColor=INK)
for t in ['Université Cadi Ayyad','Faculté des Sciences Semlalia · Marrakech','<b>Master · Semestre 3</b>','Année universitaire 2026-2027']:S.append(Paragraph(t,cover))
S.append(Spacer(1,29));S.append(Paragraph('RAPPORT DE MINI-PROJET',ParagraphStyle('kicker',parent=cover,fontSize=11,textColor=BROWN)))
S.append(Spacer(1,12));S.append(Paragraph('LoginGuard AI',ParagraphStyle('brand',parent=cover,fontName='Serif-Bold',fontSize=34,leading=42,textColor=BROWN)))
S.append(Paragraph('Détection intelligente des connexions<br/>anormales par Intelligence Artificielle',ParagraphStyle('title',parent=cover,fontName='Serif-Bold',fontSize=21,leading=28)))
S.append(Spacer(1,24));S.append(Paragraph('<b>Module</b><br/>Sécurité des systèmes d’information et l’IA',cover));S.append(Spacer(1,31))
t=Table([[Paragraph('<b>Réalisé par</b><br/>Hajar Laziz<br/>Jihane Hamouchi',cover),Paragraph('<b>Encadré par</b><br/>Pr. Mariya Ouaissa',cover)]],colWidths=[CW/2]*2)
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,0),(-1,0),.6,LINE),('TOPPADDING',(0,0),(-1,-1),16)]));S.append(t)

# CONTENT
page('Résumé')
p('LoginGuard AI étudie la détection des comportements d’authentification inhabituels à partir de journaux entièrement simulés. Le système associe une génération reproductible des événements, des caractéristiques historiques calculées sans observation du futur, un modèle Isolation Forest et un dashboard local de supervision. Le travail s’inscrit dans le module Sécurité des systèmes d’information et l’IA du Master, semestre 3, à la Faculté des Sciences Semlalia.')
p('Le jeu étudié contient <b>12 000 événements et 400 utilisateurs fictifs</b>, sur une période de 60 jours. Les 9 000 premiers événements servent à l’apprentissage et les 3 000 suivants à l’évaluation. Sept variables numériques décrivent l’heure, les échecs récents, la fréquence des tentatives et la nouveauté des adresses IP et des types de terminaux. Les étiquettes des scénarios ne sont jamais fournies au modèle pendant son apprentissage.')
p('Sur le test, Isolation Forest obtient une précision de <b>65,70 %</b>, un rappel de <b>16,83 %</b> et un score F1 de <b>26,80 %</b>. La méthode par règles atteint un F1 de <b>71,99 %</b>. Cette comparaison met en évidence l’effet du seuil de décision et l’adéquation des règles aux motifs du simulateur. Le système recommande une vérification complémentaire ; il ne bloque pas de connexion et ne déploie pas de mécanisme MFA.')
p('L’application réunit la consultation des journaux, les graphiques, les métriques, la saisie d’une connexion, l’import CSV et une simulation interactive. Les contrôles de format, les tests de causalité et les tests d’interface soutiennent la reproductibilité. La validation du 16 novembre 2026 comprend 32 tests réussis et une vérification des dépendances.')
h('Mots-clés');p('Cybersécurité ; authentification ; détection d’anomalies ; Isolation Forest ; historique causal ; Streamlit ; données synthétiques.')
h('Périmètre du document');p('Le rapport décrit la version locale du projet et ses fonctions effectivement implémentées. Les captures proviennent de l’application en fonctionnement ; les tableaux numériques proviennent des CSV et de l’évaluation exécutée pour ce rapport.')
page('Table des matières')
toc=TableOfContents(tableStyle=TableStyle([('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),('LEFTPADDING',(0,0),(-1,-1),0)]));toc.levelStyles=[ParagraphStyle('toc',fontName='Serif',fontSize=10.5,leading=15,spaceBefore=3,textColor=INK)];S.append(toc)
page('1. Contexte et problématique')
h('1.1. L’authentification comme source d’observation')
p('Une connexion ne se résume pas à un résultat de succès ou d’échec. Son horaire, son origine réseau, son terminal et son rapprochement avec les tentatives précédentes fournissent un contexte. Une multiplication rapide des essais, un horaire inhabituel ou une adresse jamais rencontrée peuvent justifier un examen, sans suffire à prouver une compromission.')
p('Dans ce projet, ces signaux sont étudiés sur des données fictives. Ce choix permet de maîtriser les scénarios, de reproduire les expériences et de disposer d’une vérité terrain pour mesurer les erreurs. Il évite également la collecte de mots de passe, d’identités réelles et de trafic réseau.')
h('1.2. Question de recherche')
p('<b>Comment repérer des connexions inhabituelles à partir du contexte disponible au moment de l’événement, sans utiliser les étiquettes d’attaque dans l’apprentissage ?</b> Cette question exige de séparer trois notions : la rareté statistique d’un comportement, la décision prise à un seuil donné et la qualification effective d’une attaque.')
h('1.3. Objectifs opérationnels')
p('Le premier objectif consiste à construire une chaîne cohérente, de la simulation à l’inférence. Le deuxième est de mesurer les performances sur une période ultérieure à celle de l’apprentissage. Le troisième est de rendre les résultats compréhensibles dans un dashboard utilisable en démonstration : un utilisateur doit pouvoir consulter une alerte, examiner son contexte et comprendre la recommandation associée.')
h('1.4. Hypothèses de travail')
p('Les horodatages sont interprétés selon la convention UTC. Les journaux sont complets dans le périmètre simulé. Un identifiant représente un compte fictif et le champ device_type représente une catégorie de terminal, non une empreinte matérielle. La nouveauté d’une IP signifie seulement son absence dans l’historique connu pour ce compte.')
p('Le produit est une aide à l’analyse. L’évaluation d’une connexion et la recommandation de vérification sont implémentées ; l’exécution de la vérification MFA, la gestion d’un compte et l’intégration à un fournisseur d’identité restent hors périmètre.')
page('2. Cahier des charges et parcours')
table(['Besoin','Réalisation'],[['Observer l’activité','Indicateurs calculés, horaires, fréquence, scores et répartition des décisions.'],['Explorer un journal','Filtres de période, compte, statut, IP et terminal ; recherche littérale ; export CSV.'],['Évaluer une connexion','Saisie d’un événement, sélection du passé strictement antérieur, calcul des variables et prédiction.'],['Importer des événements','Validation des six champs bruts, taille limitée, reconstruction du contexte du fichier.'],['Démontrer les scénarios','Génération finie d’événements normaux, suspects ou aléatoires ; historique de session.'],['Mesurer la qualité','Test chronologique, matrice de confusion, métriques, règles de référence et sensibilité au seuil.']],[130,CW-130])
h('2.1. Contraintes de réalisation')
p('L’application doit fonctionner sur un ordinateur courant sous Windows, avec Python 3.11 et un environnement virtuel. Aucun GPU, service payant, base de données externe ni fournisseur d’authentification n’est requis. Les données et l’artefact de modèle restent locaux. Les dépendances directes sont fixées pour limiter les écarts entre installations.')
h('2.2. Parcours utilisateur')
p('Le parcours principal commence dans la vue d’ensemble. L’utilisateur restreint le volume ou les heures affichées dans la barre latérale, explore les événements puis consulte la performance du modèle. Le dernier onglet permet de saisir une connexion, d’importer un journal fictif ou de générer un scénario pour observer les variables de contexte.')
p('Les filtres latéraux s’appliquent à la vue d’ensemble et à l’explorateur. Ils ne réentraînent pas le modèle et ne modifient pas l’évaluation de test. Le filtre de percentile sélectionne des lignes affichées ; il ne remplace pas le seuil de décision de la forêt.')
page('3. Architecture générale')
S.append(Diagram('architecture',300));caption('Architecture fonctionnelle de LoginGuard AI. Les échanges restent locaux.')
p('L’architecture sépare les données brutes, les transformations, l’apprentissage et l’interface. Cette séparation évite que chaque écran reconstruise sa propre logique de prédiction. La saisie manuelle, la simulation et le traitement d’un CSV utilisent les mêmes fonctions de calcul des caractéristiques et le même pipeline sauvegardé.')
h('3.1. Trois niveaux de responsabilité')
p('<b>Données :</b> les CSV conservent les événements et leurs variables historiques. <b>Traitement :</b> les modules de src valident, calculent, entraînent, évaluent et prédisent. <b>Présentation :</b> app.py rassemble les vues dans quatre onglets ; src/ui.py fournit les composants, les filtres et le style des graphiques.')
h('3.2. Persistance et réutilisation')
p('Le fichier Joblib contient le pipeline entraîné, les noms des variables, les paramètres, la fin de la période d’apprentissage et les scores de référence triés. Les ressources Streamlit sont mises en cache avec les dates de modification des fichiers. Les données et le modèle existants sont réutilisés au lancement ; leur absence déclenche la préparation initiale.')
page('4. Organisation du code et outils')
code('''anomaly_login_detection/
  app.py                    # dashboard à quatre onglets
  src/
    generate_data.py        # simulation reproductible
    preprocessing.py        # validation et historique causal
    train_model.py          # apprentissage et sauvegarde
    predict.py              # scores et analyse contextuelle
    evaluate_model.py       # métriques, règles, seuils
    simulation.py           # scénarios interactifs
    ui.py / utils.py        # composants et chemins locaux
    views/                  # vues réutilisables du dashboard
  pages/                    # entrées de compatibilité
  data/                     # CSV complet, train et test
  models/                   # isolation_forest.joblib
  assets/style.css          # identité visuelle
  tests/                    # données, variables, modèle, UI
  notebooks/                # démarche expérimentale
  docs/                     # méthode, résultats, rapport
  requirements.txt / start.ps1 / .streamlit/config.toml''')
table(['Composant','Version','Rôle'],[['Python','3.11','Exécution locale'],['Pandas / NumPy','2.3.3 / 2.2.6','Données et génération aléatoire'],['Scikit-learn','1.7.2','Pipeline, forêt, mesures'],['Streamlit / Plotly','1.50.0 / 6.3.1','Interface et visualisations'],['Joblib / pytest','1.5.2 / 8.4.2','Persistance et tests']],[145,90,CW-235])
p('Les quatre onglets constituent le point d’entrée actuel. Les fichiers pages conservent des accès de compatibilité et des scénarios de test ; ils ne définissent plus cinq destinations dans la navigation principale. Les données générées, les modèles et l’environnement virtuel sont exclus de Git.')
page('5. Construction des données synthétiques')
p('Le générateur utilise NumPy avec la graine 42. Il tire un utilisateur parmi 400 comptes, un jour parmi 60 et une heure centrée sur 10 + (indice utilisateur modulo 6), avec un écart-type de 2,5 heures. Cette construction crée des habitudes différentes selon les comptes sans fournir leur identifiant au modèle.')
p('Une session ordinaire conserve généralement une adresse privée propre au compte. Le terminal est tiré parmi desktop, mobile et tablet avec les probabilités 78 %, 18 % et 4 %. Des exceptions légitimes existent : quelques horaires nocturnes, changements d’adresse, échecs et petites rafales. Les classes se chevauchent donc.')
table(['Scénario','Construction dominante','Événements'],[['Normal','Petites sessions, horaires habituels',8915],['Brute force','5 à 16 tentatives, échec fréquent',983],['Combiné','Nuit, IP documentaire, rafale, terminal unknown',898],['Haute fréquence','5 à 16 tentatives espacées de 25 secondes',886],['Nouveau terminal','Catégorie unknown',111],['IP inhabituelle','Adresse tirée dans 192.0.2.0/24',107],['Connexion nocturne','Heure entre 0 et 6 h',100]],[100,CW-175,75])
h('5.1. Pourquoi 6,5 % ne devient pas 6,5 % des lignes')
p('La probabilité de scénario suspect est 6,5 % au niveau des sessions générées. Certains scénarios produisent cependant beaucoup plus d’événements par session. Leur poids final atteint <b>3 085 / 12 000 = 25,71 %</b> des événements. Il faut distinguer la probabilité de génération d’une session, la prévalence des étiquettes et le taux d’alertes du modèle.')
h('5.2. Qualité du jeu livré')
p('Le journal couvre du 1er janvier au 1er mars 2026. Il comporte 15 colonnes, aucun identifiant d’événement dupliqué et aucune valeur manquante. Les 2 242 échecs d’authentification correspondent au résultat courant des événements ; ils ne doivent pas être confondus avec la somme des compteurs de la fenêtre historique.')
page('6. Dictionnaire des données')
table(['Champ','Type / domaine','Signification'],[['event_id','Texte unique','Identifiant d’événement fictif.'],['user_id','Texte','Compte fictif ; clé de l’historique.'],['timestamp','Date UTC','Instant de l’événement.'],['login_hour','Entier 0 à 23','Heure extraite du timestamp.'],['day_of_week','Entier 0 à 6','Jour de semaine ; lundi = 0.'],['source_ip','IP valide','Adresse source ; privée ou documentaire dans la simulation.'],['ip_changed','0 / 1','Différence avec la dernière IP du compte.'],['new_ip','0 / 1','Adresse absente de toutes les IP connues du compte.'],['failed_attempts','Entier ≥ 0','Échecs antérieurs dans les dix minutes.'],['attempts_10min','Entier ≥ 0','Tentatives antérieures dans les dix minutes.'],['login_success','0 / 1','Issue de la connexion courante.'],['device_type','Texte','Catégorie de terminal.'],['is_new_device','0 / 1','Catégorie absente du passé connu.'],['anomaly_type','Texte','Scénario de génération ; évaluation uniquement.'],['is_anomaly','0 / 1','Étiquette de scénario ; évaluation uniquement.']],[100,105,CW-205])
p('Les champs event_id, user_id, source_ip, anomaly_type et is_anomaly ne sont pas injectés dans la matrice d’apprentissage. login_success alimente les compteurs des événements ultérieurs, mais n’est pas un prédicteur direct de l’événement courant. day_of_week et device_type restent utiles à l’exploration sans être des variables directes de la forêt.')
page('7. Historique causal et fenêtre glissante')
p('Pour chaque compte, le prétraitement maintient la dernière IP, l’ensemble des IP déjà vues, l’ensemble des catégories de terminaux et une file de tentatives récentes. Les événements sont triés par timestamp ; les compteurs d’un événement à l’instant t utilisent exclusivement l’intervalle <b>[t − 10 minutes, t[</b>.')
S.append(Diagram('history',220));caption('Deux tentatives antérieures, dont un échec, dans le contexte de 10 h 11.')
p('Le début de la fenêtre est inclus : une tentative exactement dix minutes auparavant reste présente. L’événement courant est exclu. Les événements de même timestamp sont traités en lot : leurs caractéristiques sont calculées avant de mettre à jour les états. Aucun événement simultané ne voit les autres événements de son lot.')
table(['Instant','Tentatives antérieures','Échecs antérieurs','IP nouvelle'],[['10:00',0,0,1],['10:05',1,1,0],['10:10',2,2,1],['10:11',2,1,0]],[70,140,140,CW-350])
p('Dans cet exemple, les événements de 10 h 00 et 10 h 05 échouent, puis ceux de 10 h 10 et 10 h 11 réussissent. L’IP change à 10 h 10 puis revient à l’adresse initiale. Les valeurs illustrées sont celles vérifiées par le test de fenêtre causale du projet.')
h('Démarrage sans historique')
p('Pour un compte inconnu, les compteurs valent zéro ; new_ip et is_new_device valent un, car rien n’a encore été observé. Cette convention décrit la connaissance disponible et non une certitude de nouveauté réelle. L’interface signale explicitement l’absence de passé.')
page('8. Prétraitement et prévention des fuites')
h('8.1. Validation des entrées')
p('Les six champs bruts obligatoires sont event_id, user_id, timestamp, source_ip, device_type et login_success. Le validateur rejette les champs obligatoires manquants, les identifiants dupliqués, les dates non interprétables, les IP invalides et les issues différentes de 0 ou 1. Les chaînes doivent être non vides et contenir au maximum 128 caractères.')
h('8.2. Encodage cyclique de l’heure')
eq('h<sub>sin</sub> = sin(2πh / 24) &nbsp;&nbsp; ; &nbsp;&nbsp; h<sub>cos</sub> = cos(2πh / 24) &nbsp;&nbsp; (1)')
p('Cet encodage rapproche 23 h de 0 h. Une simple valeur entière traite artificiellement ces heures comme éloignées. Le vecteur final contient, dans un ordre fixé, hour_sin, hour_cos, failed_attempts, attempts_10min, ip_changed, new_ip et is_new_device.')
h('8.3. Imputation réutilisable')
p('Les données brutes obligatoires incomplètes sont rejetées. Pour une matrice numérique déjà construite, les valeurs non interprétables et infinies deviennent des valeurs manquantes. SimpleImputer apprend les médianes sur le train uniquement et les réutilise en prédiction. keep_empty_features préserve le nombre de variables si une colonne entière est manquante. Les indicateurs binaires et les compteurs sont contrôlés.')
h('8.4. Séparation entre passé, modèle et vérité terrain')
p('Les caractéristiques sont calculées dans l’ordre chronologique, puis le journal est séparé à 75 %. Calculer les caractéristiques avant cette coupure n’introduit pas de futur : chaque ligne ne consulte que le passé. Les événements de test bénéficient du contexte antérieur, y compris des observations de test déjà survenues ; les paramètres du modèle restent figés.')
p('Les tests modifient les étiquettes et les identifiants tout en vérifiant que la matrice numérique reste identique. Aucune adresse IP brute n’est convertie en nombre ordinal. Une normalisation StandardScaler n’est pas utilisée dans ce pipeline : les arbres effectuent des partitions sur les variables numériques préparées.')
page('9. Isolation Forest : principe et scores')
p('Isolation Forest recherche les observations qui s’isolent rapidement sous des partitions aléatoires. Un arbre choisit une variable et un seuil ; une forêt agrège la longueur des chemins obtenus. Une observation atypique tend à nécessiter moins de séparations. L’algorithme est adapté ici à un apprentissage sans étiquettes d’attaque [1, 2].')
eq('s(x, n) = 2<super>− E[h(x)] / c(n)</super> &nbsp;&nbsp; (2)')
eq('c(n) = 2 H<sub>n−1</sub> − 2(n − 1)/n &nbsp;&nbsp; (3)')
p('Dans cette intuition théorique, h(x) est la longueur du chemin, E[h(x)] sa moyenne dans la forêt et H la somme harmonique. Le score original augmente lorsque l’isolement est rapide. Il ne doit pas être confondu avec les conventions de signe des méthodes exposées par Scikit-learn.')
table(['Sortie','Interprétation dans le projet'],[['predict(X)','+1 : inlier ; −1 : outlier.'],['decision_function(X)','Valeur négative : connexion classée atypique.'],['anomaly_score','Opposé de decision_function ; positif : suspect.'],['prediction','0 : normal ; 1 : suspect.'],['relative_percentile','Rang du score parmi les scores d’apprentissage triés, de 0 à 100.']],[145,CW-145])
eq('A(x) = − decision_function(x) ; ŷ = 1 si A(x) &gt; 0 &nbsp; (4)')
p('La contamination fixe l’offset utilisé pour la décision ; elle ne garantit pas le taux d’alertes d’une période future. Le percentile historique compte les scores d’apprentissage inférieurs ou égaux au score évalué. Un percentile de 94,4 signifie un rang élevé dans cette référence, pas 94,4 % de probabilité d’attaque.')
h('Lecture d’une alerte')
p('Les facteurs affichés sont des règles descriptives : au moins trois échecs, six tentatives, horaire avant 6 h, IP ou catégorie de terminal inconnue. Ils fournissent des pistes d’examen, mais ne sont ni des valeurs SHAP ni une explication causale de la décision.')
page('10. Pipeline d’apprentissage et persistance')
S.append(Diagram('pipeline',360));caption('Apprentissage sur le passé et évaluation sur la période suivante.')
table(['Paramètre','Valeur'],[['n_estimators / max_samples','200 arbres / 256 événements'],['contamination / random_state','0,08 / 42'],['n_jobs','1'],['Prétraitement intégré','SimpleImputer, stratégie médiane'],['Période train','1er janvier → 15 février 2026 à 10:12:06'],['Période test','15 février à 10:12:31 → 1er mars 2026']],[205,CW-205])
p('Le train contient 6 723 événements ordinaires et 2 277 événements de scénarios suspects. Il est majoritairement normal, mais significativement contaminé. Aucun filtrage par vérité terrain n’est effectué. Le pipeline entier est sauvegardé pour préserver le traitement entre entraînement et inférence.')
page('11. Protocole d’évaluation')
p('L’évaluation utilise les 3 000 événements les plus récents, comprenant 2 192 événements normaux et 808 événements suspects selon les scénarios. Les mêmes lignes et les mêmes étiquettes servent à la forêt et à la méthode de référence. Le modèle n’est pas réentraîné dans l’onglet Performance.')
h('11.1. Règles de référence')
eq('Alerte = (échecs ≥ 3) OU (tentatives ≥ 6)<br/>OU (nouvelle IP ET heure &lt; 6) &nbsp;&nbsp; (5)')
p('Ces règles utilisent les caractéristiques déjà calculées. Elles constituent une baseline simple et explicable. Leur performance est influencée par le fait que les scénarios simulés reposent eux-mêmes sur des rafales, des échecs et des horaires inhabituels.')
h('11.2. Mesures retenues')
eq('Précision = TP / (TP + FP) ; Rappel = TP / (TP + FN) &nbsp; (6)')
eq('F1 = 2 × Précision × Rappel / (Précision + Rappel) &nbsp; (7)')
eq('Exactitude = (TP + TN) / N ; FPR = FP / (FP + TN) &nbsp; (8)')
p('TP désigne les scénarios suspects détectés, FP les événements ordinaires signalés, FN les scénarios suspects manqués et TN les événements ordinaires non signalés. La précision mesure la qualité des alertes ; le rappel mesure la couverture. L’exactitude est insuffisante lorsque la classe majoritaire domine.')
h('11.3. Scores continus')
p('ROC-AUC, Average Precision et PR-AUC sont calculées lorsque les deux classes existent et qu’un score continu est disponible. L’Average Precision additionne les précisions pondérées par les gains de rappel. La PR-AUC trapézoïdale utilise une interpolation différente ; les deux valeurs sont donc rapportées séparément [3].')
p('Aucun score continu spécifique n’est défini pour les règles binaires : le rapport ne leur attribue pas artificiellement une courbe de classement. La comparaison principale porte sur précision, rappel, F1 et taux de faux positifs.')
page('12. Résultats expérimentaux')
table(['Méthode','Précision','Rappel','F1','Exactitude'],[[name,*[f'{M[name][k]*100:.2f} %' for k in ['precision','recall','f1','accuracy']]] for name in ['Isolation Forest','Règles']],[119,91,91,91,CW-392])
S.append(Compare());caption('Comparaison calculée sur les mêmes 3 000 événements de test.')
table(['Méthode','TN','FP','FN','TP','Taux FP'],[[name,*[M[name]['confusion_matrix'][i][j] for i,j in [(0,0),(0,1),(1,0),(1,1)]],f"{M[name]['false_positive_rate']*100:.4f} %"] for name in ['Isolation Forest','Règles']],[124,54,54,54,54,CW-340])
p('La forêt émet 207 alertes sur le test : 136 correspondent à un scénario suspect et 71 à un événement ordinaire. Elle manque 672 scénarios suspects. Les règles émettent 456 alertes, dont 455 correspondent à un scénario suspect. Leur rappel reste néanmoins incomplet : 353 événements suspects ne déclenchent aucune règle.')
p('<b>ROC-AUC = 0,8714 ; Average Precision = 0,6604 ; PR-AUC trapézoïdale = 0,6609.</b> Le classement est plus informatif que ne le laisse penser le rappel au seuil retenu. Ce constat ne transforme toutefois pas un événement manqué en événement détecté : les résultats binaires restent ceux du seuil 8 %.')
p('Les 913 alertes visibles sur les 12 000 événements du dashboard, soit 7,61 %, comprennent le train et le test. Elles ne sont pas les 3 085 étiquettes suspectes du simulateur. L’interface générale sert à l’exploration ; seule la période de test sert aux métriques indépendantes.')
page('13. Sensibilité au seuil et interprétation')
table(['Contamination','Précision','Rappel','F1','FP','FN'],[[f"{r['contamination']:.0%}",f"{r['precision']:.3f}",f"{r['recall']:.3f}",f"{r['f1']:.3f}",r['false_positives'],r['false_negatives']] for r in F['sensitivity']],[100,85,75,75,70,CW-405])
p('Cette expérimentation conserve les arbres et fait varier l’offset. Les seuils sont obtenus à partir des percentiles de score_samples sur l’apprentissage. Le test sert uniquement à décrire les conséquences de ces seuils, et non à sélectionner un réglage final.')
h('13.1. Effet observé')
p('Entre 3 % et 18 %, le rappel augmente de 7,18 % à 35,52 %, tandis que les fausses alertes passent de 17 à 113. Le F1 passe de 0,131 à 0,475. La précision n’évolue pas de manière monotone : les classes se recouvrent et la composition des événements ajoutés aux alertes varie selon le seuil.')
h('13.2. Pourquoi le rappel reste faible')
p('Le taux d’événements étiquetés suspects atteint 25,30 % dans le train et 26,93 % dans le test, alors que le seuil est fixé à 8 %. Ce décalage contribue à une décision conservatrice. Il n’explique pas tout : une première tentative d’une rafale peut ne présenter aucun compteur élevé ; un événement associé à un scénario suspect peut aussi conserver des caractéristiques ordinaires.')
h('13.3. Le rôle de la baseline')
p('Le résultat des règles ne doit pas être masqué. Elles correspondent bien aux motifs explicites du générateur et atteignent une meilleure couverture. La forêt reste utile pour étudier la rareté multivariée et la différence entre score et seuil, mais cette expérience ne démontre pas sa supériorité sur des règles.')
h('13.4. Protocole futur recommandé')
p('Une évolution rigoureuse utiliserait trois périodes : apprentissage, validation et test final. Le choix du seuil et du budget de fausses alertes serait effectué sur la validation, puis gelé avant le test. Un découpage par sessions et une zone tampon temporelle permettraient également d’étudier l’effet des rafales traversant la frontière entre les périodes.')
page('14. Interface : vue d’ensemble')
screenshot('01-accueil.jpg','Accueil réel du dashboard, indicateurs globaux et barre de réglages.')
p('L’interface réunit les fonctions dans un seul écran à quatre onglets. Le fond beige, la navigation brun foncé et les accents caramel constituent une identité cohérente. Les titres et les valeurs des cartes sont hiérarchisés ; les contenus explicatifs restent séparés des résultats calculés. La police de l’application est Inter lorsqu’elle est disponible, avec un repli vers Segoe UI.')
h('14.1. Indicateurs et périmètre')
p('Sans filtre, la vue présente 12 000 événements, 11 087 prédictions normales, 913 prédictions suspectes, un taux suspect arrondi à 7,6 %, 400 comptes et 2 242 échecs d’authentification. Ces valeurs décrivent le jeu affiché, et non une surveillance de trafic réel en cours.')
h('14.2. Barre latérale')
p('Le nombre de connexions sélectionne les événements les plus récents. Le curseur d’heures restreint la plage horaire et le percentile minimum filtre le rang des scores. Ces réglages sont cumulatifs avec les filtres locaux. Le modèle reste Isolation Forest ; le champ correspondant indique le modèle implémenté, sans proposer des algorithmes non disponibles.')
p('Les indicateurs et graphiques de la vue d’ensemble sont reconstruits sur la même sélection. Une sélection vide produit un message explicite au lieu d’un tableau incohérent. La performance et la simulation restent indépendantes des filtres d’affichage.')
page('15. Interface : graphiques et activité')
screenshot('02-graphiques.jpg','Répartition horaire, fréquence, activité quotidienne, scores et décisions.')
p('Le graphique horaire rapproche le volume de connexions et le statut prédit. Le nuage de points relie le nombre de tentatives aux échecs récents ; le symbole distingue la nouveauté IP. Pour conserver une interaction fluide, le nuage affiche au plus 2 000 événements sélectionnés avec une graine fixe, tandis que les autres agrégats utilisent toute la sélection.')
h('15.1. Lecture des scores')
p('L’histogramme positionne les scores par rapport à la limite zéro. Les valeurs positives correspondent aux décisions suspectes. Le diagramme en anneau exprime la part de ces décisions dans les données affichées. La courbe quotidienne montre la concentration de l’activité et la différence de volume entre les deux statuts.')
h('15.2. Choix visuels')
p('Les graphiques Plotly associent des remplissages clairs, des contours plus foncés et des légendes. Les survols permettent de lire les valeurs ; les titres indiquent la mesure représentée. Les barres, courbes et points ne sont pas interchangeables : chacun correspond respectivement à une distribution, une évolution ou une relation entre variables.')
p('Une projection à deux dimensions ne résume pas les sept variables. Les graphiques aident à examiner les alertes, sans établir de causalité ni remplacer la décision du modèle.')
page('16. Interface : exploration des journaux')
screenshot('03-explorateur.jpg','Recherche du compte fictif USR-0001 : 57 événements retrouvés.')
p('L’explorateur fournit une recherche littérale dans event_id, user_id et source_ip. Il n’interprète pas la saisie comme une expression régulière. L’exemple montre les 57 événements du compte USR-0001. Le tableau conserve les horodatages et les informations nécessaires pour suivre la chronologie du compte.')
h('16.1. Filtrage et export')
p('Les filtres locaux portent sur la période, les utilisateurs, le statut prédit, la nouveauté IP et le type de terminal. Ils se combinent aux réglages latéraux. Le bouton Exporter CSV produit le sous-ensemble affiché, avec un encodage UTF-8 comportant une marque BOM pour faciliter l’ouverture dans les tableurs.')
h('16.2. Compréhension des colonnes')
p('Les libellés du dashboard sont traduits pour la lecture, alors que les noms techniques restent stables dans les données. Les champs de vérité terrain décrivent le simulateur ; ils ne remplacent pas les colonnes de prédiction. Le tableau peut être parcouru horizontalement pour examiner l’ensemble des caractéristiques.')
p('L’export neutralise les préfixes susceptibles d’être interprétés comme des formules par un tableur. Cette mesure protège la consultation des chaînes exportées ; elle ne transforme pas le CSV en source de confiance pour un autre système.')
page('17. Interface : performance du modèle')
screenshot('04-performance.jpg','Métriques et matrice de confusion sur les 3 000 événements de test.')
p('L’onglet Performance sépare l’évaluation de l’exploration générale. Les quatre cartes présentent précision, rappel, F1 et exactitude. La matrice expose les comptes de chaque combinaison réel/prédit : 2 121 vrais négatifs, 71 faux positifs, 672 faux négatifs et 136 vrais positifs.')
h('17.1. Comparaison explicite')
p('Le graphique voisin compare la forêt et les règles sur le même test. Le tableau de métriques complète la lecture avec le taux de fausses alertes et les erreurs absolues. Les scores continus et la distribution par vérité terrain permettent ensuite d’examiner la séparation entre classes sans confondre cet examen avec un réentraînement.')
h('17.2. Configuration expérimentale')
p('Un panneau dépliable affiche la sensibilité à la contamination et les paramètres de l’artefact : nombre d’arbres, taille de l’apprentissage, date de fin et noms des variables. Les filtres du dashboard ne changent ni les 3 000 événements de cette évaluation ni les paramètres utilisés.')
p('La matrice rend visible la principale limite de l’expérience : les faux négatifs sont nombreux. Présenter seulement l’exactitude de 75,23 % ferait perdre cette information. La lecture conjointe du rappel, de la précision et des effectifs fournit une conclusion plus utile pour la cybersécurité.')
page('18. Interface : analyse d’une connexion')
screenshot('05-manuel.jpg','Évaluation réelle d’une saisie avec 57 événements antérieurs disponibles.')
p('Le formulaire demande l’utilisateur, l’IP, la date, l’heure, le type de terminal et l’issue de l’authentification. assess_event conserve seulement les événements du même compte dont le timestamp est strictement antérieur à la saisie. Il reconstruit les caractéristiques, puis applique le pipeline local chargé.')
h('18.1. Résultat observé')
p('Dans la capture, le compte USR-0001 est évalué le 2 mars 2026 à 14 h, depuis 192.0.2.42 et un terminal desktop. Le modèle produit un score arrondi à 0,0137, un percentile historique de 94,4 et une décision suspecte. L’horaire est ordinaire, mais il ne suffit pas à rendre toutes les autres dimensions habituelles.')
h('18.2. Interprétation et erreurs de saisie')
p('Le score positif justifie la recommandation de vérification selon le seuil choisi. Le percentile n’est pas une probabilité. Le message indique une différence par rapport aux habitudes statistiques ; il ne certifie pas une attaque. Les facteurs simples affichés servent à orienter l’examen du contexte.')
p('Une IP invalide ou un champ obligatoire incorrect déclenche un message de validation. Lorsqu’aucun historique n’existe, l’interface le précise. Le formulaire n’authentifie pas réellement un compte et ne transmet pas de code MFA.')
page('19. Interface : import d’un CSV')
screenshot('06-import.jpg','Zone d’import et rappel des six champs bruts obligatoires.')
p('L’import permet d’évaluer un journal fictif externe au jeu local. Les variables fournies dans le fichier ne sont pas acceptées comme un contexte déjà fiable : engineer_history reconstruit les compteurs et la nouveauté à partir des événements bruts, dans leur ordre temporel.')
h('19.1. Contrat de données')
code('event_id,user_id,timestamp,source_ip,device_type,login_success\nEX-1,USR-DEMO,2026-03-02 10:00:00,192.0.2.10,desktop,0\nEX-2,USR-DEMO,2026-03-02 10:02:00,192.0.2.10,desktop,1')
p('L’import accepte entre 1 et 100 000 lignes et au plus 10 Mo. Les six colonnes doivent être présentes et valides. Les exceptions de lecture, d’encodage et de validation sont présentées comme des erreurs compréhensibles. Le contenu du CSV n’est jamais exécuté comme du code.')
h('19.2. Limite du contexte')
p('L’historique du fichier n’est pas fusionné avec le jeu local. La première apparition d’un compte, d’une IP ou d’un terminal est donc évaluée relativement au seul fichier. Cette propriété doit être connue avant de comparer les scores d’un import avec ceux du journal complet.')
page('20. Interface : historique évalué')
screenshot('07-historique.jpg','Historique trié par score décroissant, avec rappel du périmètre.')
p('Cet écran donne accès aux événements déjà évalués et les trie par score décroissant. Les premières lignes correspondent aux observations les plus atypiques selon le modèle. Il reste possible d’exporter ces résultats pour une analyse complémentaire.')
h('20.1. Classement et étiquettes')
p('Les scénarios combinés figurent parmi les observations fortement notées, mais un événement étiqueté normal peut également apparaître en tête. Ce comportement est cohérent avec une méthode de rareté : les exceptions légitimes sont parfois atypiques. Le classement permet de discuter les faux positifs plutôt que de les dissimuler.')
h('20.2. Deux périmètres distincts')
p('L’historique évalué contient l’apprentissage et le test. Il répond au besoin d’exploration de toute la base. La mesure de généralisation provient, elle, exclusivement de l’onglet Performance. Réutiliser toutes les lignes de cet écran comme test introduirait une évaluation en partie sur les données d’apprentissage.')
p('La présence simultanée des étiquettes du simulateur et des résultats est utile pour la démonstration universitaire. Dans un véritable système de supervision, une telle vérité terrain complète ne serait généralement pas disponible au moment de l’alerte.')
page('21. Interface : simulation interactive')
screenshot('08-simulation.jpg','Scénario suspect exécuté : neuf échecs précédents et score positif.')
p('La simulation produit un événement à chaque clic, sans boucle infinie ni processus continu. Les actions disponibles sont Connexion normale, Connexion suspecte, Scénario aléatoire et Réinitialiser. Les événements générés sont conservés dans l’état de session, sans réécrire le jeu d’apprentissage.')
h('21.1. Construction du contexte suspect')
p('Le scénario suspect ajoute neuf échecs synthétiques espacés de 30 secondes avant une connexion à 2 h. Il utilise une adresse de documentation et la catégorie unknown. L’événement final est évalué par le modèle, sans forcer sa décision. La capture montre le compte USR-0338, neuf tentatives antérieures, neuf échecs et un score arrondi à 0,0190.')
h('21.2. Pourquoi l’IP peut être indiquée comme connue')
p('L’adresse apparaît déjà dans les neuf échecs ajoutés au contexte. Au moment de la dixième connexion, new_ip vaut donc zéro. Il s’agit d’un effet attendu de la définition historique, et non d’une incohérence : l’IP était nouvelle à sa première apparition, puis elle est devenue connue dans ce contexte.')
p('La réinitialisation efface seulement les événements de simulation de la session. La recommandation MFA reste un texte d’aide à la décision. Aucun service de connexion réel n’est contacté et aucune identité réelle n’est utilisée.')
page('22. Sécurité et qualité logicielle')
table(['Risque ou contrainte','Mesure mise en œuvre'],[['Données sensibles','Simulation de comptes, absence de mots de passe et de trafic réel.'],['Fichier trop volumineux','Limite de 10 Mo et plafond de 100 000 lignes.'],['Entrées mal formées','Contrôle des champs, dates, adresses, doublons et domaines binaires.'],['Exécution via CSV','Lecture comme données, jamais comme instructions ou code.'],['Formules à l’export','Préfixes dangereux neutralisés dans les chaînes.'],['Modèle non fiable','Aucun import de modèle utilisateur ; chargement du Joblib local de confiance.'],['Incohérence de traitement','Fonctions communes et pipeline sauvegardé complet.'],['Fuite de variables cibles','Liste explicite des sept variables ; tests d’invariance aux labels.']],[155,CW-155])
h('22.1. Portabilité et maintenance')
p('Les chemins sont construits avec pathlib depuis la racine du projet. La logique métier est regroupée dans des fonctions courtes. Les vues réutilisent les services communs au lieu de dupliquer l’apprentissage. Les erreurs attendues de saisie sont interceptées et affichées ; les tests restent capables de révéler les erreurs de programmation.')
h('22.2. Frontière de confiance')
p('Joblib repose sur une désérialisation qui exige un fichier fiable. Le projet charge son artefact local, mais ne garantit pas son intégrité face à un attaquant ayant accès au disque. Une utilisation opérationnelle demanderait des contrôles d’accès, une vérification d’intégrité, une politique de journalisation et une gestion du cycle de vie des modèles.')
p('Le serveur de démonstration écoute sur l’adresse locale. La télémétrie Streamlit est désactivée dans la configuration. L’installation des dépendances peut nécessiter Internet ; le fonctionnement métier ne dépend ensuite d’aucun service distant.')
page('23. Tests et validation reproductible')
p('La validation du 16 novembre 2026 a exécuté <b>32 tests pytest, tous réussis</b>. Le contrôle pip check n’a signalé aucune dépendance incompatible. Le notebook explicatif a été exécuté : ses 11 cellules de code se terminent sans erreur. Ces contrôles établissent la cohérence de l’implémentation, pas une efficacité de sécurité sur un réseau réel.')
table(['Groupe','Vérifications couvertes'],[['Données','Graine reproductible, schéma, plages, ordre temporel, présence des scénarios.'],['Historique','Borne des dix minutes, exclusion du courant, événements simultanés, comptes inconnus.'],['Variables','Heure cyclique, valeurs manquantes, invariance aux labels.'],['Import et export','CSV valides, champs absents, doublons, IP/dates invalides, taille, formules.'],['Modèle','Entraînement, sauvegarde, rechargement et prédictions identiques.'],['Inférence','Sorties 0/1, scores, percentiles, passé strict, scénarios.'],['Interface','Vues, filtres vides, recherche, formulaire, simulation et reset.'],['Barre latérale','Limite de 500 événements et filtre de percentile jusqu’au cas vide.']],[110,CW-110])
h('23.1. Contrôles effectués dans le navigateur')
p('Les quatre onglets ont été parcourus sur le serveur local pour produire les captures. La recherche a retourné les événements du compte choisi, le formulaire a fourni une décision et la simulation a construit son contexte. Les visualisations présentées sont des captures du rendu effectif, non des maquettes.')
h('23.2. Portée des tests')
p('Les tests couvrent les cas attendus et plusieurs entrées invalides. Ils ne constituent ni un audit exhaustif de sécurité ni un test de charge. La version exécutée est Python 3.11 sous Windows ; les autres systèmes, la concurrence multiutilisateur et les grands volumes restent à valider séparément.')
page('24. Installation et démonstration')
h('24.1. Préparation sous Windows / VS Code')
p('Ouvrir le dossier du projet dans VS Code puis un terminal PowerShell. Les commandes suivantes utilisent directement l’interpréteur du venv ; il n’est pas nécessaire d’activer l’environnement ni de modifier la politique d’exécution PowerShell.')
code(r'''py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.generate_data
.\.venv\Scripts\python.exe -m src.train_model
.\.venv\Scripts\python.exe -m src.evaluate_model
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
''')
p('Par défaut, ouvrir http://localhost:8501. Les captures du rapport utilisent le même programme avec le port 8503. Arrêter le serveur avec Ctrl+C. Si les données et le modèle existent déjà, le lancement du dashboard les réutilise.')
h('24.2. Reconstruction volontaire')
p('L’option --force de src.generate_data régénère les CSV. Après une régénération, réentraîner puis réévaluer le modèle pour maintenir la cohérence entre données et artefact. Le script start.ps1 automatise la préparation ; les commandes directes restent l’alternative lorsque les scripts PowerShell ne sont pas autorisés.')
h('24.3. Démonstration de soutenance')
table(['Durée','Démonstration'],[['1 minute','Présenter les données fictives et distinguer labels et alertes.'],['2 minutes','Observer les graphiques, filtrer puis rechercher USR-0001.'],['2 minutes','Saisir une connexion et commenter score, percentile et contexte.'],['1 minute','Générer une connexion suspecte ; expliquer les neuf échecs.'],['2 minutes','Lire la matrice et comparer la forêt aux règles ; conclure sur les limites.']],[80,CW-80])
page('25. Discussion, limites et perspectives')
h('25.1. Représentativité des données')
p('Le simulateur simplifie les réseaux, les habitudes et les attaques. Ses scénarios ne couvrent pas les vols de session, les déplacements géographiques, les proxys, les authentifications fédérées ou les changements d’équipe. Les résultats quantifient le comportement sur ce générateur précis, pas sur toutes les connexions possibles.')
h('25.2. Dépendances entre événements')
p('Les rafales contiennent des événements proches et corrélés. Le découpage chronologique évite une répartition aléatoire du passé et du futur, mais une rafale peut traverser la coupure train/test. Une évaluation par sessions et avec intervalle tampon serait plus exigeante. Les événements ne sont donc pas assimilables à des observations indépendantes.')
h('25.3. Contexte et dérive')
p('La nouveauté IP dépend du passé disponible. Un compte inconnu et une fenêtre importée courte peuvent produire davantage de signaux de nouveauté. Le modèle n’utilise pas de profil horaire appris par utilisateur, malgré les profils du générateur. L’évolution des horaires, des terminaux et des réseaux nécessiterait un suivi de dérive et une stratégie de réentraînement.')
h('25.4. Seuil et coût des erreurs')
p('Le seuil actuel privilégie un nombre limité d’alertes, au prix d’un rappel faible. En exploitation, le coût d’une anomalie manquée et celui d’une fausse alerte doivent être définis avec les responsables du système. Un percentile historique n’est pas une calibration de risque ; il ne justifie pas seul un blocage automatique.')
h('25.5. Améliorations proposées')
p('Les priorités sont une validation temporelle dédiée au choix du seuil, des jeux de simulation plus variés, une comparaison à d’autres approches et des profils individuels. Une étape ultérieure pourrait intégrer un mécanisme de vérification complémentaire dans un environnement de test autorisé. Cette intégration devrait inclure contrôle d’accès, journalisation et protection des données avant toute utilisation réelle.')
page('26. Conclusion générale')
p('LoginGuard AI constitue une chaîne locale complète pour étudier la détection de connexions inhabituelles. Le projet relie des journaux fictifs, des variables historiques causales, un pipeline d’apprentissage sauvegardé, une évaluation chronologique et une interface de démonstration. La réutilisation des mêmes fonctions entre notebook, tests et dashboard assure la cohérence du traitement.')
p('L’expérience montre qu’un modèle non supervisé ne doit pas être jugé sur son seul statut de méthode d’intelligence artificielle. Au seuil choisi, Isolation Forest détecte une fraction limitée des scénarios suspects et reste moins performant que les règles de référence en F1. Le score continu apporte une information de classement, mais la décision de sécurité dépend du seuil et du contexte.')
p('L’intérêt du travail réside aussi dans la rigueur des distinctions : événement courant et passé, vérité terrain et prédiction, score et probabilité, recommandation et action effective. Ces distinctions rendent le dashboard explicable et les limites vérifiables pendant une soutenance.')
h('Bilan des réalisations')
table(['Livrable','État vérifié'],[['Jeu synthétique','12 000 événements, 400 comptes, six scénarios suspects.'],['Prétraitement','Sept variables et historique causal testés.'],['Modèle local','Isolation Forest persisté et rechargé.'],['Évaluation','3 000 événements de test ; comparaison aux règles.'],['Dashboard','Quatre onglets, import, export, saisie et simulation.'],['Validation','32 tests réussis ; notebook exécuté.'],['Documentation','Méthode, rapport, installation et guide de présentation.']],[135,CW-135])
p('Le prolongement naturel est de rendre l’évaluation plus représentative et le choix du seuil plus rigoureux. Le prototype fournit une base pédagogique compréhensible pour cette évolution, sans prétendre remplacer un dispositif de sécurité opérationnel.')
page('Références bibliographiques')
refs=[
('1','Liu, F. T., Ting, K. M. et Zhou, Z.-H. (2008). Isolation Forest. Eighth IEEE International Conference on Data Mining (ICDM). Référence originale de l’algorithme, répertoriée dans la documentation officielle Scikit-learn.'),
('2','Scikit-learn 1.7.2. IsolationForest : paramètres, score_samples, decision_function et predict. Documentation officielle.'),
('3','Scikit-learn 1.7.2. average_precision_score : définition de l’Average Precision et différence avec l’intégration trapézoïdale.'),
('4','Streamlit. st.testing.v1.AppTest : interface de test des applications Streamlit. Documentation officielle.'),
('5','LoginGuard AI. Code source du projet, modules src, tests, CSV locaux et artefact d’apprentissage. Version analysée pour ce rapport le 16 novembre 2026.')]
for n,t in refs:p(f'<b>[{n}]</b> {t}')
for label,url in [('Isolation Forest','https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html'),('Average Precision','https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html'),('AppTest','https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest'),('Dépôt du projet','https://github.com/HajarLaziz/SentinelAI-Login-Anomaly-Detection')]:
    S.append(Paragraph(f'<b>{label}</b><br/><link href="{url}" color="#795437">{url}</link>',styles['small']));S.append(Spacer(1,9))
p('Documentation en ligne consultée le 16 novembre 2026. Les versions techniques exécutées sont celles du fichier requirements.txt ; la documentation Streamlit en ligne peut présenter une version plus récente.')
h('Provenance des illustrations et résultats')
p('Le logo institutionnel UCA-FSSM est celui fourni pour la couverture. Les huit captures d’écran ont été réalisées sur le serveur local du projet. Les schémas d’architecture, de fenêtre temporelle et de pipeline synthétisent le code. Les métriques proviennent de l’exécution de src.evaluate_model ; les distributions proviennent des CSV générés avec la graine 42.')
# The source remains editable; report generation is independent of the application.
doc=Report(str(OUT/'Rapport_LoginGuard_AI_FSSM_2026_2027.pdf'),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=62,bottomMargin=58,title='LoginGuard AI - Détection intelligente des connexions anormales',author='Hajar Laziz ; Jihane Hamouchi',subject='Master S3 - FSSM - Sécurité des systèmes d’information et l’IA',pageCompression=1)
doc.addPageTemplates(PageTemplate(id='academic',frames=[Frame(56,58,CW,H-120,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=footer))
doc.multiBuild(S)
print(OUT/'Rapport_LoginGuard_AI_FSSM_2026_2027.pdf')
