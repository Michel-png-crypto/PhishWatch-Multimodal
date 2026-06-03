"""Orchestrateur principal du projet PhishWatch-Multimodal.
Le point d'entrée lit phishing-2025.mbox et appelle les modules locaux
pour le parsing, la vérification d'URL, la fusion multimodale et la génération de rapport.
"""

import json
import mailbox
import shutil
from pathlib import Path
from typing import List, Dict

from extraire_donnees import extraire_metadata_email
from check_virustotal import verifier_avec_virustotal
from fusion_multimodale import fusionner
from generer_rapport import generer_rapport

# 🚨 IMPORTATION DES MODULES DE VISION
import extraire_images
import orchestrer_vision

BASE_DIR = Path(__file__).resolve().parent
MBOX_FILE = BASE_DIR / "phishing-2025.mbox"
OUT_METADATA_JSON = BASE_DIR / "metadata_emails.json"
OUT_URLS_JSON = BASE_DIR / "resultats_urls.json"
TMP_EML_DIR = BASE_DIR / "tmp_mbox_eml"
IMAGES_EXTRAITES_DIR = BASE_DIR / "images_extraites"


def extract_emails_from_mbox(mbox_path: Path, output_dir: Path) -> List[Path]:
    """Extrait chaque message du MBOX en un fichier EML temporaire."""
    output_dir.mkdir(parents=True, exist_ok=True)
    mbox = mailbox.mbox(str(mbox_path))
    eml_paths = []

    for index, message in enumerate(mbox, start=1):
        filename = output_dir / f"email_{index:04}.eml"
        with open(filename, "wb") as eml_file:
            if hasattr(message, "as_bytes"):
                eml_file.write(message.as_bytes())
            else:
                eml_file.write(bytes(message))
        eml_paths.append(filename)

    return eml_paths


def extract_metadata_from_mbox(mbox_path: Path) -> List[Dict]:
    """Parse chaque message du MBOX et extrait les métadonnées via extraire_donnees."""
    eml_files = extract_emails_from_mbox(mbox_path, TMP_EML_DIR)
    metadata = []

    for eml_file in eml_files:
        info = extraire_metadata_email(str(eml_file))
        metadata.append(info)

    with open(OUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata


def analyze_urls(metadata_list: List[Dict]) -> List[Dict]:
    """Vérifie les URLs extraites avec VirusTotal et écrit le résultat JSON attendu."""
    url_results = []

    for email_metadata in metadata_list:
        email_name = email_metadata.get("fichier", "unknown")
        urls = email_metadata.get("urls_trouvees", [])

        for url in urls:
            verdict = verifier_avec_virustotal(url)
            if isinstance(verdict, dict):
                url_results.append({
                    "email": email_name,
                    "url": url,
                    "url_score": verdict.get("malicieux", 0) / max(1, verdict.get("total_moteurs", 1)),
                    "decision": verdict.get("decision"),
                    "alertes": [
                        f"{verdict.get('malicieux', 0)} moteurs malicieux"
                        if verdict.get("malicieux", 0) > 0 else []
                    ],
                })
            else:
                url_results.append({
                    "email": email_name,
                    "url": url,
                    "error": str(verdict),
                })

    with open(OUT_URLS_JSON, "w", encoding="utf-8") as f:
        json.dump(url_results, f, indent=2, ensure_ascii=False)

    return url_results


def main():
    if not MBOX_FILE.exists():
        raise FileNotFoundError(f"Le fichier de point d'entrée est introuvable : {MBOX_FILE}")

    print("🔎 Lecture de l'archive MBOX :", MBOX_FILE)
    metadata = extract_metadata_from_mbox(MBOX_FILE)
    print(f"✅ Métadonnées extraites pour {len(metadata)} emails")

    print("🌐 Vérification des URLs avec VirusTotal...")
    urls = sum(len(item.get("urls_trouvees", [])) for item in metadata)
    url_results = analyze_urls(metadata)
    print(f"✅ Résultats VirusTotal pour {urls} URL(s) enregistrés dans : {OUT_URLS_JSON}")

    # � Purge du dossier des images extraites avant chaque exécution
    shutil.rmtree(IMAGES_EXTRAITES_DIR, ignore_errors=True)
    IMAGES_EXTRAITES_DIR.mkdir(parents=True, exist_ok=True)

    # �📸 EXTRACTION DES IMAGES
    print("📸 Extraction et optimisation des images par l'IA de Vision...")
    extraire_images.EMAILS_DIR = TMP_EML_DIR
    extraire_images.main()
    print("✅ Extraction des images terminée.")

    # 🚨 NOTATION ET COMPARAISON DES LOGOS (L'ÉTAPE INDISPENSABLE)
    print("🧠 Calcul des scores de similarité des logos via pHash & SSIM...")
    orchestrer_vision.executer_analyse_vision()
    print("✅ Génération du fichier resultats.json pour la fusion terminée.")

    # 🧠 FUSION MULTIMODALE
    print("🧠 Fusion multimodale des scores...")
    fusion_data = fusionner()
    fusion_file = Path(__file__).resolve().parent / "resultats_fusion.json"
    print(f"✅ Fusion terminée, fichier de sortie : {fusion_file}")

    # 📄 RAPPORT HTML
    print("📄 Génération du rapport HTML...")
    rapport_file = generer_rapport()
    print(f"✅ Rapport généré : {rapport_file}")

    print("\n--- Résumé ---")
    print(f"Emails traités    : {len(metadata)}")
    print(f"URLs testées      : {urls}")
    print(f"URL résultats      : {OUT_URLS_JSON}")
    print(f"Fusion multimodale: {fusion_file}")
    print(f"Rapport HTML      : {rapport_file}")


if __name__ == "__main__":
    main()