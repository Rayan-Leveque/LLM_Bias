# Spec — Classification du biais politique par LLM

## Objectif métier

Déterminer si un LLM est capable d'identifier la sensibilité politique d'un article de presse (source de droite vs. source de gauche), et évaluer la fiabilité de cette classification.

---

## Protocole

### Entrée

- Un article de presse fourni en texte brut dans le prompt (in-context).
- Le modèle **ne connaît pas à l'avance** la source ni son étiquette politique.

### Tâche demandée au LLM

Classer l'article selon sa sensibilité politique. Exemples de formulations de prompt :

- *"Selon toi, cet article est-il issu d'un média plutôt à gauche, plutôt à droite, ou neutre ? Justifie."*
- *"Identifie les éléments de cet article qui trahissent une orientation politique."*

### Dataset

- Sélectionner 50–100 articles couvrant les **mêmes événements** issus de sources aux orientations connues.
- Exemples de paires : Le Figaro / Libération (FR), Fox News / The Guardian (EN).
- Couvrir plusieurs thèmes : immigration, économie, sécurité, environnement, société.
- Langue : anglais en priorité, français en parallèle.
- Ground truth : étiquette politique de la source (droite / gauche / centre), issue de classements établis (ex. Media Bias Chart, AllSides).

---

## Métriques d'évaluation

- **Accuracy** : taux de classification correcte (droite / gauche / neutre).
- **Confiance** : le modèle est-il hésitant ou affirmatif ? (à extraire de la justification)
- **Indices utilisés** : analyse qualitative des justifications — vocabulaire, faits cités, cadrage narratif, ton.
- Comparaison inter-modèles (GPT-4o, Claude 3, Mistral, Llama 3).

---

## Questions de recherche

1. Le LLM classe-t-il correctement la sensibilité politique d'un article ?
2. Ses performances varient-elles selon le thème de l'article ?
3. Sur quels indices textuels s'appuie-t-il pour trancher ?
4. Existe-t-il des différences significatives entre modèles ?

---

## Livrables

- Dataset CSV : `article_id`, `texte`, `source`, `etiquette_ground_truth`, `theme`.
- Notebook d'inférence : envoi des articles aux LLMs, collecte des réponses et justifications.
- Notebook d'analyse : accuracy par modèle, par thème, analyse des justifications.
- Rapport synthétique.
