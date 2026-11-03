# Publication GitHub

Le dépôt public est [HajarLaziz/SentinelAI-Login-Anomaly-Detection](https://github.com/HajarLaziz/SentinelAI-Login-Anomaly-Detection). L’identité du propriétaire a été vérifiée avec GitHub CLI. Les 13 jalons locaux ont été publiés successivement après l’authentification, avec contrôle du SHA distant après chaque push. La publication avait initialement été suspendue faute d’authentification ; il ne s’agit donc pas d’une publication continue pendant la phase initiale de développement.

## Authentification pour les prochaines contributions

Depuis la racine du projet, GitHub CLI téléchargé depuis son dépôt officiel est disponible localement (hors Git) :

```powershell
.\.tools\gh\bin\gh.exe auth login --hostname github.com --git-protocol https --web
.\.tools\gh\bin\gh.exe auth status
.\.tools\gh\bin\gh.exe api user --jq .login
```

Le résultat doit être **HajarLaziz**. Ne jamais partager un jeton dans le chat, le code ou les commits. Sur une autre machine, installer GitHub CLI depuis sa source officielle, puis remplacer le chemin local par `gh`.

## Vérifier le dépôt avant toute création

```powershell
.\.tools\gh\bin\gh.exe repo view HajarLaziz/SentinelAI-Login-Anomaly-Detection --json nameWithOwner,visibility,url
git remote -v
```

Si le dépôt existe, vérifier son propriétaire, sa visibilité et son contenu. Ne pas interpréter une erreur réseau ou d’autorisation comme une preuve qu’il est absent. Ne pas écraser un dépôt contenant du travail indépendant.

Si le dépôt est confirmé absent, le créer sans README distant initial, pour conserver l’historique local :

```powershell
.\.tools\gh\bin\gh.exe repo create HajarLaziz/SentinelAI-Login-Anomaly-Detection --public --description "AI-powered login anomaly detection system using Isolation Forest, Python, Scikit-learn and Streamlit. University cybersecurity mini-project with an interactive monitoring dashboard."
git remote add origin https://github.com/HajarLaziz/SentinelAI-Login-Anomaly-Detection.git
git push -u origin main
```

Si `origin` existe déjà, inspecter sa destination avant toute modification. Ne jamais utiliser `--force` pour résoudre une divergence. La commande push publie les commits distincts conservés localement ; elle ne recrée pas une publication continue qui n’a pas pu avoir lieu.

## Vérification après publication

```powershell
git rev-parse HEAD
git ls-remote origin refs/heads/main
.\.tools\gh\bin\gh.exe repo view HajarLaziz/SentinelAI-Login-Anomaly-Detection --json nameWithOwner,visibility,url
git status --short
```

Les identifiants du commit local et de la branche distante doivent correspondre ; la visibilité doit être PUBLIC. Ajouter uniquement les fichiers du jalon concerné lors des évolutions suivantes et vérifier chaque push. Le choix de licence reste à confirmer avant l’ajout d’un fichier LICENSE.

Référence : [GitHub CLI — authentification](https://cli.github.com/manual/gh_auth_login).
