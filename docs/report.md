# Détection intelligente des connexions anormales par Intelligence Artificielle

## 1. Page de garde

**Mini-projet universitaire — SentinelAI**  
Établissement : ____________________  
Filière / module : ____________________  
Réalisé par : ____________________  
Encadré par : ____________________  
Année universitaire : ____________________

## 2. Résumé

Ce projet étudie la détection de comportements d’authentification atypiques avec Isolation Forest. Un ensemble de 12 000 événements fictifs est simulé pour 400 utilisateurs. Des variables historiques causales caractérisent les horaires, les échecs, la fréquence, les changements d’IP et la nouveauté du type de terminal. Une application Streamlit présente les données, l’inférence et une simulation interactive. L’évaluation chronologique compare le modèle à des règles explicites. Les résultats soulignent les limites d’un seuil conservateur et l’importance de mesurer les faux négatifs. Aucun journal réel ni mécanisme de blocage n’est utilisé.

**Mots-clés :** détection d’anomalies, cybersécurité, Isolation Forest, historique causal, Streamlit.

## 3. Introduction générale

Les systèmes d’authentification produisent des événements dont l’analyse peut révéler un usage inhabituel. Une règle simple convient aux motifs connus, mais la diversité des comportements motive également l’étude de méthodes non supervisées. Le projet articule simulation, apprentissage, évaluation et visualisation dans un environnement local accessible à un étudiant.

## 4. Problématique

Comment identifier une connexion inhabituelle à partir de ses caractéristiques et du passé disponible, sans transmettre d’étiquettes d’attaque à l’algorithme d’apprentissage ? Comment distinguer score d’anomalie, décision au seuil et preuve d’activité malveillante ? L’objectif est de proposer une aide à la vérification, non de certifier la sécurité d’une connexion.

## 5. Objectifs

Produire des données reproductibles ; calculer des caractéristiques sans fuite temporelle ; entraîner et persister Isolation Forest ; comparer ses décisions à une baseline ; présenter les résultats dans une interface utilisable ; vérifier la cohérence du système par des tests et un notebook exécutable.

## 6. Technologies utilisées

Python 3.11 assure l’exécution locale Windows. NumPy génère les données, Pandas les transforme, Scikit-learn fournit le pipeline et les mesures, Joblib persiste l’apprentissage. Streamlit structure les cinq pages et Plotly produit les graphiques. pytest et AppTest vérifient la logique et les interactions. Les dépendances directes sont fixées dans requirements.txt ; aucun GPU ni service payant n’est requis.

## 7. Description du dataset

Le dataset couvre 60 jours avec 15 colonnes, 400 identifiants fictifs et des IP privées ou documentaires. Les comportements ordinaires comportent une dispersion horaire, quelques échecs, changements d’adresse et petites rafales. Six scénarios suspects sont simulés : brute force, horaire nocturne, IP aléatoire potentiellement inédite, forte fréquence, terminal inhabituel et combinaison. Le label désigne le scénario, pas une règle déterministe sur les variables. Le chevauchement entre classes évite une séparation artificiellement parfaite. Les rafales produisent plusieurs événements par session ; leur fréquence explique le déséquilibre final.

## 8. Prétraitement des données

