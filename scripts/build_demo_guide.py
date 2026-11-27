"""Generate the French oral demonstration cue sheet."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf/Guide_demonstration_LoginGuard_AI.pdf'
pdfmetrics.registerFont(TTFont('Body', 'C:/Windows/Fonts/calibri.ttf'))
pdfmetrics.registerFont(TTFont('Bold', 'C:/Windows/Fonts/calibrib.ttf'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
styles = {
    'title': ParagraphStyle('title',fontName='Bold',fontSize=25,leading=29,textColor=HexColor('#38271e'),spaceAfter=12),
    'sub': ParagraphStyle('sub',fontName='Body',fontSize=12,leading=17,textColor=HexColor('#786250'),spaceAfter=22),
    'heading': ParagraphStyle('heading',fontName='Bold',fontSize=17,leading=22,textColor=HexColor('#795334'),spaceBefore=14,spaceAfter=12),
    'label': ParagraphStyle('label',fontName='Bold',fontSize=11,leading=15,textColor=HexColor('#795334'),spaceBefore=10,spaceAfter=5),
    'body': ParagraphStyle('body',fontName='Body',fontSize=12,leading=18,textColor=HexColor('#302a26'),spaceAfter=9),
    'quote': ParagraphStyle('quote',fontName='Body',fontSize=13,leading=19,textColor=HexColor('#302a26'),backColor=HexColor('#f4ede3'),borderPadding=12,spaceBefore=9,spaceAfter=18),
}
story=[]
def p(text,style='body'):story.append(Paragraph(text,styles[style]))
def step(title,action,speech,goal):
    p(title,'heading');p('À montrer','label');p(action)
    p('À dire','label');p('« '+speech+' »','quote')
    p('<b>But du test :</b> '+goal)

p('LoginGuard AI','title')
p('Guide de démonstration orale • 5 à 7 minutes<br/>Étapes 1 et 2 : présenter le système et explorer la vue d’ensemble.','sub')
step('1. Présenter l’objectif',
     'Ouvrir l’application et sélectionner <b>Rareté contextuelle</b>.',
     'Notre projet analyse des journaux d’authentification pour repérer les connexions inhabituelles qui méritent une vérification. Nous utilisons des données réelles anonymisées du laboratoire LANL. Une alerte ne signifie pas automatiquement qu’une attaque est confirmée.',
     'Situer le rôle du système et la nature des données.')
step('2. Tester la vue d’ensemble',
     'Présenter les indicateurs et les graphiques. Modifier le nombre de connexions affichées, puis filtrer un compte.',
     'Le modèle apprend les relations habituelles entre les comptes et les machines. Une relation rarement observée reçoit un score plus élevé. Les filtres permettent d’examiner une partie des connexions ; ils ne réentraînent pas le modèle.',
     'Vérifier que les indicateurs et les tableaux suivent les filtres.')
p('<b>À retenir :</b> le dataset complet contient 243 247 événements. Pour le modèle contextuel, J+0 sert de référence ; seuls J+1 et J+2 sont affichés parmi les événements analysés. Les identifiants de machines ne sont pas des adresses IP.')
story.append(PageBreak())
p('Explorer et vérifier','title')
p('Étapes 3 et 4 : passer de la vue globale à un événement réel.','sub')
step('3. Rechercher les connexions d’un compte',
     'Dans <b>Explorer les connexions</b>, copier un compte présent dans le tableau, le rechercher, puis cliquer sur <b>Exporter CSV</b>.',
     'Cet explorateur permet de retrouver les connexions d’un compte, leurs machines source et destination, leur résultat et la décision du détecteur. L’export permet de poursuivre l’examen des événements sélectionnés.',
     'Vérifier la recherche, la cohérence des résultats et le téléchargement CSV.')
step('4. Relire un événement réel annoté',
     'Ouvrir <b>Vérifier une connexion → Relire des événements réels</b>. Choisir <b>Annotations red team</b>, puis cliquer sur <b>Lire l’événement suivant</b>. Montrer la décision et le score.',
     'Cet événement provient réellement du dataset. Son annotation correspond à une activité offensive connue, menée dans le cadre de l’exercice red team. Je vérifie si notre détecteur le signale. L’annotation n’entre pas dans le calcul de son score.<br/><br/>Le score affiché est la rareté moins le seuil : une valeur positive déclenche une alerte. Ce n’est pas une probabilité d’attaque.',
     'Observer la réaction du détecteur sur une activité réelle annotée.')
story.append(PageBreak())
p('Tester et interpréter','title')
p('Étapes 5 et 6 : évaluer une saisie et expliquer les résultats.','sub')
step('5. Analyser une saisie manuelle',
     'Dans <b>Évaluer une saisie</b>, analyser les valeurs proposées. Changer ensuite la destination pour une machine absente de l’historique, au format <b>C…</b>, et comparer les scores. Garder un temps postérieur à J+0.',
     'Cette saisie est un scénario de démonstration : elle ne modifie pas les journaux réels. Je compare une relation connue à une destination inconnue pour observer l’effet sur le score. Une machine nouvelle peut être légitime ; elle ne garantit pas une attaque ni systématiquement une alerte.',
     'Vérifier la prédiction sur une saisie et l’influence du contexte.')
step('6. Présenter les performances',
     'Ouvrir <b>Performance du modèle</b>. Montrer le rappel, la précision et la matrice de confusion.',
     'Le premier jour sert de référence, le deuxième à choisir le seuil et le troisième à évaluer le modèle. Sur 76 291 événements de test, le modèle contextuel détecte les 11 événements annotés, contre 1 pour l’ancien Isolation Forest.<br/><br/>Il produit 347 alertes, dont 336 sur des événements non annotés. Le rappel est de 100 %, mais la précision par rapport aux annotations reste de 3,17 %. Les annotations sont partielles et seulement 11 événements sont annotés : il faut confirmer ces résultats sur d’autres journées.',
     'Mesurer la détection et ses limites, au-delà du fonctionnement de l’interface.')
p('Pour conclure','label')
p('« Nous avons réalisé une chaîne complète : préparation des données réelles, calcul du contexte, détection et exploration des alertes. Le système aide à choisir les connexions à examiner ; il ne bloque pas les comptes et ne réalise pas lui-même une authentification multifacteur. »')

def decorate(c,doc):
    c.setFillColor(HexColor('#b78b5e'));c.rect(45,801,505,3,fill=1,stroke=0)
    c.setFont('Body',10);c.setFillColor(HexColor('#786250'))
    c.drawCentredString(297.5,28,str(doc.page))

OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=(595,842),rightMargin=48,leftMargin=48,
                  topMargin=55,bottomMargin=43,title='Guide de démonstration - LoginGuard AI').build(story,onFirstPage=decorate,onLaterPages=decorate)
print(OUT)
