"""
Vérification complète du projet (module vision + interconnexion).

Usage :
  python verifier_projet.py           # contrôles + pytest + fusion
  python verifier_projet.py --pipeline  # relance aussi extraction + comparaison logos
"""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def ok(msg):
    print(f"  [OK] {msg}")
    return True


def warn(msg):
    print(f"  [!!] {msg}")
    return False


def fail(msg):
    print(f"  [XX] {msg}")
    return False


def check_python_packages():
    print("\n1. Dépendances Python")
    packages = ["cv2", "PIL", "numpy", "skimage", "pytest"]
    tout_ok = True
    for name in packages:
        mod = "PIL" if name == "PIL" else name
        if importlib.util.find_spec(mod) is None:
            fail(f"Manquant : {name}  →  pip install -r requirements.txt")
            tout_ok = False
        else:
            ok(name)
    return tout_ok


def check_fichiers_projet():
    print("\n2. Fichiers et dossiers")
    tout_ok = True

    scripts = [
        "extraire_images.py",
        "comparer_logos.py",
        "fusion_multimodale.py",
        "app.py",
    ]
    for s in scripts:
        if (BASE_DIR / s).exists():
            ok(s)
        else:
            fail(s)
            tout_ok = False

    logos = [
        f
        for f in BASE_DIR.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg")
        and "email" not in f.name.lower()
    ]
    if logos:
        ok(f"{len(logos)} logos de référence à la racine")
    else:
        warn("Aucun logo PNG/JPEG à la racine du projet")
        tout_ok = False

    for dossier, min_attendu, label in [
        ("emails_avec_images", 1, "emails avec images"),
        ("images_extraites", 1, "images extraites"),
    ]:
        p = BASE_DIR / dossier
        if p.is_dir():
            n = len(list(p.glob("*")))
            if n >= min_attendu:
                ok(f"{dossier}/ ({n} fichiers)")
            else:
                warn(f"{dossier}/ presque vide ({n})")
        else:
            warn(f"{dossier}/ absent — lancer le pipeline")
    return tout_ok


def run_pytest():
    print("\n3. Tests unitaires (pytest)")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        ok(r.stdout.strip() or "tous les tests passent")
        return True
    fail("pytest a échoué")
    print(r.stdout)
    print(r.stderr)
    return False


def run_script(nom):
    r = subprocess.run([sys.executable, nom], cwd=BASE_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{nom} — code {r.returncode}")
        if r.stderr:
            print(r.stderr[-800:])
        return False
    ok(nom)
    return True


def check_resultats_vision():
    print("\n4. Module vision (resultats.json)")
    p = BASE_DIR / "resultats.json"
    if not p.exists():
        return warn("resultats.json absent — lancer : python comparer_logos.py")

    data = json.loads(p.read_text(encoding="utf-8"))
    if not data:
        return fail("resultats.json vide")

    alertes = sum(1 for r in data if r.get("statut") == "ALERTE")
    ok(f"{len(data)} images | {alertes} alertes vision")
    return True


def check_interconnexion():
    print("\n5. Interconnexion modules collègues")
    fichiers = {
        "Vision (Florient)": BASE_DIR / "resultats.json",
        "NLP (Masudi)": BASE_DIR / "resultats_texte.json",
        "URL (Béni)": BASE_DIR / "resultats_urls.json",
    }
    counts = {}
    for label, path in fichiers.items():
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            counts[label] = len(data)
            ok(f"{label} : {len(data)} entrées")
        else:
            counts[label] = 0
            warn(f"{label} : fichier absent ({path.name})")

    if counts.get("NLP (Masudi)", 0) < 10:
        warn(
            "Peu de résultats NLP — Masudi doit lancer son analyse sur tout le corpus "
            "(resultats_texte.json)"
        )
    if counts.get("URL (Béni)", 0) == 0:
        warn("Module URL vide — Béni doit générer resultats_urls.json")

    return True


def run_fusion():
    print("\n6. Fusion multimodale")
    if not run_script("fusion_multimodale.py"):
        return False

    p = BASE_DIR / "resultats_fusion.json"
    if not p.exists():
        return fail("resultats_fusion.json non créé")

    data = json.loads(p.read_text(encoding="utf-8"))
    res = data.get("resultats", [])
    meta = data.get("meta", {})
    ok(f"{len(res)} emails fusionnés | sources : {meta.get('sources', {})}")

    # Exemple email présent dans les 3 modules si possible
    triple = [
        r for r in res
        if all(r["modules_presents"].get(m) for m in ("vision", "nlp", "url"))
    ]
    if triple:
        ex = triple[0]
        ok(
            f"Exemple interconnecte : {ex['email_id']} -> fusion={ex['score_fusion']} "
            f"(V={ex['scores']['vision']} N={ex['scores']['nlp']} U={ex['scores']['url']})"
        )
    else:
        warn(
            "Aucun email avec les 3 modules en même temps — normal si NLP pas encore "
            "lancé sur tout le dataset"
        )
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Relancer extraire_images.py et comparer_logos.py avant les contrôles",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("VÉRIFICATION PROJET — Groupe 8 Phishing multimodal")
    print("=" * 70)

    if args.pipeline:
        print("\n0. Pipeline vision")
        run_script("extraire_images.py")
        run_script("comparer_logos.py")

    etapes = [
        check_python_packages(),
        check_fichiers_projet(),
        run_pytest(),
        check_resultats_vision(),
        check_interconnexion(),
        run_fusion(),
    ]

    print("\n" + "=" * 70)
    if all(etapes):
        print("RÉSULTAT : Tout est opérationnel pour ta partie + fusion.")
        print("Dashboard : streamlit run app.py")
        print("Fusion    : resultats_fusion.json")
    else:
        print("RÉSULTAT : Des points nécessitent attention (voir [!!] et [XX] ci-dessus).")
    print("=" * 70)
    return 0 if all(etapes) else 1


if __name__ == "__main__":
    sys.exit(main())
