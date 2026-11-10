# Soutenance : parcours de 9 minutes

## 0:00–1:00 — Présenter la question

« Comment repérer une connexion inhabituelle sans disposer d’exemples de toutes les attaques ? Clair analyse le contexte d’authentification et propose une vérification supplémentaire. Toutes les données de la démonstration sont fictives. »

## 1:00–2:00 — Expliquer les données

Présenter les 12 000 événements et les 400 utilisateurs. Montrer les horaires, les échecs et les IP. Expliquer les six scénarios et les événements légitimes atypiques. Une session suspecte peut produire une rafale : la proportion d’événements n’est pas la probabilité de scénario.

## 2:00–3:15 — Montrer le passé disponible

Ouvrir `src/preprocessing.py`. Expliquer la fenêtre de dix minutes excluant la connexion actuelle, la distinction IP changée/IP jamais observée et la nouveauté d’un type de terminal. Montrer la liste FEATURES : aucun label ni identifiant. Dire que les timestamps de la démonstration sont traités en UTC.

## 3:15–4:15 — Présenter Isolation Forest

« On coupe aléatoirement les données avec plusieurs arbres. Un point rare est souvent isolé en peu de coupes. La moyenne sur de nombreux arbres rend ce signal plus stable. » Expliquer les 200 arbres et le seuil fixé par la contamination. La forêt ne lit jamais la colonne indiquant les attaques.

## 4:15–6:30 — Démonstration du produit

1. Vue de sécurité : filtrer un utilisateur et constater que les indicateurs et graphiques changent ensemble.
2. Analyse : montrer les tentatives récentes et exporter le CSV.
3. Détection : évaluer un compte connu, puis un compte sans historique ; lire le message explicite sur le contexte inconnu.
4. Simulation : générer un événement normal puis suspect. Montrer les neuf échecs préalables du scénario suspect, la décision réellement calculée et la recommandation. Ne pas promettre que tout scénario sera détecté.
5. Réinitialiser la session pour montrer que les événements de démonstration ne modifient pas le dataset local.

## 6:30–8:00 — Interpréter l’évaluation

Afficher la page Performance, réservée au test chronologique. Lire les valeurs réellement affichées, y compris les faux négatifs. La précision indique combien d’alertes sont correctes, le rappel combien d’événements suspects sont repérés. Comparer aux règles sur le même test ; ne pas prétendre que l’IA doit forcément gagner. Une règle peut bien fonctionner sur un simulateur construit avec des motifs explicites.

## 8:00–9:00 — Limites et conclusion

« Le système est reproductible et démontrable, mais une anomalie ne prouve pas une attaque. Les journaux réels sont plus complexes. Il faudrait valider sur des données représentatives, gérer la dérive et mesurer le coût des erreurs avant tout usage opérationnel. »

## Questions probables

**Pourquoi Isolation Forest ?** Il apprend sans labels, traite des caractéristiques numériques simples et fonctionne sur CPU avec un coût raisonnable.

**Pourquoi avoir des labels ?** Pour mesurer objectivement les erreurs sur le test, pas pour apprendre la forêt ni choisir les lignes d’entraînement.

**Pourquoi pas de découpage aléatoire ?** Il mélangerait passé et futur et rendrait moins crédible l’évaluation d’un système historique.

**Pourquoi une heure sin/cos ?** Minuit et 23 h doivent être proches. Un entier brut ne représente pas correctement cette proximité.

**Est-ce une probabilité d’attaque ?** Non. Le score mesure un écart au seuil ; le percentile est un rang dans l’historique d’entraînement.

**Pourquoi des faux négatifs ?** Certaines premières tentatives sont ordinaires, les classes se recouvrent, et le seuil est un compromis entre rappel et fausses alertes.

**Les règles sont meilleures ?** Les données contiennent des scénarios définis par des motifs simples ; c’est possible. La comparaison honnête est plus utile qu’un résultat artificiellement favorable à l’IA.

**Que se passe-t-il pour un utilisateur inconnu ?** Les compteurs démarrent à zéro et la nouveauté signifie seulement « pas encore observé ». L’interface le précise.

**Un nouveau mobile est-il détecté ?** Seulement si son type n’avait jamais été observé. Sans identifiant de terminal, deux mobiles restent indistinguables.

**Comment améliorer ?** Ajouter une validation temporelle, des profils horaires par utilisateur, des données autorisées représentatives et une stratégie de réentraînement évaluée.

## Préparation avant la séance

Lancer les tests, démarrer Streamlit et ouvrir le navigateur local. Vérifier les cinq pages. Garder le README, le notebook et le rapport à disposition. Ne pas installer les dépendances pendant la soutenance ; une fois préparé, le produit fonctionne sans service externe.
