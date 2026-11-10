# Méthodologie scientifique

## Problème et périmètre

Une connexion réussie ne garantit pas une utilisation légitime. Nous cherchons des événements atypiques à proposer à une vérification supplémentaire. Le système ne reçoit aucune donnée réelle et ne bloque aucun compte. L’unité d’analyse est un événement d’authentification, avec son contexte antérieur par utilisateur.

## Simulation reproductible

Le générateur utilise NumPy et une graine de 42. Il produit 12 000 événements pour 400 utilisateurs fictifs sur 60 jours à partir du 1er janvier 2026. L’horaire habituel varie selon l’utilisateur, avec une dispersion de 2,5 heures. Les terminaux ordinaires sont desktop, mobile et tablet. Les adresses appartiennent au réseau privé 10.0.0.0/8 ou aux plages documentaires 192.0.2.0/24 et 198.51.100.0/24.

Une session peut être normale ou appartenir à six scénarios : échecs répétés, connexion nocturne, IP inédite, fréquence élevée, nouveau type de terminal, combinaison de signaux. Certains scénarios créent plusieurs événements espacés de 25 secondes. La probabilité de choisir un scénario suspect par session est 6,5 % ; **ce n’est pas la proportion finale d’événements suspects**, car les rafales en produisent davantage. Les événements légitimes peuvent également survenir la nuit, échouer, changer d’adresse ou former de petites rafales. Les classes se recouvrent volontairement.

Le label décrit l’intention du scénario simulé, et non une règle appliquée aux caractéristiques. Une première tentative d’une attaque peut être impossible à distinguer du comportement ordinaire. Les adresses tirées au hasard peuvent avoir déjà été vues : le scénario « unseen_ip » n’impose pas artificiellement la variable `new_ip`.

## Historique causal

Les événements sont triés avant l’extraction. Pour un événement au temps t, la fenêtre est [t−10 minutes, t[. Elle exclut la connexion courante et tous les événements simultanés. Une file par utilisateur conserve les timestamps et résultats antérieurs ; deux ensembles conservent les IP et types de terminaux déjà observés. La dernière IP permet de mesurer un changement.

Au démarrage sans historique, les indicateurs de nouveauté valent 1 au sens « jamais observé dans les données disponibles ». Ils ne prouvent pas qu’un terminal physique ou une IP est réellement nouveau. Le champ device_type ne permet pas de reconnaître deux appareils différents du même type : c’est une limite explicite.

Les caractéristiques sont : sin(2πh/24), cos(2πh/24), nombre d’échecs antérieurs, nombre de tentatives antérieures, changement d’IP, nouveauté IP et nouveauté du type de terminal. L’encodage cyclique rapproche 23 h de 0 h. L’heure est discrétisée à l’heure entière. Il n’existe pas de normalisation personnelle des habitudes horaires dans cette version.

## Contrôles et prétraitement

Les champs bruts obligatoires, IP, timestamps, valeurs binaires et identifiants sont validés ; les doublons d’identifiants et données brutes manquantes sont rejetés avec un message. Les timestamps sont normalisés en UTC sans fuseau pour faciliter les calculs ; les dates naïves sont interprétées comme UTC. L’interface utilise la même convention. Pour les caractéristiques numériques manquantes à l’inférence, un SimpleImputer emploie la médiane apprise exclusivement sur le train. Il est persisté dans le même Pipeline que la forêt. Aucune mise à l’échelle n’est requise pour ces arbres à coupures aléatoires.

Les caractéristiques excluent event_id, user_id, source_ip, anomaly_type et is_anomaly. La fonction feature_matrix sélectionne une liste fermée. Les imports recalculent les variables historiques au lieu de faire confiance aux compteurs fournis.

## Isolation Forest : intuition et conventions

Chaque arbre choisit une caractéristique et une coupure aléatoires. Un point isolé en peu de coupures est inhabituel. La longueur moyenne de chemin E[h(x)] est normalisée par c(n), longueur attendue dans un arbre de recherche aléatoire : le score original s(x,n)=2^(−E[h(x)]/c(n)) augmente lorsque l’isolement est rapide. Ce score original n’est pas directement le score affiché ici.

Scikit-learn expose `decision_function = score_samples − offset_`. Une valeur négative indique un outlier. `predict` renvoie −1 pour un outlier et +1 pour un inlier. Le système affiche `anomaly_score = −decision_function`, puis 1 = suspect et 0 = normal. Au seuil exact zéro, l’événement est un inlier. Le percentile affiché est le rang du score parmi les scores du train ; il ne représente pas une probabilité d’attaque.

## Entraînement et séparation

Les premiers 75 % des événements forment le train ; les derniers 25 % constituent le test. La forêt est entraînée sur **tout le train majoritairement normal**, sans filtrage par le label. Paramètres : 200 arbres, max_samples=256, random_state=42, contamination=0,08, n_jobs=1. La contamination fixe l’offset, sans imposer que 8 % des événements de test soient suspects. Ce choix pédagogique est fixé avant l’évaluation et peut sous-estimer la prévalence des scénarios simulés.

Le calcul causal sur la série entière avant le découpage ne fuit pas le futur : le contexte du train est disponible au début du test. L’imputation et les arbres sont ajustés exclusivement sur le train. Le test reste non vu pendant cet ajustement.

## Évaluation et expérimentation

Le même test est évalué par la forêt et une règle : au moins 3 échecs antérieurs OU au moins 6 tentatives antérieures OU une IP nouvelle avant 6 h. Les seuils sont des choix de démonstration, pas une norme de cybersécurité.

La matrice donne VN, FP, FN et VP. Précision=VP/(VP+FP), rappel=VP/(VP+FN), F1=2PR/(P+R), taux de faux positifs=FP/(FP+VN). L’accuracy doit être interprétée avec le déséquilibre des classes. ROC-AUC mesure le classement global ; Average Precision résume la courbe précision-rappel sans interpolation trapézoïdale, lorsque les deux classes existent.

La sensibilité à plusieurs contaminations est affichée à titre descriptif : les arbres sont conservés, l’offset est recalculé sur les scores du train. **Aucun meilleur seuil n’est sélectionné à partir du test.** Une optimisation ultérieure nécessiterait un jeu de validation temporel distinct, puis un nouveau test final.

## Limites

Le simulateur simplifie fortement les habitudes et peut favoriser les règles construites sur ses scénarios. Les métriques ne garantissent aucune performance sur des journaux réels. Une anomalie n’est pas une preuve d’attaque ; des attaques discrètes peuvent rester normales. Les erreurs, la dérive et l’absence d’historique sont des limites centrales. Les indications de facteurs dans l’interface sont des règles transparentes, pas des attributions calculées par Isolation Forest.

## Références vérifiées

- [Scikit-learn 1.7 — IsolationForest](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html), paramètres, références originales de Liu, Ting et Zhou (2008 et 2012), scores et offset.
- [Scikit-learn 1.7 — Average Precision](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html), définition et différence avec l’intégration trapézoïdale.
- [Streamlit — AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), tests d’interfaces et interactions.