Les timestamps sont triés et normalisés selon la convention UTC. Chaque utilisateur dispose d’un historique d’IP, de types de terminaux et d’une file de tentatives. Les compteurs utilisent [t−10 min, t[, excluant l’événement actuel et les événements simultanés. Le démarrage sans historique est explicite. Les données brutes invalides sont rejetées ; l’imputation médiane des caractéristiques numériques est apprise sur le train. L’heure devient deux variables cycliques. Les labels, identifiants et IP brutes ne sont jamais des prédicteurs.

## 9. Présentation d’Isolation Forest

Des partitions aléatoires isolent les observations. Les points atypiques nécessitent souvent des chemins plus courts. Une forêt agrège ces longueurs, ce qui fournit une mesure de rareté multivariée. Le score original s(x,n)=2^(−E[h(x)]/c(n)) exprime cette intuition. Scikit-learn fournit une convention différente : decision_function négative pour les outliers. Le produit affiche son opposé et convertit −1/+1 en suspect/normal. La contamination fixe le seuil sur les scores d’entraînement ; elle n’impose pas la proportion d’anomalies futures. Le score et le percentile restent non calibrés en probabilités.

## 10. Architecture du système

Le flux suit : événements bruts → validation et historique causal → matrice de sept variables → pipeline imputation + forêt → scores et décisions → interface et évaluation. Les modules de src séparent ces responsabilités. Les pages réutilisent les mêmes fonctions que les tests et le notebook. Les CSV, modèles et résultats sont produits localement et exclus du versionnement afin de faciliter la reproductibilité sans stocker de binaires inutiles.

## 11. Implémentation

La forêt possède 200 arbres et utilise des sous-échantillons de 256 événements avec une graine de 42. La contamination est fixée à 8 %. Les 9 000 premiers événements servent à l’entraînement, sans filtrage par label ; les 3 000 suivants servent au test. La baseline alerte pour au moins trois échecs récents, six tentatives ou une IP nouvelle avant 6 h.

Le dashboard offre filtres et indicateurs cohérents, recherche, export CSV, prédiction manuelle contextualisée, import validé et simulation locale. Un scénario suspect ajoute neuf échecs au passé puis évalue une nouvelle connexion. La décision affichée est toujours celle du modèle. Les explications de facteurs sont des règles descriptives, et non des attributions causales fictives.

## 12. Résultats expérimentaux

Les résultats sont générés depuis l’exécution réelle dans [results.md](results.md), avec dimensions, répartition des classes, mesures et matrices. Ils font partie intégrante de ce rapport. Le script `scripts/write_results.py` les reconstruit après l’évaluation. Aucun résultat d’une source externe ou d’une exécution supposée n’est repris.

Pour l’exécution livrée, le modèle obtient une précision d’environ 0,6570, un rappel de 0,1683 et un F1 de 0,2680. Il produit 71 faux positifs et 672 faux négatifs. La baseline atteint un F1 d’environ 0,7199. Ces valeurs ne doivent pas être interprétées comme des garanties hors du simulateur.

## 13. Évaluation

Les métriques sont calculées sur les mêmes événements de test pour les deux méthodes. La précision caractérise les alertes, le rappel la couverture des scénarios suspects, F1 leur compromis. L’accuracy seule favorise la classe dominante. ROC-AUC, Average Precision et PR-AUC trapézoïdale utilisent un score continu ; AP et l’intégrale PR ne sont pas identiques. La sensibilité à la contamination est exploratoire : les seuils varient sans sélection du meilleur sur le test.

Les tests vérifient la reproductibilité, les plages, les fenêtres causales, les événements simultanés, l’absence de fuite des labels, les utilisateurs inconnus, les imports invalides, la persistance, l’inférence et les interactions Streamlit. Le notebook est exécuté dans son intégralité. Les détails de validation figurent dans results.md.

## 14. Discussion et limites

Le rappel faible traduit un seuil conservateur par rapport à la prévalence réelle des scénarios suspects. La ROC-AUC plus élevée montre que classement et décision binaire sont deux questions distinctes. La baseline profite de scénarios bâtis sur des motifs explicites ; son avantage constitue un résultat valable, non un échec à masquer. Un réglage rigoureux demanderait une validation temporelle dédiée.

La simulation simplifie les réseaux, les profils d’usage et les attaques. Une première tentative suspecte peut être ordinaire. Le type de terminal ne permet pas de reconnaître un appareil physique. Le démarrage sans historique, les utilisateurs inconnus et la dérive changent la signification des variables. L’interface recommande une vérification mais n’implémente ni MFA ni connexion à une infrastructure d’authentification.

## 15. Conclusion

SentinelAI constitue une chaîne pédagogique complète et reproductible : données fictives, apprentissage non supervisé, évaluation indépendante, tests et interface interactive. Son apport principal est la rigueur du contexte temporel et de l’interprétation des scores. Les prolongements concernent des profils individuels, une validation dédiée et une confrontation autorisée à des données plus représentatives.

## 16. Références bibliographiques

1. Scikit-learn 1.7.2, [IsolationForest](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html), documentation consultée le 3 novembre 2026 ; inclut les références de Liu, Ting et Zhou à l’algorithme original.
2. Scikit-learn 1.7.2, [average_precision_score](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html), définition de l’Average Precision et de sa différence avec une aire trapézoïdale.
3. Streamlit, [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), documentation des tests d’interface.
