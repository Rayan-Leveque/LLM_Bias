# LLM Bias — Biais d'évaluation des LLMs en contexte d'embauche

Pipeline expérimental pour mesurer les biais des LLMs lors de l'évaluation de CV, en contexte français.

## Hypothèse

Lorsqu'un LLM évalue des candidats **séparément**, il tend à favoriser les minorités (sur-correction RLHF). Lorsqu'il est placé en **comparaison directe**, il tend à favoriser la majorité (activation de stéréotypes implicites).

Cette dissociation est testée via deux conditions expérimentales (single vs. comparative) sur des CV dont seuls les marqueurs d'identité varient.

Pour le détail du design expérimental, voir [docs/design.md](docs/design.md).

## Pourquoi des modèles open-source / on-premise ?

Ce pipeline teste exclusivement des modèles **open-weight** déployables localement (vLLM) ou via des APIs cloud open-source (Novita AI). Nous ne testons pas GPT-4, Claude ou Gemini. Ce choix est délibéré et méthodologiquement justifié :

1. **Validité écologique du déploiement.** Les systèmes de pré-sélection automatisée en entreprise sont massivement déployés *on-premise* ou via des APIs open-source, non via des APIs propriétaires coûteuses et instables. Tester ces modèles, c'est auditer les outils réellement utilisés par les DSI et les éditeurs de RH.

2. **Reproductibilité scientifique.** Les poids des modèles open-source sont figés et versionnés. Un reviewer peut relancer exactement le même modèle (mêmes poids, même tokenizer, mêmes hyperparamètres) dans 2 ans. Les modèles closed-source changent de version sans préavis ("GPT-4-turbo" d'aujourd'hui n'est pas celui de demain), rendant toute réplication impossible.

3. **Transparence du comportement.** En local, nous contrôlons réellement `temperature=0`, le format de sortie, et l'absence de post-traitement propriétaire. Les APIs closed-source appliquent des filtres, des re-roll, ou des systèmes de modération non documentés qui contaminent la mesure du biais.

4. **Complémentarité avec la littérature existante.** Bai et al. (2024) et Gallegos et al. (2025) ont déjà documenté le phénomène sur GPT-4 et Claude. Notre contribution n'est pas de répéter ces résultats, mais de tester leur **généralisation à l'écosystème open-source** et à un **contexte linguistique et culturel non anglophone**.

5. **Scalabilité économique.** Tester 8 modèles sur ~1 100 appels chacun coûte quelques euros en cloud open-source contre plusieurs centaines d'euros en API propriétaire. Cela permet des analyses inter-modèles riches (taille, architecture, alignement) impossibles autrement.

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
