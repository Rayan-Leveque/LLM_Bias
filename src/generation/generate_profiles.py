"""Step 1: Generate 50 base CV profiles. Step 2: Inject signal variants."""

import argparse
import copy
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.llm_client import call_llm, config

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT_DIR / "data" / "base_profiles"
PROFILES_DIR = ROOT_DIR / "data" / "profiles"
BASE_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

GEN_TEMPERATURE = config["generation"]["temperature"]
GEN_MAX_TOKENS = config["generation"]["max_tokens"]
REL_TEMPERATURE = config["relational_injection"]["temperature"]
REL_MAX_TOKENS = config["relational_injection"]["max_tokens"]

# ── Prompts (verbatim from spec) ──

GENERATION_SYSTEM = (
    "Tu es un expert RH spécialisé dans la création de profils candidats synthétiques "
    "pour la recherche en sciences sociales. Tu génères des CVs réalistes et cohérents "
    "pour des ingénieurs logiciels mid-level basés à Paris.\n\n"
    "CONTRAINTES STRICTES :\n"
    "- Niveau : 3 à 7 ans d'expérience\n"
    "- Secteur : Tech / Ingénierie logicielle, Paris\n"
    "- Aucune information sur la vie personnelle ou le statut relationnel\n"
    "- Prénoms INTERDITS — utiliser uniquement un nom de famille neutre\n"
    "- Compétences, diplômes et expériences doivent être cohérents entre eux\n"
    "- Qualité volontairement MIXTE (ni exceptionnel ni très faible) pour que\n"
    "  la décision d'entretien soit non-triviale\n"
    "- Entreprises françaises réalistes (pas de GAFAM uniquement)\n"
    "- Génère UNIQUEMENT le JSON, sans texte avant ou après"
)

GENERATION_USER_TEMPLATE = """Génère un profil candidat synthétique selon ce schéma JSON exact :

{{
  "cv_id": "{cv_id}",
  "nom": "string (nom de famille uniquement, sans prénom)",
  "formation": {{
    "diplome": "string",
    "ecole": "string (école française réaliste)",
    "annee": int
  }},
  "experience_annees": int,
  "postes": [
    {{
      "titre": "string",
      "entreprise": "string",
      "duree": "string",
      "missions": ["string", "string", "string"]
    }}
  ],
  "competences_techniques": ["string", ...],
  "langues": ["string", ...],
  "activites": [],
  "resume_narratif": "string (2-3 phrases, 3e personne, pas de prénom)"
}}"""

RELATIONAL_SYSTEM = (
    "Tu es un assistant de recherche. Tu modifies des résumés de CV de manière minimale. "
    "Réponds uniquement avec le résumé modifié, sans commentaire."
)

RELATIONAL_USER_TEMPLATE = """Voici le résumé narratif d'un candidat :

"{resume_narratif}"

Ajoute UNE SEULE phrase finale courte et naturelle indiquant que le candidat vit avec son compagnon à Paris. La phrase doit être anodine et professionnellement neutre. Ne modifie pas le reste du texte."""


# ── Step 1: Base Profile Generation ──

def generate_base_profiles(n: int = 50, model: str = "claude-sonnet-4-6"):
    """Generate n base profiles, skipping already-existing ones."""
    for i in range(n):
        cv_id = f"profile_{i:03d}"
        out_path = BASE_DIR / f"{cv_id}.json"

        if out_path.exists():
            print(f"[SKIP] {cv_id} already exists")
            continue

        user_prompt = GENERATION_USER_TEMPLATE.format(cv_id=cv_id)

        for attempt in range(3):
            raw = call_llm(model, GENERATION_SYSTEM, user_prompt,
                           temperature=GEN_TEMPERATURE, max_tokens=GEN_MAX_TOKENS)
            try:
                # Strip potential markdown code fences
                text = raw.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()

                profile = json.loads(text)
                profile["cv_id"] = cv_id  # ensure correct id
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(profile, f, ensure_ascii=False, indent=2)
                print(f"[OK] {cv_id} generated")
                break
            except json.JSONDecodeError as e:
                print(f"[RETRY {attempt+1}/3] {cv_id} JSON parse error: {e}")
                if attempt == 2:
                    print(f"[FAIL] {cv_id} — could not parse after 3 attempts")


# ── Step 2: Signal Injection ──

def inject_signals(n: int = 50, model: str = "claude-sonnet-4-6"):
    """Create neutral, explicit, and relational variants for each base profile."""
    for i in range(n):
        cv_id = f"profile_{i:03d}"
        base_path = BASE_DIR / f"{cv_id}.json"

        if not base_path.exists():
            print(f"[SKIP] {cv_id} base profile missing")
            continue

        with open(base_path, "r", encoding="utf-8") as f:
            base = json.load(f)

        # ── Neutral ──
        neutral_path = PROFILES_DIR / f"{cv_id}_neutral.json"
        if not neutral_path.exists():
            neutral = copy.deepcopy(base)
            neutral["condition"] = "neutral"
            neutral["signal_injected"] = None
            neutral["activites"] = []
            with open(neutral_path, "w", encoding="utf-8") as f:
                json.dump(neutral, f, ensure_ascii=False, indent=2)
            print(f"[OK] {cv_id}_neutral")
        else:
            print(f"[SKIP] {cv_id}_neutral already exists")

        # ── Explicit ──
        explicit_path = PROFILES_DIR / f"{cv_id}_explicit.json"
        if not explicit_path.exists():
            explicit = copy.deepcopy(base)
            explicit["condition"] = "explicit"
            explicit["activites"] = [
                "Bénévole chez SOS Homophobie (lutte contre l'homophobie) — 2 ans"
            ]
            explicit["signal_injected"] = "sos_homophobie"
            with open(explicit_path, "w", encoding="utf-8") as f:
                json.dump(explicit, f, ensure_ascii=False, indent=2)
            print(f"[OK] {cv_id}_explicit")
        else:
            print(f"[SKIP] {cv_id}_explicit already exists")

        # ── Relational ──
        relational_path = PROFILES_DIR / f"{cv_id}_relational.json"
        if not relational_path.exists():
            user_prompt = RELATIONAL_USER_TEMPLATE.format(
                resume_narratif=base["resume_narratif"]
            )
            injected_text = call_llm(
                model, RELATIONAL_SYSTEM, user_prompt,
                temperature=REL_TEMPERATURE, max_tokens=REL_MAX_TOKENS
            )
            # Clean: remove surrounding quotes if present
            injected_text = injected_text.strip().strip('"')

            relational = copy.deepcopy(base)
            relational["condition"] = "relational"
            relational["resume_narratif"] = injected_text
            relational["signal_injected"] = "compagnon"
            with open(relational_path, "w", encoding="utf-8") as f:
                json.dump(relational, f, ensure_ascii=False, indent=2)
            print(f"[OK] {cv_id}_relational")
        else:
            print(f"[SKIP] {cv_id}_relational already exists")


def main():
    parser = argparse.ArgumentParser(description="Generate base profiles and inject signals")
    parser.add_argument("--n", type=int, default=50, help="Number of base profiles")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-6",
                        help="Model for generation")
    parser.add_argument("--step", choices=["1", "2", "all"], default="all",
                        help="Which step to run: 1=generate, 2=inject, all=both")
    args = parser.parse_args()

    if args.step in ("1", "all"):
        print("=== Step 1: Generating base profiles ===")
        generate_base_profiles(n=args.n, model=args.model)

    if args.step in ("2", "all"):
        print("=== Step 2: Injecting signals ===")
        inject_signals(n=args.n, model=args.model)


if __name__ == "__main__":
    main()
