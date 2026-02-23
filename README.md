# LLM Bias — Biais d'évaluation des LLMs en contexte d'embauche

Pipeline expérimental pour mesurer les biais des LLMs lors de l'évaluation de CV, en contexte français.

## Hypothèse

Lorsqu'un LLM évalue des candidats **séparément**, il tend à favoriser les minorités (sur-correction RLHF). Lorsqu'il est placé en **comparaison directe**, il tend à favoriser la majorité (activation de stéréotypes implicites).

Cette dissociation est testée via deux conditions expérimentales (single vs. comparative) sur des CV dont seuls les marqueurs d'identité varient.

Pour le détail du design expérimental, voir [docs/design.md](docs/design.md).

## Structure du projet

```
├── docs/               # Documentation et design expérimental
├── data/
│   ├── templates/      # Templates de CV (stimuli)
│   └── results/        # Résultats bruts des expériences
├── src/
│   ├── generation/     # Génération des CV à partir des templates
│   ├── evaluation/     # Appels LLM (conditions single & comparative)
│   └── analysis/       # Analyse statistique (chi², Fisher, etc.)
└── notebooks/          # Notebooks d'exploration et d'analyse
```

## Installation

*À venir.*

## Usage

*À venir.*

## Références

- Gallegos et al. (2025) — [Biases in the Blind Spot](https://arxiv.org/abs/2602.10117)
- Bai et al. (2024) — [IAT adapté aux LLMs](https://arxiv.org/abs/2402.04105)
- Hsee (1996) — Évaluation séparée vs. conjointe
- Bertrand & Mullainathan (2004) — Audit studies
