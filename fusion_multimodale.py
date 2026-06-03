"""
Fusion des scores Vision (Florient) + NLP (Masudi) + URL (Béni).

Entrées attendues à la racine du projet :
  - resultats.json         (module vision — une ligne par image)
  - resultats_texte.json   (module NLP — une ligne par email)
  - resultats_urls.json    (module URL — une ligne par email)

Sortie :
  - resultats_fusion.json  (une ligne par email, score unifié)
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

FICHIER_VISION = BASE_DIR / "resultats.json"
FICHIER_NLP = BASE_DIR / "resultats_texte.json"
FICHIER_URL = BASE_DIR / "resultats_urls.json"
FICHIER_FUSION = BASE_DIR / "resultats_fusion.json"

# Poids par défaut (modifiable)
POIDS_VISION = 0.35
POIDS_NLP = 0.35
POIDS_URL = 0.30
SEUIL_PHISHING = 0.60

EMAIL_ID_RE = re.compile(r"^(email_\d{4})")


def normaliser_email_id(nom: str) -> str:
    """email_0041.eml, email_0041_part3.png → email_0041"""
    if not nom:
        return ""
    base = nom.replace(".eml", "").replace(".EML", "")
    m = EMAIL_ID_RE.match(base)
    if m:
        return m.group(1)
    if base.startswith("email_") and len(base) >= 10:
        return base[:10]
    return base


def charger_json(chemin: Path):
    if not chemin.exists():
        return []
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def agreger_vision(lignes_vision: list) -> dict:
    """Regroupe par email : score vision = max(score_final) des images."""
    par_email = {}
    for row in lignes_vision:
        eid = normaliser_email_id(row.get("image", ""))
        if not eid:
            continue
        score = float(row.get("score_final", 0))
        statut = row.get("statut", "SAIN")
        entree = par_email.get(eid)
        if entree is None or score > entree["score_vision"]:
            par_email[eid] = {
                "score_vision": score,
                "statut_vision": statut,
                "visual_score": row.get("visual_score"),
                "ressemble_a": row.get("ressemble_a"),
                "nb_images": 1,
                "images_alertes": [row["image"]] if statut == "ALERTE" else [],
            }
        else:
            entree["nb_images"] += 1
            if statut == "ALERTE":
                entree["images_alertes"].append(row["image"])
            if score > entree["score_vision"]:
                entree["score_vision"] = score
                entree["statut_vision"] = statut
                entree["ressemble_a"] = row.get("ressemble_a")
    return par_email


def index_nlp(lignes_nlp: list) -> dict:
    out = {}
    for row in lignes_nlp:
        cle = row.get("fichier") or row.get("email") or ""
        eid = normaliser_email_id(cle)
        if eid:
            out[eid] = {
                "score_nlp": float(row.get("score_nlp", 0)),
                "statut_nlp": row.get("statut_nlp", "SAIN"),
                "menaces_detectees": row.get("menaces_detectees", []),
            }
    return out


def index_url(lignes_url: list) -> dict:
    out = {}
    for row in lignes_url:
        eid = normaliser_email_id(row.get("email", ""))
        if eid:
            out[eid] = {
                "score_url": float(row.get("url_score", 0)),
                "urls_analysees": row.get("urls_analysees", 0),
                "alertes_url": row.get("alertes", []),
            }
    return out


def calculer_score_fusion(score_vision, score_nlp, score_url):
    """Moyenne pondérée sur les modules disponibles."""
    parties = []
    if score_vision is not None:
        parties.append((score_vision, POIDS_VISION))
    if score_nlp is not None:
        parties.append((score_nlp, POIDS_NLP))
    if score_url is not None:
        parties.append((score_url, POIDS_URL))
    if not parties:
        return 0.0
    total_poids = sum(p for _, p in parties)
    return round(sum(s * p for s, p in parties) / total_poids, 3)


def statut_fusion(score: float, modules: dict) -> str:
    if score >= SEUIL_PHISHING:
        return "PHISHING"
    if modules.get("statut_vision") == "ALERTE" or modules.get("statut_nlp") == "ALERTE":
        return "PHISHING"
    if any(
        modules.get(k) in ("ALERTE", "SUSPECT")
        for k in ("statut_vision", "statut_nlp")
    ):
        return "SUSPECT"
    return "SAIN"


def fusionner():
    vision_raw = charger_json(FICHIER_VISION)
    nlp_raw = charger_json(FICHIER_NLP)
    url_raw = charger_json(FICHIER_URL)

    vision_par_email = agreger_vision(vision_raw)
    nlp_par_email = index_nlp(nlp_raw)
    url_par_email = index_url(url_raw)

    tous_ids = sorted(set(vision_par_email) | set(nlp_par_email) | set(url_par_email))

    resultats = []
    for eid in tous_ids:
        v = vision_par_email.get(eid)
        n = nlp_par_email.get(eid)
        u = url_par_email.get(eid)

        sv = v["score_vision"] if v else None
        sn = n["score_nlp"] if n else None
        su = u["score_url"] if u else None

        score = calculer_score_fusion(sv, sn, su)
        modules_info = {
            "statut_vision": v["statut_vision"] if v else None,
            "statut_nlp": n["statut_nlp"] if n else None,
        }
        ligne = {
            "email_id": eid,
            "fichier": f"{eid}.eml",
            "score_fusion": score,
            "statut_fusion": statut_fusion(score, modules_info),
            "scores": {
                "vision": sv,
                "nlp": sn,
                "url": su,
            },
            "modules_presents": {
                "vision": v is not None,
                "nlp": n is not None,
                "url": u is not None,
            },
        }
        if v:
            ligne["detail_vision"] = {
                "nb_images": v["nb_images"],
                "ressemble_a": v.get("ressemble_a"),
                "images_alertes": v.get("images_alertes", []),
            }
        if n:
            ligne["detail_nlp"] = {
                "menaces": n.get("menaces_detectees", []),
            }
        if u:
            ligne["detail_url"] = {
                "urls_analysees": u.get("urls_analysees", 0),
                "alertes": u.get("alertes_url", []),
            }
        resultats.append(ligne)

    meta = {
        "poids": {"vision": POIDS_VISION, "nlp": POIDS_NLP, "url": POIDS_URL},
        "seuil_phishing": SEUIL_PHISHING,
        "nb_emails": len(resultats),
        "sources": {
            "vision_lignes": len(vision_raw),
            "nlp_emails": len(nlp_par_email),
            "url_emails": len(url_par_email),
        },
    }

    sortie = {"meta": meta, "resultats": resultats}
    with open(FICHIER_FUSION, "w", encoding="utf-8") as f:
        json.dump(sortie, f, indent=2, ensure_ascii=False)

    return sortie


def main():
    print("=" * 70)
    print("FUSION MULTIMODALE — Vision + NLP + URL")
    print("=" * 70)

    for label, path in [
        ("Vision", FICHIER_VISION),
        ("NLP", FICHIER_NLP),
        ("URL", FICHIER_URL),
    ]:
        flag = "OK" if path.exists() else "MANQUANT"
        print(f"  [{flag}] {path.name}")

    data = fusionner()
    meta = data["meta"]
    phishing = sum(1 for r in data["resultats"] if r["statut_fusion"] == "PHISHING")
    suspect = sum(1 for r in data["resultats"] if r["statut_fusion"] == "SUSPECT")

    print(f"\nEmails fusionnés : {meta['nb_emails']}")
    print(f"  PHISHING : {phishing}")
    print(f"  SUSPECT  : {suspect}")
    print(f"  SAIN     : {meta['nb_emails'] - phishing - suspect}")
    print(f"\nSortie : {FICHIER_FUSION}")
    print("=" * 70)


if __name__ == "__main__":
    main()
