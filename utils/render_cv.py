"""CV text rendering for evaluation prompts (verbatim from prompts.md § A.5)."""


def render_cv_fr(profile: dict) -> str:
    lines = []
    lines.append(f"Candidat : {profile['nom_complet']}")
    lines.append(f"Adresse : {profile['adresse']}")
    lines.append(f"Formation : {profile['formation']['diplome']}, "
                 f"{profile['formation']['ecole']} ({profile['formation']['annee']})")
    lines.append(f"Expérience : {profile['experience_annees']} ans\n")
    lines.append("Expériences professionnelles :")
    for p in profile["postes"]:
        lines.append(f"  {p['titre']} — {p['entreprise']} ({p['duree']})")
        for m in p["missions"]:
            lines.append(f"    - {m}")
    lines.append("")
    lines.append(f"Compétences techniques : {', '.join(profile['competences_techniques'])}")
    lines.append(f"Langues : {', '.join(profile['langues'])}")
    lines.append("")
    lines.append(profile["resume_narratif"])
    return "\n".join(lines)
