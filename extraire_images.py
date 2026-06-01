import os
import email
import base64
import re
import json
from pathlib import Path
from PIL import Image
import io

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Module Vision (Florient Kalumuna)
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
EMAILS_DIR = BASE_DIR / "emails_avec_images"
SORTIE_DIR = BASE_DIR / "images_extraites"
LOG_FILE = BASE_DIR / "extraction_log.json"

SIZE_STANDARD = (128, 128)
MIN_SIZE = (16, 16)
MAX_SIZE = (512, 512)
CONVERT_TO_GRAYSCALE = True
QUALITY = 85

SORTIE_DIR.mkdir(parents=True, exist_ok=True)


def valider_et_optimiser_image(img_pil):
    """Valide et optimise une image PIL (grayscale). Retourne (image, None) ou (None, raison)."""
    try:
        if img_pil is None:
            return None, "Image None"

        w, h = img_pil.size

        if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
            return None, f"Trop petite ({w}x{h} < {MIN_SIZE})"

        if w > MAX_SIZE[0] or h > MAX_SIZE[1]:
            scale = min(MAX_SIZE[0] / w, MAX_SIZE[1] / h)
            new_w, new_h = int(w * scale), int(h * scale)
            img_pil = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)

        if CONVERT_TO_GRAYSCALE:
            img_pil = img_pil.convert("L")

        return img_pil, None

    except Exception as e:
        return None, str(e)


def extraire_et_sauvegarder_image(data, email_id, source_type, index, sortie_dir=None):
    """Extrait une image et la sauvegarde en PNG optimisé."""
    out_dir = sortie_dir or SORTIE_DIR
    try:
        img_pil = Image.open(io.BytesIO(data)).convert("RGB")
        taille_origine = len(data)

        img_optimisee, raison_rejet = valider_et_optimiser_image(img_pil)
        if img_optimisee is None:
            return False, f"Rejet : {raison_rejet}", 0

        nom_fichier = f"{email_id}_{source_type}{index}.png"
        chemin_complet = out_dir / nom_fichier
        out_dir.mkdir(parents=True, exist_ok=True)

        img_optimisee.save(chemin_complet, "PNG", optimize=True, quality=QUALITY)
        economie = taille_origine - chemin_complet.stat().st_size

        return True, nom_fichier, economie

    except Exception as e:
        return False, f"Erreur extraction : {str(e)}", 0


def main():
    compteur_images = 0
    compteur_emails = 0
    compteur_erreurs = 0
    economie_totale = 0
    log_details = {
        "config": {
            "email_dir": str(EMAILS_DIR),
            "output_dir": str(SORTIE_DIR),
            "size_standard": SIZE_STANDARD,
            "grayscale": CONVERT_TO_GRAYSCALE,
        },
        "resultats": [],
    }

    print("=" * 80)
    print("EXTRACTION D'IMAGES — Module Vision (Florient)")
    print("=" * 80)

    if not EMAILS_DIR.is_dir():
        print(f"Dossier introuvable : {EMAILS_DIR}")
        return

    for nom_fichier in os.listdir(str(EMAILS_DIR)):
        if not nom_fichier.endswith(".eml"):
            continue

        chemin = EMAILS_DIR / nom_fichier

        try:
            with open(chemin, "rb") as f:
                msg = email.message_from_bytes(f.read())
        except Exception as e:
            print(f"Erreur lecture {nom_fichier}: {e}")
            compteur_erreurs += 1
            continue

        email_id = nom_fichier.replace(".eml", "")
        images_trouvees = 0
        erreurs_email = 0
        images_email_log = []

        for i, part in enumerate(msg.walk()):
            if part.get_content_type().startswith("image/"):
                try:
                    data = part.get_payload(decode=True)
                    if data:
                        succes, resultat, economie = extraire_et_sauvegarder_image(
                            data, email_id, "part", i
                        )
                        if succes:
                            images_trouvees += 1
                            compteur_images += 1
                            economie_totale += economie
                            images_email_log.append(
                                {"fichier": resultat, "economie_bytes": economie}
                            )
                        else:
                            erreurs_email += 1
                except Exception as e:
                    erreurs_email += 1
                    print(f"  {nom_fichier} (part): {e}")

            if part.get_content_type() == "text/html":
                try:
                    contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    pattern = r"data:image/(png|jpeg|jpg|gif);base64,([A-Za-z0-9+/=\s]+)"
                    for j, (_ext, b64data) in enumerate(re.findall(pattern, contenu)):
                        try:
                            b64data_clean = b64data.replace("\n", "").replace("\r", "").replace(" ", "")
                            data = base64.b64decode(b64data_clean)
                            succes, resultat, economie = extraire_et_sauvegarder_image(
                                data, email_id, "html", j
                            )
                            if succes:
                                images_trouvees += 1
                                compteur_images += 1
                                economie_totale += economie
                                images_email_log.append(
                                    {"fichier": resultat, "economie_bytes": economie}
                                )
                            else:
                                erreurs_email += 1
                        except Exception:
                            erreurs_email += 1
                except Exception:
                    pass

        if images_trouvees > 0:
            compteur_emails += 1
            print(f"OK {nom_fichier:<30} -> {images_trouvees} image(s)")
            log_details["resultats"].append({
                "email": nom_fichier,
                "images_ok": images_trouvees,
                "erreurs": erreurs_email,
                "images": images_email_log,
            })

    print(f"\nImages extraites : {compteur_images} | Emails : {compteur_emails}")

    log_details["stats"] = {
        "images_total": compteur_images,
        "emails_total": compteur_emails,
        "erreurs_total": compteur_erreurs,
        "economie_bytes": economie_totale,
    }

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_details, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
