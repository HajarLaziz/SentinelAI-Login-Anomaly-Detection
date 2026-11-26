# Comparaison des modèles sur LANL

Le détecteur de rareté contextuelle complète Isolation Forest, qui reste disponible
dans le sélecteur du tableau de bord. Il apprend les fréquences des relations
compte–source, compte–destination et source–destination sur J+0 seulement.
Les identifiants servent de clés de comptage, jamais de nombres ordinaux.

Pour chaque relation, le score est `-log((effectif + 1) / (total + V))`,
où V est le nombre de machines distinctes de référence plus une catégorie inconnue.
Le maximum des trois raretés constitue le score brut. Le score affiché soustrait
le seuil : une valeur strictement positive déclenche une vérification.
Ce modèle statistique non supervisé n'est pas une nouvelle variante d'Isolation Forest.

## Protocole

- Référence : J+0, 78 924 événements, sans utilisation des annotations.
- Validation : J+1, 88 032 événements, 9 annotations.
- Deux candidats : rareté relationnelle et Isolation Forest sur des caractéristiques contextuelles.
- Quatre quantiles de seuil prédéfinis : 99 %, 99,5 %, 99,9 %, 99,95 %.
- Sélection au meilleur F1 de validation, avec au plus 1 % d'alertes de validation.
- Test : J+2, 76 291 événements, 11 annotations ; aucun réajustement après son évaluation.

La rareté avec le quantile 99,5 % est sélectionnée. Seuil : 6,0661080901.
La référence reste figée après sélection. Le tableau de bord exclut J+0 pour ce
modèle et refuse les saisies antérieures à la fin de sa référence. Les imports
utilisent aussi cette référence apprise ; leurs compteurs temporels sont calculés
sur le fichier importé. Une nouveauté de machine n'est pas une preuve d'attaque.

## Résultats réellement calculés

| Mesure sur J+2 | Isolation Forest historique | Rareté contextuelle |
|---|---:|---:|
| Annotations détectées | 1 / 11 | 11 / 11 |
| Rappel | 9,09 % | 100 % |
| Précision par rapport aux annotations | 0,50 % | 3,17 % |
| F1 | 0,95 % | 6,15 % |
| Alertes non annotées | 198 | 336 |
| Total des alertes | 199 | 347 |

La matrice du nouveau modèle est `[[75944, 336], [0, 11]]`.
ROC-AUC : 0,99876 ; average precision : 0,08148.
Les résultats complets, y compris tous les essais de validation, figurent dans
`docs/model_comparison.json`. Le fichier est régénéré par le programme.

## Limites de la conclusion

Le rappel est nettement meilleur sur ce sous-ensemble, mais la précision reste
faible. Les annotations LANL sont partielles : les 336 alertes non annotées ne
sont pas toutes démontrées fausses. Onze événements annotés, possiblement liés
à une même campagne, ne permettent pas de promettre 100 % de rappel ailleurs.
J+2 avait déjà été étudié pour le modèle historique : il ne constitue pas une
nouvelle évaluation externe aveugle. Il faut confirmer sur des journées ultérieures
et une cohorte élargie avant de parler de performance robuste.
Le modèle historique a deux jours d'apprentissage ; le candidat a un jour de
référence et un jour de validation. Cette différence fait partie de la comparaison.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m src.compare_models
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Le modèle est enregistré localement dans `models/lanl_context_candidate.joblib`.
Il devient l'option initiale du tableau de bord lorsque cet artefact existe.
Les rapports PDF et diapositives précédents décrivent l'ancien modèle ; les
nouveaux résultats sont documentés ici, sans modifier rétrospectivement leurs chiffres.
