# Rapport académique LoginGuard AI

Le rapport final se trouve dans `../../output/pdf/Rapport_LoginGuard_AI_FSSM_2026_2027.pdf`.

- 30 pages A4, sommaire cliquable et signets PDF.
- Couverture FSSM, Hajar Laziz et Jihane Hamouchi, encadrement Pr. Mariya Ouaissa.
- Année 2026-2027, Master S3, module Sécurité des systèmes d’information et l’IA.
- 8 captures réelles, 3 schémas vectoriels et 1 graphique comparatif vectoriel.
- Métriques recalculées le 16 novembre 2026 ; 32 tests réussis ; 11 cellules du notebook exécutées.

## Reconstruction sous Windows

Le PDF est composé avec ReportLab dans un style académique inspiré de LaTeX. La source éditable est `scripts/build_report_pdf.py`. Elle utilise les polices Times présentes dans `C:/Windows/Fonts` et les ressources de ce dossier. Aucun moteur LaTeX n’est nécessaire.

```powershell
.\.venv\Scripts\python.exe -m pip install -r docs\rapport\requirements-report.txt
.\.venv\Scripts\python.exe scripts\build_report_pdf.py
```

Les dépendances du rapport sont séparées de celles de l’application.
`facts.json` et `metrics.json` constituent un instantané des résultats vérifiés ; ils doivent être mis à jour si le modèle ou les données changent. Les résultats sont calculés avec `python -m src.evaluate_model` ; le rapport ne modifie ni les données ni le modèle.

## Illustrations et contrôle

`UCA-FSSM.png` est le logo fourni pour le rapport. `captures/` conserve les images originales. La capture d’accueil reprend la vue complète validée le 13 novembre ; les sept autres vues ont été capturées le 16 novembre 2026. Le PDF recadre la partie centrale de ces dernières pour améliorer la lisibilité sans modifier les fichiers source.

Chaque page du PDF a été rendue et inspectée. Le contrôle textuel vérifie les noms, le nombre de pages, le sommaire et l’absence de paragraphes isolés sur une page presque vide. Les rendus de travail sont dans `tmp/pdfs/`, exclu de Git.
