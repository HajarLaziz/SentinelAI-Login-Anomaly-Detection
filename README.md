# LoginGuard AI — authentifications réelles LANL

Tableau de bord local de détection des connexions inhabituelles avec Isolation Forest, Python, Pandas, Scikit-learn, Streamlit et Plotly.

Le tableau de bord propose aussi un **détecteur de rareté contextuelle** fondé
sur les habitudes compte–machine. Sur J+2 : 11 annotations détectées sur 11,
347 alertes, précision relative aux annotations de 3,17 %. Ce rappel ne garantit
pas la généralisation : le test ne contient que 11 annotations partielles.
Voir [le protocole et les résultats comparés](docs/context_model.md).

## Dataset réellement utilisé

[Comprehensive, Multi-Source Cyber-Security Events, LANL](https://csr.lanl.gov/data/cyber1/), Alexander D. Kent (2015), DOI **10.17021/1179829**. Journaux d’entreprise collectés et anonymisés, téléchargés depuis le miroir académique Imperial College. Aucun événement synthétique n’alimente le tableau de bord.

Le sous-ensemble comporte **243 247 événements, 459 comptes et 2 799 échecs**, sur les trois premiers jours relatifs. Sélection fixée sans consulter les annotations : comptes sources U1 à U1000, machines connues, NTLM / Network / LogOn. Il ne représente pas l’ensemble du réseau LANL.

Les machines C… ne sont pas des IP. Dates civiles, fuseau et types physiques de terminaux ne sont pas publiés. L’heure affichée est relative, pas une heure locale permettant de conclure à une connexion nocturne.

## Installation Windows / VS Code

Ouvrir ce dossier dans VS Code, puis son terminal PowerShell :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.import_lanl
.\.venv\Scripts\python.exe -m src.lanl
.\.venv\Scripts\python.exe -m src.compare_models
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Sur ce PC, les données et le modèle existent déjà : seule la dernière commande est nécessaire. Aucune activation PowerShell ni privilège administrateur requis. `start.ps1` automatise ces étapes, sans télécharger de nouveau lorsque les fichiers existent.

L’import initial télécharge environ 326 Mio compressés, parcourt environ 49 millions de lignes et conserve une cohorte intermédiaire avant sélection NTLM. Prévoir environ 1 Go libre et plusieurs minutes. Aucun accès externe n’est nécessaire ensuite. Les données et modèles sont exclus de Git ; les empreintes de provenance figurent dans `docs/lanl_results.json`.

## Méthode et résultats exécutés

166 956 événements des deux premiers jours entraînent le modèle ; 76 291 du troisième jour servent au test. Sept variables : heure relative cyclique, tentatives et échecs antérieurs sur dix minutes, changement de source, nouveauté source et destination. Fenêtre [t−600, t[ ; les événements simultanés ne se voient pas mutuellement. Le contexte est limité aux événements sélectionnés. Aucun identifiant brut ou label n’entre dans le modèle.

200 arbres, contamination 1 %, seed 42. Les annotations ne servent ni à sélectionner les comptes, ni à entraîner, ni à fixer le seuil. `prediction=1` indique un score négatif de `decision_function` ; le score affiché est son opposé. Le percentile historique n’est pas une probabilité d’attaque.

Les annotations red team sont **partielles** : non annoté ne signifie pas normal. Le test contient 11 événements annotés. Isolation Forest en détecte **1**, en manque **10**, et signale **198 événements non annotés** (199 alertes). Précision relative aux annotations : **0,50 %** ; rappel : **9,09 %** ; F1 : **0,95 %** ; ROC-AUC : **0,6700**. Le taux d’alertes parmi les non annotés est **0,2596 %**. L’accuracy de 99,73 % masque le faible rappel.

Le seuil simple de règles détecte 6/11 annotations mais alerte sur 71 062 non-annotés (93,16 %). Il est manifestement trop sensible à la fréquence des authentifications de service. Les résultats sont conservés tels quels ; aucune efficacité opérationnelle n’est revendiquée.

## Utilisation

- Vue d’ensemble : filtres communs, statistiques calculées et graphiques.
- Explorateur : recherche de comptes et machines, export CSV de la sélection.
- Performance : test chronologique, matrice, comparaison avec règles et limites des annotations.
- Vérification : saisie manuelle explicitement distincte du dataset, import CSV validé et relecture de véritables événements du test. Aucun générateur ne remplace les données absentes.

## Architecture

```text
app.py                         # entrée du tableau de bord réel
src/import_lanl.py             # téléchargement borné, sélection, annotations
src/lanl.py                    # validation, historique, entraînement, inférence
src/real_dashboard.py          # quatre onglets, formulaires, relecture
assets/style.css              # thème beige / brun
start.ps1                     # installation et lancement
requirements.txt              # dépendances
 data/lanl/                   # sources, CSV et métriques locaux (ignorés)
models/lanl_isolation_forest.joblib
 tests/test_lanl.py            # causalité, schéma, persistance et provenance
 docs/lanl_results.json        # résultats calculés et empreintes
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Les petits exemples écrits à la main dans les tests sont des fixtures de validation, pas le dataset d’apprentissage. Les anciens modules synthétiques et pages sont conservés pour compatibilité ; ils ne sont pas appelés par `app.py` ni `start.ps1`.

## Documents antérieurs

**Le PDF universitaire et les captures créés avant cette migration décrivent la version synthétique. Ils ne constituent pas un rapport de résultats LANL.** Leur mise à jour complète reste nécessaire. La référence actuelle est ce README et `docs/lanl_results.json`. L’ancienne documentation est conservée comme archive explicitement identifiée.

## Limites et pistes

Annotations incomplètes, cohorte restreinte, seulement trois jours et onze annotations de test ; aucun déploiement de sécurité réel. Une anomalie ne prouve pas une attaque. Étendre la période, ajouter un jeu de validation temporel indépendant et étudier les profils par compte avant toute optimisation du seuil. L’application recommande une vérification mais n’exécute pas de MFA.
