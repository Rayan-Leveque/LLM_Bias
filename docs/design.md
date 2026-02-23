# Design du pipeline — Point d'ancrage

## Hypothèse centrale

Lorsqu'un LLM évalue des candidats **séparément** (condition single), il tend à favoriser les minorités — probablement par sur-correction RLHF (social desirability). Lorsqu'il est placé en situation de **comparaison directe**, il tend à favoriser la majorité — les stéréotypes implicites s'activent.

Cette dissociation s'appuie sur deux corpus de littérature distincts :

- **Tests en condition single** — [Biases in the Blind Spot (Gallegos et al., 2025, arXiv:2602.10117)](https://arxiv.org/abs/2602.10117) montre qu'en évaluation isolée, les LLMs produisent des biais non verbalisés (religion, origine, langue) tout en maintenant une apparence de neutralité dans leur raisonnement. En condition single, la pression sociale (RLHF) pousse les modèles à corriger explicitement en faveur des groupes minoritaires, ce qui masque — sans éliminer — les stéréotypes sous-jacents.

- **Tests en condition comparative (IAT)** — [Bai et al. (2024, arXiv:2402.04105)](https://arxiv.org/abs/2402.04105) adaptent l'Implicit Association Test (IAT) aux LLMs et introduisent une mesure de *Decision Bias* fondée sur l'évaluation relative de deux candidats. Leur résultat clé : les modèles alignés sur des valeurs égalitaires (GPT-4, Claude, LLaMA2) passent les tests explicites mais révèlent des biais stéréotypés pervasifs en comparaison directe — par exemple, GPT-4 oriente les candidats à noms africains/hispaniques vers des postes de clerc et les candidats à noms caucasiens vers des postes d'encadrement. L'évaluation relative est significativement plus diagnostique que l'évaluation absolue.

Ce phénomène est à rapprocher de la littérature psychologique sur l'évaluation séparée vs. conjointe (Hsee, 1996) et des audit studies (Bertrand & Mullainathan, 2004).

**L'hypothèse est empirique et non confirmée — c'est précisément ce que ce pipeline cherche à tester.**

---

## Domaine

**Embauche / évaluation de CV** — contexte français.

Littérature de référence : études de testing ISM Corum, données DARES, [Bai et al. (2024)](https://arxiv.org/abs/2402.04105) pour l'adaptation de l'IAT aux LLMs, et [Gallegos et al. (2025)](https://arxiv.org/abs/2602.10117) pour la détection automatique de biais non verbalisés en condition single.

---

## Structure expérimentale

### Condition A — Single

- Présenter **un seul CV** au modèle
- Demander une décision binaire : **Accepter / Rejeter**
- Répéter pour N itérations par groupe (ex: N=100)
- Calculer le taux d'acceptation par groupe

### Condition B — Comparatif

- Présenter **deux CV côte à côte** (candidat A vs candidat B)
- Les CV sont identiques sauf les marqueurs d'identité
- Demander un **choix forcé** : "Lequel retenezvous ?"
- Randomiser l'ordre de présentation (A/B vs B/A)
- Calculer P(majorité choisie)

---

## Stimuli

- **Plusieurs templates de CV** (pour éviter que les résultats soient liés à un seul profil)
- **Marqueurs d'identité** : prénom + adresse (photo en option pour les VLMs)
- Paires de prénoms à définir : ex. "Kévin Martin" ↔ "Moussa Diallo"

### Points ouverts sur les stimuli
- Nombre de templates (à décider)
- Liste définitive des paires de prénoms
- Adresses : arrondissements/communes à utiliser
- Condition de contrôle possible (prénom neutre / ambigu) — non décidée

---

## Analyse statistique

**Tests d'indépendance** (chi-carré ou Fisher exact) :

- Condition single : tester si le taux d'acceptation est indépendant du groupe ethnique
- Condition comparative : tester si le choix est indépendant de l'identité du candidat A/B
- Comparer les deux conditions pour mesurer le "shifting bias"

---

## Modèles

Plusieurs modèles à tester (liste non encore définie). L'objectif à terme est de comparer si le phénomène est universel ou propre à certaines architectures/entraînements.

---

## Ce qui reste à décider

| Question | Statut |
|---|---|
| Paires de prénoms définitives | Ouvert |
| Nombre de templates de CV | Ouvert |
| Adresses à utiliser | Ouvert |
| Condition de contrôle (prénom neutre) | Non décidée |
| Modèles à tester en premier | Ouvert |
| Formulation exacte des prompts | Ouvert |
