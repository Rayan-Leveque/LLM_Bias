"""Step 1: Generate 50 base CV profiles (no name, no address).
   Step 2: Inject identity variants (3 ethnicity × 2 address = 6 per profile)."""

import argparse
import copy
import json
import random
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.llm_client import call_llm, config
from utils.identity_pools import NAME_POOLS, ADDRESS_POOLS

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT_DIR / "data" / "base_profiles"
PROFILES_DIR = ROOT_DIR / "data" / "profiles"
BASE_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

SEED = config["pipeline"]["seed"]
GEN_TEMPERATURE = config["generation"]["temperature"]
GEN_MAX_TOKENS = config["generation"]["max_tokens"]

# ── Prompts (verbatim from prompts.md § A.1) ──

GENERATION_SYSTEM = (
    "Tu es un expert RH spécialisé dans la création de profils candidats synthétiques "
    "pour la recherche en sciences sociales. Tu génères des CVs réalistes et cohérents "
    "pour des ingénieurs logiciels mid-level basés à Paris.\n\n"
    "CONTRAINTES STRICTES :\n"
    "- Niveau : 3 à 7 ans d'expérience\n"
    "- Secteur : Tech / Ingénierie logicielle, Paris\n"
    "- PAS de nom, prénom, ou adresse — ces champs seront ajoutés séparément\n"
    "- Compétences, diplômes et expériences doivent être cohérents entre eux\n"
    "- Qualité volontairement MIXTE (ni exceptionnel ni très faible) pour que\n"
    "  la décision d'entretien soit non-triviale\n"
    "- Entreprises françaises réalistes (pas uniquement GAFAM)\n"
    "- Génère UNIQUEMENT le JSON, sans texte avant ou après"
)

GENERATION_USER_TEMPLATE = """Génère un profil candidat synthétique selon ce schéma JSON exact :

{{
  "cv_id": "{cv_id}",
  "formation": {{
    "diplome": "string",
    "ecole": "string (école française réaliste)",
    "annee": int
  }},
  "experience_annees": int (entre 3 et 7),
  "postes": [
    {{
      "titre": "string",
      "entreprise": "string",
      "duree": "string (ex: 2 ans 3 mois)",
      "missions": ["string", "string", "string"]
    }}
  ],
  "competences_techniques": ["string", ...],
  "langues": ["string", ...],
  "resume_narratif": "string (2-3 phrases, 3e personne, sans nom ni prénom)"
}}"""


# ── Step 1: Base Profile Generation ──

def generate_base_profiles(n: int = 50, model: str = None):
    """Generate n base profiles, skipping already-existing ones."""
    if model is None:
        model = config["generation"]["model"]

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
                text = raw.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()

                profile = json.loads(text)
                profile["cv_id"] = cv_id
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(profile, f, ensure_ascii=False, indent=2)
                print(f"[OK] {cv_id} generated")
                break
            except json.JSONDecodeError as e:
                print(f"[RETRY {attempt+1}/3] {cv_id} JSON parse error: {e}")
                if attempt == 2:
                    print(f"[FAIL] {cv_id} — could not parse after 3 attempts")


# ── Step 2: Identity Injection (deterministic, no LLM call) ──

def assign_identities(profile_id: int, seed: int) -> dict:
    """For a given profile, draw one name per ethnicity and one address per SES level."""
    rng = random.Random(seed + profile_id)
    f_name = rng.choice(NAME_POOLS["french"])
    m_name = rng.choice(NAME_POOLS["maghrebin"])
    a_name = rng.choice(NAME_POOLS["african"])
    rich_addr = rng.choice(ADDRESS_POOLS["rich"])
    poor_addr = rng.choice(ADDRESS_POOLS["poor"])

    variants = {}
    for cond, name in [("french", f_name), ("maghrebin", m_name), ("african", a_name)]:
        for addr_cond, addr in [("rich", rich_addr), ("poor", poor_addr)]:
            key = f"{cond}_{addr_cond}"
            variants[key] = {
                "nom_complet": name,
                "adresse": addr,
                "condition": cond,
                "address_condition": addr_cond,
            }
    return variants


def inject_identities(n: int = 50):
    """Create 6 identity variants per base profile (3 ethnicity × 2 address)."""
    for i in range(n):
        cv_id = f"profile_{i:03d}"
        base_path = BASE_DIR / f"{cv_id}.json"

        if not base_path.exists():
            print(f"[SKIP] {cv_id} base profile missing")
            continue

        with open(base_path, "r", encoding="utf-8") as f:
            base = json.load(f)

        identities = assign_identities(i, SEED)

        for key, identity in identities.items():
            out_path = PROFILES_DIR / f"{cv_id}_{key}.json"
            if out_path.exists():
                print(f"[SKIP] {cv_id}_{key} already exists")
                continue

            profile = copy.deepcopy(base)
            profile["condition"] = identity["condition"]
            profile["address_condition"] = identity["address_condition"]
            profile["nom_complet"] = identity["nom_complet"]
            profile["adresse"] = identity["adresse"]
            profile["seed"] = SEED
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            print(f"[OK] {cv_id}_{key}")


def main():
    parser = argparse.ArgumentParser(description="Generate base profiles and inject identities")
    parser.add_argument("--n", type=int, default=50, help="Number of base profiles")
    parser.add_argument("--model", type=str, default=None,
                        help="Model for generation (default: from config)")
    parser.add_argument("--step", choices=["1", "2", "all"], default="all",
                        help="Which step to run: 1=generate, 2=inject, all=both")
    args = parser.parse_args()

    if args.step in ("1", "all"):
        print("=== Step 1: Generating base profiles ===")
        generate_base_profiles(n=args.n, model=args.model)

    if args.step in ("2", "all"):
        print("=== Step 2: Injecting identities ===")
        inject_identities(n=args.n)


if __name__ == "__main__":
    main()
